from unittest import mock
from unittest.mock import patch
import datetime
from collections import namedtuple
from playhouse.shortcuts import model_to_dict
from peewee import (
    Model,
    IntegerField,
    CharField,
    AutoField,
    SqliteDatabase,
    BooleanField,
    DateTimeField,
    fn,
    OperationalError,
)

db = SqliteDatabase("automatic.db")


class Vehicle(Model):
    pk = AutoField()
    vin = CharField()
    type_make = CharField()
    type_year = IntegerField()
    type_ref = IntegerField()

    class Meta:
        database = db


class VehicleType(Model):
    pk = AutoField()
    type_name = CharField()
    fuel_type = CharField()

    class Meta:
        database = db


class GearChangeConfig(Model):
    pk = AutoField()
    vehicle_type_ref = IntegerField()
    speed = IntegerField()
    gear_from = IntegerField()
    gear_to = IntegerField()

    class Meta:
        database = db


class TransmissionLog(Model):
    pk = AutoField()
    vehicle_ref = IntegerField()
    gear_speed = IntegerField()
    gear_from = IntegerField()
    gear_to = IntegerField()
    error = BooleanField()
    error_message = CharField()
    date_timestamp = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


def create_tables() -> None:
    db.create_tables([Vehicle, VehicleType, GearChangeConfig, TransmissionLog])


def preload_config() -> None:
    with db.atomic():
        if VehicleType.select().count() == 0:
            VehicleType.create(type_name="Truck", fuel_type="Gasoline")
            VehicleType.create(type_name="Car", fuel_type="Gasoline")
            VehicleType.create(type_name="SUV", fuel_type="Gasoline")
            VehicleType.create(type_name="Van", fuel_type="Diesel")
        if GearChangeConfig.select().count() == 0:
            for i in range(1, 4):
                GearChangeConfig.create(
                    vehicle_type_ref=i, speed=15, gear_from=1, gear_to=2
                )
                GearChangeConfig.create(
                    vehicle_type_ref=i, speed=25, gear_from=2, gear_to=3
                )
                GearChangeConfig.create(
                    vehicle_type_ref=i, speed=40, gear_from=3, gear_to=4
                )
                GearChangeConfig.create(
                    vehicle_type_ref=i, speed=45, gear_from=4, gear_to=5
                )
                GearChangeConfig.create(
                    vehicle_type_ref=i, speed=50, gear_from=5, gear_to=6
                )
            GearChangeConfig.create(
                vehicle_type_ref=4, speed=12, gear_from=1, gear_to=2
            )
            GearChangeConfig.create(
                vehicle_type_ref=4, speed=19, gear_from=2, gear_to=3
            )
            GearChangeConfig.create(
                vehicle_type_ref=4, speed=26, gear_from=3, gear_to=4
            )
            GearChangeConfig.create(
                vehicle_type_ref=4, speed=34, gear_from=4, gear_to=5
            )
            GearChangeConfig.create(
                vehicle_type_ref=4, speed=46, gear_from=5, gear_to=6
            )


def configs_loaded() -> bool:
    try:
        if GearChangeConfig.select().count() > 0:
            return True
    except OperationalError:
        return False
    return False


def tables_exists() -> bool:
    tables = db.get_tables()
    if len(tables) > 0:
        return True
    return False


def check_existance() -> SqliteDatabase:
    if not tables_exists():
        create_tables()
        if not configs_loaded():
            preload_config()
        return db
    return db


def get_vehicle_type(vtype: str) -> list[str]:
    vtype_name = vtype.capitalize()
    VehicleTypeObj = namedtuple("VehicleTypeObj", ["pk", "type_name", "fuel_type"])
    typex = VehicleType.select().where(VehicleType.type_name == vtype_name)
    if not typex.exists():
        return False
    for types in typex:
        VehicleTypeData = VehicleTypeObj(**model_to_dict(types))
    return VehicleTypeData


def get_vehicle(vin: str) -> object:
    try:
        vehicle = Vehicle.select().where(Vehicle.vin == vin).get()
        VehicleObj = namedtuple(
            "VehicleObj", ["pk", "vin", "type_make", "type_year", "type_ref"]
        )
        VehicleData = VehicleObj(**model_to_dict(vehicle))
        return VehicleData
    except Vehicle.DoesNotExist:
        raise ValueError("Vehicle does not exist")


def get_gear_config_by_vtid_gearto(vtid: int, gear_to: int) -> object:
    gearChangeData = None
    gearChangeObj = namedtuple(
        "gearChangeObj", ["pk", "vehicle_type_ref", "speed", "gear_from", "gear_to"]
    )
    configs = GearChangeConfig.select().where(
        GearChangeConfig.vehicle_type_ref == vtid, GearChangeConfig.gear_to == gear_to
    )
    for config in configs:
        gearChangeData = gearChangeObj(**model_to_dict(config))
    return gearChangeData


def get_vehicle_type_ref(vtype_id: str) -> object:
    VehicleTypeObj = namedtuple("VehicleTypeObj", ["pk", "type_name", "fuel_type"])
    try:
        vehicle_type = VehicleType.select().where(VehicleType.pk == vtype_id).get()
        VehicleTypeData = VehicleTypeObj(**model_to_dict(vehicle_type))
        return VehicleTypeData
    except VehicleType.DoesNotExist:
        raise ValueError("Vehicle type does not exist")


def is_error(gear_speed: int, actual_speed: int, gear_from: int, gear_to: int) -> bool:
    message = "No Error Detected"
    error = {"error": False, "message": message}
    if type(gear_speed) != int or type(actual_speed) != int:
        raise ValueError("Gear speed and actual speed must be integers")
    if gear_speed < actual_speed:
        error["message"] = (
            f"Gear shift exceeded at {actual_speed}, expected {gear_speed}, shifting from {gear_from} to {gear_to}"
        )
        error["error"] = True
    # This use-case has not been defined
    # if gear_speed > actual_speed:
    #     message = f"Gear shift speed not met at {actual_speed}, expected {gear_speed}, shifting from {gear_from} to {gear_to}"
    #     return True
    return error


def shift_log_add(
    vin: str,
    gear_speed: int,
    gear_from: int,
    gear_to: int,
) -> None:
    vehicle = get_vehicle(vin)
    vtObj = VehicleType.get(VehicleType.pk == vehicle.type_ref)
    vehicle_type = get_vehicle_type(vtObj.type_name)
    config = get_gear_config_by_vtid_gearto(vehicle_type.pk, gear_to)
    error = is_error(config.speed, gear_speed, gear_from, gear_to)
    with db.atomic():
        TransmissionLog.create(
            vehicle_ref=vehicle.pk,
            gear_speed=gear_speed,
            gear_from=gear_from,
            gear_to=gear_to,
            error=error["error"],
            error_message=error["message"],
        )
    return None


def add_vehicle(vin: str, make: str, year: int, vtype: str) -> None:
    if type(make) != str or type(year) != int or type(vin) != str or type(vtype) != str:
        raise ValueError("Invalid vehicle data")
    vtype_proper = vtype.capitalize()
    type_name = get_vehicle_type(vtype_proper)
    if type_name.type_name != vtype_proper:
        raise ValueError("Invalid vehicle type")
    with db.atomic():
        Vehicle.create(vin=vin, type_make=make, type_year=year, type_ref=type_name.pk)


def average_speed_to_fourth_gear():
    # SQL - SELECT AVG(gear_speed) FROM transmissionlog WHERE (gear_to = 4);
    average_speed = (
        TransmissionLog.select(
            fn.AVG(TransmissionLog.gear_speed).coerce(False).alias("average_speed")
        )
        .where(TransmissionLog.gear_to == 4)
        .scalar()
    )
    return average_speed


def error_frequency_previous_last_week():
    # SQL - SELECT COUNT(error) FROM transmissionlog WHERE (date_timestamp BETWEEN DATE('now', '-7 day') AND DATE('now'));
    # SQL - SELECT vin FROM transmissionlog WHERE (date_timestamp BETWEEN DATE('now', '-7 day') AND (date_timestamp > DATE('now', '-30 day') AND error = 1)
    error_frequency = (
        TransmissionLog.select(fn.COUNT(TransmissionLog.error).alias("error_frequency"))
        .where(
            TransmissionLog.date_timestamp
            >= datetime.datetime.now() - datetime.timedelta(days=7),
            TransmissionLog.date_timestamp
            <= datetime.datetime.now() - datetime.timedelta(days=30),
            TransmissionLog.error == 1,
        )
        .scalar()
    )
    return error_frequency

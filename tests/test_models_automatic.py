import unittest
from functools import wraps, partial
from playhouse.sqlite_ext import SqliteExtDatabase
from peewee import SqliteDatabase, OperationalError
from models.automatic import (
    GearChangeConfig,
    TransmissionLog,
    Vehicle,
    VehicleType,
    preload_config,
    configs_loaded,
    check_existance,
    get_vehicle_type,
    get_vehicle,
    add_vehicle,
    get_gear_config_by_vtid_gearto,
    get_vehicle_type_ref,
    is_error,
    shift_log_add,
    average_speed_to_fourth_gear,
    error_frequency_previous_last_week,
)

MODELS = [GearChangeConfig, TransmissionLog, Vehicle, VehicleType]

test_db = SqliteDatabase(":memory:")


class TestAutomatic(unittest.TestCase):
    def setUp(self):
        self.db = test_db
        self.db.bind(MODELS, bind_refs=False, bind_backrefs=False)
        try:
            self.db.connect()
        except OperationalError:
            pass
        self.db.create_tables(MODELS)

    def tearDown(self):
        self.db.drop_tables(MODELS)
        self.db.close()

    def test_preload_config(self):
        # Initialize Configs for testing
        results = GearChangeConfig.select().count()
        self.assertEqual(0, results)  # Verify configs are empty
        preload_config()
        new_results = (
            GearChangeConfig.select().count()
        )  # Verify configs have been loaded
        self.assertEqual(20, new_results)

    def test_configs_loaded(self):
        # Initialize Configs for testing
        self.assertFalse(configs_loaded())
        preload_config()
        self.assertTrue(configs_loaded())

    def test_tables_exist(self):
        # Verify tables exist
        self.assertTrue(GearChangeConfig.table_exists())
        self.assertTrue(TransmissionLog.table_exists())
        self.assertTrue(Vehicle.table_exists())
        self.assertTrue(VehicleType.table_exists())
        # Verify tables are empty
        self.assertEqual(0, GearChangeConfig.select().count())
        self.assertEqual(0, TransmissionLog.select().count())
        self.assertEqual(0, Vehicle.select().count())
        self.assertEqual(0, VehicleType.select().count())

    def test_check_existance(self):
        results = check_existance()
        self.assertEqual(type(results), SqliteDatabase)

    def test_get_vehicle_type(self):
        # Initialize Configs for testing
        preload_config()
        # Verify vehicle type exists
        vehicle_type = get_vehicle_type("car")
        self.assertEqual(vehicle_type.type_name, "Car")
        self.assertEqual(vehicle_type.fuel_type, "Gasoline")
        # Test Negative Case
        vehicle_type = get_vehicle_type("plane")
        self.assertFalse(vehicle_type)

    def test_get_vehicle(self):
        # Initialize Configs for testing
        preload_config()
        # Add entry to test with
        vin, make, year, type = "ABC12345", "Toyota", 2010, "Car"

        add_vehicle(vin, make, year, type)
        vehicle = get_vehicle(vin)
        self.assertEqual(vehicle.vin, vin)
        self.assertEqual(vehicle.type_make, make)
        self.assertEqual(vehicle.type_year, year)
        # Test negative case
        self.assertRaises(ValueError, get_vehicle, "Something Wrong")

    def test_get_gear_config_by_vtid_gearto(self):
        # Add Configs
        preload_config()
        # Setup Vehicle
        vin, make, year, type = "ABC12345", "Toyota", 2010, "Car"
        add_vehicle(vin, make, year, type)
        # Prepwork for function
        gear_to = 4
        vehicle = get_vehicle(vin)
        vtObj = VehicleType.get(VehicleType.pk == vehicle.type_ref)
        vehicle_type = get_vehicle_type(vtObj.type_name)
        Config = get_gear_config_by_vtid_gearto(vehicle_type.pk, gear_to)
        self.assertEqual(Config.vehicle_type_ref, 2)
        self.assertEqual(Config.speed, 40)
        self.assertEqual(Config.gear_from, 3)
        self.assertEqual(Config.gear_to, 4)
        # Test Negative Case
        BadConfig = get_gear_config_by_vtid_gearto("ABC", 10)
        self.assertIsNone(BadConfig)

    def test_get_vehicle_type_ref(self):
        # Add Configs
        preload_config()
        # Setup Vehicle
        vin, make, year, type = "ABC12345", "Toyota", 2010, "Car"
        add_vehicle(vin, make, year, type)
        # Setup test
        vehicle_type_ref = 2
        VehicleType = get_vehicle_type_ref(vehicle_type_ref)
        self.assertEqual(VehicleType.type_name, "Car")
        self.assertEqual(VehicleType.fuel_type, "Gasoline")
        # Test Negative Case
        self.assertRaises(ValueError, get_vehicle_type_ref, 9999)

    def test_is_error(self):
        # Non-error test case
        gear_speed, actual_speed, gear_from, gear_to = 20, 12, 1, 2
        error = is_error(gear_speed, actual_speed, gear_from, gear_to)
        self.assertEqual(error, {"error": False, "message": "No Error Detected"})
        # Error test case
        gear_speed, actual_speed = 12, 20
        error = is_error(gear_speed, actual_speed, gear_from, gear_to)
        self.assertEqual(
            error,
            {
                "error": True,
                "message": f"Gear shift exceeded at {actual_speed}, expected {gear_speed}, shifting from {gear_from} to {gear_to}",
            },
        )

    def test_shift_log_add(self):
        # Add Configs
        preload_config()
        # Setup Vehicle
        vin, make, year, type = "ABC12345", "Toyota", 2010, "Car"
        add_vehicle(vin, make, year, type)
        # Setup test
        gear_speed, gear_from, gear_to = 20, 1, 2
        shift_log_add(vin, gear_speed, gear_from, gear_to)
        # Test Negative Case - Invalid VIN
        vin, gear_speed, gear_from, gear_to = "ABC12345SS", 20, 1, 2
        with self.assertRaises(ValueError):
            shift_log_add(vin, gear_speed, gear_from, gear_to)
        # Test Negative Case - Invalid Gear Speed
        vin, gear_speed, gear_from, gear_to = "ABC12345", "20", 1, 2
        with self.assertRaises(ValueError):
            shift_log_add(vin, gear_speed, gear_from, gear_to)
        # Test Negative Case - Invalid Gear From
        vin, gear_speed, gear_from, gear_to = 2, 20, 1, 2
        with self.assertRaises(ValueError):
            shift_log_add(vin, gear_speed, gear_from, gear_to)

    def test_add_vehicle(self):
        # Add Configs
        preload_config()
        # Setup Vehicle
        vin, make, year, vtype = "ABC12345", "Toyota", 2010, "Car"
        add_vehicle(vin, make, year, vtype)
        vehicle = Vehicle.get(Vehicle.vin == vin)
        self.assertEqual(vehicle.vin, vin)
        self.assertEqual(vehicle.type_make, make)
        self.assertEqual(vehicle.type_year, year)
        self.assertEqual(vehicle.type_ref, 2)
        # Test Negative Case
        vtype = "Saturn"
        with self.assertRaises(ValueError):
            add_vehicle(vin, make, year, type)

    def test_average_speed_to_fourth_gear(self):
        # Add Configs
        preload_config()
        # Setup Vehicle
        vin, make, year, vtype = "ABC12345", "Toyota", 2010, "Car"
        add_vehicle(vin, make, year, vtype)
        gear_speed, gear_from, gear_to = 42, 3, 4
        shift_log_add(vin, gear_speed, gear_from, gear_to)

        vin2, make2, year2, vtype2 = "ABC123456", "Ford", 2010, "Truck"
        add_vehicle(vin2, make2, year2, vtype2)
        gear_speed2, gear_from2, gear_to2 = 40, 3, 4
        shift_log_add(vin2, gear_speed2, gear_from2, gear_to2)

        self.assertEqual(average_speed_to_fourth_gear(), 41.0)

    def test_error_frequency_previous_last_week(self):
        # Add Configs
        preload_config()
        # Setup Vehicle

        vin, make, year, vtype = "ABC12345", "Toyota", 2010, "Car"
        add_vehicle(vin, make, year, vtype)
        gear_speed, gear_from, gear_to = 42, 3, 4
        shift_log_add(vin, gear_speed, gear_from, gear_to)

        vin, make, year, vtype = "ABC123456", "Ford", 2010, "Truck"
        add_vehicle(vin, make, year, vtype)
        gear_speed, gear_from, gear_to = 40, 3, 4
        shift_log_add(vin, gear_speed, gear_from, gear_to)

        result = error_frequency_previous_last_week()
        print(result)


if __name__ == "__main__":
    unittest.main()

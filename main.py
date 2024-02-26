import json
import argparse
from models.automatic import (
    check_existance,
    add_vehicle,
    shift_log_add,
    average_speed_to_fourth_gear,
)

# Some questions that were not provided when recieving this assessment.
# 1. What type of input is expected. Currerntly this accepts CLI arguments.
# 2. The assessment says its for an Automatic Transmission but arguments are for Manual Transmission.
# 3. Regarding "Automatic Gear Shifts", should we only accept the argument of Speed/RPM?
# 4. If "Automatic Gear Shift" takes place, does it make this use-case potentially false
# since the application expects to shift gear given the existing requirerments?

# Gear shift Input Example
# {"speed": 0.0, "gear_to": 2, "gear_from": 1}

# VIN shift log input:
# {"vin": "1G1ZZ8F", "speed": 15, "gear_to": 2, "gear_from": 1}
# --vin 1G1ZZ8F --speed 15 --gear_to 2 --gear_from 1

parser = argparse.ArgumentParser()

# Primary usage for entering shift details
parser.add_argument("--shift-log", action="store_true")
parser.add_argument(
    "--vin", type=str, default=None, help="VIN must exist in the database."
)
parser.add_argument("--speed", type=int, default=0)
parser.add_argument("--gear_to", type=int, default=0)
parser.add_argument("--gear_from", type=int, default=0)

# Adding a vehicle
parser.add_argument(
    "--vehicle-add", default=None, action="store_true", help="Add a vehicle"
)
parser.add_argument("--vehicle", action="store", default=None)

# Average speed to fourth gear
parser.add_argument("--average-speed", action="store_true")

args = parser.parse_args()
db = check_existance()

if args.shift_log:
    # Example:
    # python main.py --shift-log --vin 1G1ZZ8F --speed 15 --gear_to 2 --gear_from 1
    # python main.py --shift-log --vin ABC1234 --speed 48 --gear_to 3 --gear_from 4
    # python main.py --shift-log --vin ABC1234 --speed 48 --gear_to 3 --gear_from 4 --vehicle-add --vehicle '{"vin": "ABC1234", "make": "Honda", "year": 2020, "type": "car"}'
    if not args.vin or not args.speed or not args.gear_to or not args.gear_from:
        print("Missing required arguments")
        exit(1)
    shift_log_add(args.vin, args.speed, args.gear_from, args.gear_to)


if args.vehicle_add:
    # Example:
    # python main.py --vehicle-add --vehicle '{"vin": "ABC123", "make": "Honda", "year": 2020, "type": "car"}'
    if not args.vehicle:
        print("Missing required arguments")
        exit(1)
    vehicle = json.loads(args.vehicle)
    try:
        add_vehicle(vehicle["vin"], vehicle["make"], vehicle["year"], vehicle["type"])
    except AttributeError:
        print("Invalid vehicle details, please use {'vin', 'make', 'year', 'type'}")

if args.average_speed:
    # Example:
    # python main.py --average-speed
    print(average_speed_to_fourth_gear())

if __name__ == "__main__":
    shift_log_add("ABC1234", 15, 1, 2)

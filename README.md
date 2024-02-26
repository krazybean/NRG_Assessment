# Assessment for NRG

Assessment to implement handling input from an Automatic Transmission Gear Change

## Instructions

```
Create a python-based solution to respond to the manual inputs of an automobile gear shift with automatic transmission, as well as dealing with automated gear shifts.

This should include Unit Testing for the basic scenarios.

Logging (this is a company log for all of its models by vin number):
  - Log the speed at which the gear changes from one level to another.
  - Log as an error any time the speed exceeds a defined level without causing a gear change.

Build sample queries to show the following:
  - What is the average speed that causes a gear to change from 3 to 4 by car type.
  - For any car that had an error in gear changes prior to one month ago, has it experienced any errors in the last 7 days?
```

## Installation

```bash
pip install -r requirements.txt
```

## Testing

```bash
python -m unittest tests.test_models_automatic
```

## Usage

```bash

# Create Vehicle Entry
python main.py --vehicle-add --vehicle '{"vin": "ABC123", "make": "Honda", "year": 2020, "type": "car"}'

# Add log entry:
python main.py --shift-log --vin 1G1ZZ8F --speed 15 --gear_to 2 --gear_from 1

# Get Average Speed:
python main.py --average-speed
```

## Query requirements are found at the bottom of models/automatic.p

Query requirements defined by the question are found at the end of models/automatic.py

## License

[MIT](https://choosealicense.com/licenses/mit/)

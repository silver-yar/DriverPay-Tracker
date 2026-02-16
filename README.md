# DriverPay-Tracker

DriverPay Tracker is a desktop application designed to help delivery drivers accurately track orders, tips, mileage, cash flow, and total earnings during a work shift.

## Features

- Track multiple drivers
- Record shift details: date, start/end time, mileage, cash/credit tips, owed amounts, hourly rate
- View shift history with date range filtering
- Calculate summary statistics (total mileage, tips, owed, average hourly rate)
- Add, edit, and delete shifts
- Persistent SQLite database storage

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone or download the repository:
   ```bash
   git clone <repository-url>
   cd DriverPay-Tracker
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Build the database:
   ```bash
   python src/db/db_setup.py
   ```
   
   ⚠️ **Warning**: Running the database setup script will append to any existing database file, which may cause schema conflicts. If you have an existing database, delete it first:
   ```bash
   rm src/driver_pay_tracker.db
   ```
   Then run the setup script.

## Running the Application

1. Ensure the virtual environment is activated.

2. Run the application:
   ```bash
   python src/main.py
   ```

3. The application window will open. Use the interface to:
   - Select a driver from the sidebar
   - Filter shifts by date range using the date inputs and Search button
   - Add new shifts using the "Add Shift" button
   - Edit existing shifts by selecting one and clicking "Edit Shift"
   - Delete shifts by selecting them and clicking "Delete Shift"

## Database Setup

The application uses SQLite for data storage. The database file `src/driver_pay_tracker.db` is created by running `src/db/db_setup.py`. This script creates the necessary tables (drivers, shifts, deliveries) and populates them with sample data.

## Testing

Run the test suite to verify functionality:

```bash
python -m pytest tests/ -v
```

## Development

- Database operations are handled by `src/db/db_handler.py`
- UI is built with HTML/CSS/JavaScript in `src/ui/`
- Main application entry point is `src/main.py`

## Technologies Used

- Python 3
- PySide6 (Qt for Python)
- SQLite
- HTML/CSS/JavaScript for UI
- pytest for testing

## License

See LICENSE file for details.

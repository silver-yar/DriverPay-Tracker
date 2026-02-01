import sqlite3

import pytest

from src.db.db_handler import DBHandler


@pytest.fixture
def db_handler():
    # In-memory database for testing
    handler = DBHandler(":memory:")
    # Sample database
    setup_database(handler.conn)
    return handler


def setup_database(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            mileage REAL NOT NULL,
            cash_tips REAL NOT NULL,
            credit_tips REAL NOT NULL,
            owed REAL NOT NULL,
            hourly_rate REAL NOT NULL,
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        )
    """)
    # Sample data
    cursor.execute("INSERT INTO drivers (name) VALUES ('John Smith')")
    cursor.execute("INSERT INTO drivers (name) VALUES ('Sarah Davis')")
    cursor.execute(
        "INSERT INTO shifts (driver_id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate) VALUES (1, '2023-01-01', '08:00', '16:00', 100.0, 50.00, 40.00, 10.00, 15.00)"
    )
    cursor.execute(
        "INSERT INTO shifts (driver_id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate) VALUES (1, '2023-01-02', '09:00', '17:00', 120.0, 60.00, 50.00, 15.00, 16.00)"
    )
    conn.commit()


def test_get_drivers(db_handler):
    drivers = db_handler.get_drivers()
    import json

    drivers_list = json.loads(drivers)
    assert len(drivers_list) == 2
    assert drivers_list[0]["name"] == "John Smith"


def test_get_shifts(db_handler):
    shifts = db_handler.get_shifts(1)
    import json

    shifts_list = json.loads(shifts)
    assert len(shifts_list) == 2
    assert shifts_list[0]["date"] == "2023-01-02"  # Ordered by date desc
    assert "id" in shifts_list[0]


def test_add_shift(db_handler):
    db_handler.add_shift(
        1, "2023-01-03", "10:00", "18:00", 110.0, 55.00, 45.00, 12.00, 15.50
    )
    shifts = db_handler.get_shifts(1)
    import json

    shifts_list = json.loads(shifts)
    assert len(shifts_list) == 3


def test_get_summary(db_handler):
    summary = db_handler.get_summary(1)
    import json

    summary_dict = json.loads(summary)
    assert summary_dict["total_mileage"] == 220.0
    assert summary_dict["total_cash"] == 110.0
    assert summary_dict["total_credit"] == 90.0
    assert summary_dict["total_owed"] == 25.0
    assert summary_dict["avg_hourly"] == 15.5


def test_get_shift(db_handler):
    shift = db_handler.get_shift(1)
    import json

    shift_dict = json.loads(shift)
    assert shift_dict["date"] == "2023-01-01"
    assert shift_dict["mileage"] == 100.0


def test_update_shift(db_handler):
    db_handler.update_shift(
        1, "2023-01-01", "08:30", "16:30", 105.0, 52.00, 42.00, 11.00, 15.25
    )
    shift = db_handler.get_shift(1)
    import json

    shift_dict = json.loads(shift)
    assert shift_dict["start_time"] == "08:30"
    assert shift_dict["mileage"] == 105.0


def test_delete_shift(db_handler):
    db_handler.delete_shift(1)
    shifts = db_handler.get_shifts(1)
    import json

    shifts_list = json.loads(shifts)
    assert len(shifts_list) == 1

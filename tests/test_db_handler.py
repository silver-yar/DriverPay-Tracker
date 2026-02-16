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
    cursor.execute("""
        CREATE TABLE deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            order_num TEXT,
            payment_type TEXT NOT NULL,
            order_subtotal REAL NOT NULL,
            amount_collected REAL NOT NULL,
            tip REAL NOT NULL,
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        )
    """)
    # Sample shift data
    cursor.execute("INSERT INTO drivers (name) VALUES ('John Smith')")
    cursor.execute("INSERT INTO drivers (name) VALUES ('Sarah Davis')")
    cursor.execute(
        "INSERT INTO shifts (driver_id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate) VALUES (1, '2023-01-01', '08:00', '16:00', 100.0, 50.00, 40.00, 10.00, 15.00)"
    )
    cursor.execute(
        "INSERT INTO shifts (driver_id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate) VALUES (1, '2023-01-02', '09:00', '17:00', 120.0, 60.00, 50.00, 15.00, 16.00)"
    )
    # Sample delivery data
    cursor.execute(
        "INSERT INTO deliveries (driver_id, date, order_num, payment_type, order_subtotal, amount_collected, tip) VALUES (1, '2023-01-01', '#1001', 'Credit', 25.00, 30.00, 5.00)"
    )
    cursor.execute(
        "INSERT INTO deliveries (driver_id, date, order_num, payment_type, order_subtotal, amount_collected, tip) VALUES (1, '2023-01-02', '#1002', 'Cash', 40.00, 45.00, 5.00)"
    )
    cursor.execute(
        "INSERT INTO deliveries (driver_id, date, order_num, payment_type, order_subtotal, amount_collected, tip) VALUES (2, '2023-01-01', '#2001', 'Debit', 18.50, 22.00, 3.50)"
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


def test_get_deliveries(db_handler):
    deliveries = db_handler.get_deliveries(1)
    import json

    deliveries_list = json.loads(deliveries)
    assert len(deliveries_list) == 2
    assert deliveries_list[0]["date"] == "2023-01-02"  # Ordered by date desc
    assert deliveries_list[0]["payment_type"] == "Cash"
    assert deliveries_list[0]["order_subtotal"] == "$40.00"
    assert deliveries_list[0]["amount_collected"] == "$45.00"
    assert deliveries_list[0]["tip"] == "$5.00"
    assert "id" in deliveries_list[0]


def test_get_delivery(db_handler):
    delivery = db_handler.get_delivery(1)
    import json

    delivery_dict = json.loads(delivery)
    assert delivery_dict["date"] == "2023-01-01"
    assert delivery_dict["order_num"] == "#1001"
    assert delivery_dict["payment_type"] == "Credit"
    assert delivery_dict["order_subtotal"] == 25.00
    assert delivery_dict["amount_collected"] == 30.00
    assert delivery_dict["tip"] == 5.00


def test_add_delivery(db_handler):
    db_handler.add_delivery(1, "2023-01-03", "#1003", "Debit", 32.00, 38.00, 6.00)
    deliveries = db_handler.get_deliveries(1)
    import json

    deliveries_list = json.loads(deliveries)
    assert len(deliveries_list) == 3


def test_update_delivery(db_handler):
    db_handler.update_delivery(
        1, "2023-01-01", "#1001-UPDATED", "Cash", 26.00, 31.00, 5.00
    )
    delivery = db_handler.get_delivery(1)
    import json

    delivery_dict = json.loads(delivery)
    assert delivery_dict["order_num"] == "#1001-UPDATED"
    assert delivery_dict["payment_type"] == "Cash"
    assert delivery_dict["order_subtotal"] == 26.00
    assert delivery_dict["amount_collected"] == 31.00


def test_delete_delivery(db_handler):
    db_handler.delete_delivery(1)
    deliveries = db_handler.get_deliveries(1)
    import json

    deliveries_list = json.loads(deliveries)
    assert len(deliveries_list) == 1


def test_get_deliveries_summary(db_handler):
    summary = db_handler.get_deliveries_summary(1)
    import json

    summary_dict = json.loads(summary)
    assert summary_dict["delivery_count"] == 2
    assert summary_dict["total_subtotal"] == 65.00
    assert summary_dict["total_collected"] == 75.00
    assert summary_dict["total_tips"] == 10.00


def test_add_delivery_negative_subtotal(db_handler):
    import json

    result = db_handler.add_delivery(
        1, "2023-01-03", "#1003", "Cash", -10.00, 15.00, 5.00
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert "subtotal cannot be negative" in str(result_dict["errors"])


def test_add_delivery_negative_collected(db_handler):
    import json

    result = db_handler.add_delivery(
        1, "2023-01-03", "#1003", "Cash", 10.00, -5.00, -15.00
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert "collected cannot be negative" in str(result_dict["errors"])


def test_add_delivery_too_many_decimals(db_handler):
    import json

    result = db_handler.add_delivery(
        1, "2023-01-03", "#1003", "Cash", 10.999, 15.00, 4.001
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert "more than 2 decimal places" in str(result_dict["errors"])


def test_add_delivery_valid_values(db_handler):
    import json

    result = db_handler.add_delivery(
        1, "2023-01-03", "#1003", "Credit", 25.50, 32.75, 7.25
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == True


def test_add_delivery_collected_less_than_subtotal(db_handler):
    import json

    # Test that amount collected cannot be less than subtotal
    result = db_handler.add_delivery(
        1, "2023-01-03", "#1003", "Cash", 30.00, 25.00, -5.00
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert (
        "amount collected cannot be less than order subtotal"
        in str(result_dict["errors"]).lower()
    )


def test_update_delivery_validation(db_handler):
    import json

    # Test update with negative value
    result = db_handler.update_delivery(
        1, "2023-01-01", "#1001", "Cash", -5.00, 10.00, 15.00
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False

    # Test update with too many decimals
    result = db_handler.update_delivery(
        1, "2023-01-01", "#1001", "Cash", 25.123, 30.00, 4.877
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False

    # Test update with collected less than subtotal
    result = db_handler.update_delivery(
        1, "2023-01-01", "#1001", "Cash", 40.00, 35.00, -5.00
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert (
        "amount collected cannot be less than order subtotal"
        in str(result_dict["errors"]).lower()
    )

    # Test update with valid values
    result = db_handler.update_delivery(
        1, "2023-01-01", "#1001", "Debit", 26.00, 31.50, 5.50
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == True

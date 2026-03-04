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
            starting_mileage REAL NOT NULL,
            ending_mileage REAL NOT NULL,
            mileage REAL NOT NULL,
            cash_tips REAL NOT NULL,
            credit_tips REAL NOT NULL,
            owed REAL NOT NULL,
            mileage_rate REAL NOT NULL,
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            shift_id INTEGER,
            date TEXT NOT NULL,
            order_num TEXT,
            payment_type TEXT NOT NULL,
            order_subtotal REAL NOT NULL,
            amount_collected REAL NOT NULL,
            card_tip REAL NOT NULL,
            cash_tip REAL DEFAULT 0.0,
            mileage REAL DEFAULT 0.0,
            FOREIGN KEY (driver_id) REFERENCES drivers (id),
            FOREIGN KEY (shift_id) REFERENCES shifts (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            default_mileage_rate REAL NOT NULL DEFAULT 0.65
        )
    """)
    cursor.execute("INSERT INTO settings (id, default_mileage_rate) VALUES (1, 0.65)")
    # Sample shift data
    cursor.execute("INSERT INTO drivers (name) VALUES ('John Smith')")
    cursor.execute("INSERT INTO drivers (name) VALUES ('Sarah Davis')")
    cursor.execute(
        "INSERT INTO shifts (driver_id, date, start_time, end_time, starting_mileage, ending_mileage, mileage, cash_tips, credit_tips, owed, mileage_rate) VALUES (1, '2023-01-01', '08:00', '16:00', 1000, 1100, 100.0, 50.00, 40.00, 10.00, 15.00)"
    )
    cursor.execute(
        "INSERT INTO shifts (driver_id, date, start_time, end_time, starting_mileage, ending_mileage, mileage, cash_tips, credit_tips, owed, mileage_rate) VALUES (1, '2023-01-02', '09:00', '17:00', 1100, 1220, 120.0, 60.00, 50.00, 15.00, 16.00)"
    )
    # Sample delivery data
    cursor.execute(
        "INSERT INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage) VALUES (1, 1, '2023-01-01', '#1001', 'Credit', 25.00, 30.00, 5.00, 2.00, 8.00)"
    )
    cursor.execute(
        "INSERT INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage) VALUES (1, 2, '2023-01-02', '#1002', 'Cash', 40.00, 45.00, 5.00, 0.00, 12.00)"
    )
    cursor.execute(
        "INSERT INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage) VALUES (2, NULL, '2023-01-01', '#2001', 'Debit', 18.50, 22.00, 3.50, 1.50, 3.50)"
    )
    conn.commit()


def test_get_drivers(db_handler):
    drivers = db_handler.get_drivers()
    import json

    drivers_list = json.loads(drivers)
    assert len(drivers_list) == 2
    assert drivers_list[0]["name"] == "John Smith"


def test_add_driver(db_handler):
    import json

    result = db_handler.add_driver("Taylor Green")
    result_dict = json.loads(result)
    assert result_dict["success"] == True

    drivers = json.loads(db_handler.get_drivers())
    assert any(d["name"] == "Taylor Green" for d in drivers)


def test_add_driver_duplicate_and_empty_name(db_handler):
    import json

    duplicate = json.loads(db_handler.add_driver("John Smith"))
    assert duplicate["success"] == False

    empty = json.loads(db_handler.add_driver("   "))
    assert empty["success"] == False


def test_delete_driver(db_handler):
    import json

    # Driver 2 has one delivery and no shifts in seed data.
    result = json.loads(db_handler.delete_driver("Sarah Davis"))
    assert result["success"] == True

    drivers = json.loads(db_handler.get_drivers())
    assert all(d["name"] != "Sarah Davis" for d in drivers)

    deliveries = json.loads(db_handler.get_deliveries(2))
    assert len(deliveries) == 0


def test_delete_driver_not_found_and_empty_name(db_handler):
    import json

    not_found = json.loads(db_handler.delete_driver("Missing Driver"))
    assert not_found["success"] == False

    empty = json.loads(db_handler.delete_driver(""))
    assert empty["success"] == False


def test_get_shifts(db_handler):
    shifts = db_handler.get_shifts(1)
    import json

    shifts_list = json.loads(shifts)
    assert len(shifts_list) == 2
    assert shifts_list[0]["date"] == "2023-01-02"  # Ordered by date desc
    assert "id" in shifts_list[0]


def test_add_shift(db_handler):
    db_handler.add_shift(
        1, "2023-01-03", "10:00", "18:00", 1220, 1330, 55.00, 45.00, 12.00, 15.50
    )
    shifts = db_handler.get_shifts(1)
    import json

    shifts_list = json.loads(shifts)
    assert len(shifts_list) == 3


def test_get_summary(db_handler):
    summary = db_handler.get_summary(1)
    import json

    summary_dict = json.loads(summary)
    assert summary_dict["total_mileage"] == 20.0
    assert summary_dict["total_cash"] == 2.0
    assert summary_dict["total_credit"] == 10.0
    assert summary_dict["total_owed"] == -33.0
    assert summary_dict["avg_mileage_rate"] == 15.5


def test_shift_totals_sync_from_deliveries(db_handler):
    import json

    # Add delivery linked to shift 1 and verify shift totals come from deliveries.
    db_handler.add_delivery(
        1, 1, "2023-01-03", "#1009", "Credit", 20.0, 25.0, 5.0, 1.0, 3.0
    )
    shifts = json.loads(db_handler.get_shifts(1))
    shift_1 = next(s for s in shifts if s["id"] == 1)

    # Shift 1 seeded deliveries: card 5.00 + cash 2.00, then + (5.00, 1.00)
    assert shift_1["credit"] == "$10.00"
    assert shift_1["cash"] == "$3.00"
    assert shift_1["mileage"] == 11.0


def test_get_shift(db_handler):
    shift = db_handler.get_shift(1)
    import json

    shift_dict = json.loads(shift)
    assert shift_dict["date"] == "2023-01-01"
    assert shift_dict["mileage"] == 100.0


def test_update_shift(db_handler):
    db_handler.update_shift(
        1, "2023-01-01", "08:30", "16:30", 1000, 1105, 52.00, 42.00, 11.00, 15.25
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
    assert deliveries_list[0]["card_tip"] == "$5.00"
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
    assert delivery_dict["card_tip"] == 5.00
    assert delivery_dict["mileage"] == 8.00


def test_add_delivery(db_handler):
    db_handler.add_delivery(
        1, None, "2023-01-03", "#1003", "Debit", 32.00, 38.00, 6.00, 0, 4.0
    )
    deliveries = db_handler.get_deliveries(1)
    import json

    deliveries_list = json.loads(deliveries)
    assert len(deliveries_list) == 3


def test_update_delivery(db_handler):
    db_handler.update_delivery(
        1, 1, "2023-01-01", "#1001-UPDATED", "Cash", 26.00, 31.00, 5.00, 0, 9.0
    )
    delivery = db_handler.get_delivery(1)
    import json

    delivery_dict = json.loads(delivery)
    assert delivery_dict["order_num"] == "#1001-UPDATED"
    assert delivery_dict["payment_type"] == "Cash"
    assert delivery_dict["order_subtotal"] == 26.00
    assert delivery_dict["amount_collected"] == 31.00
    assert delivery_dict["mileage"] == 9.0


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
        1, None, "2023-01-03", "#1003", "Cash", -10.00, 15.00, 5.00, 0, 1.0
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert "subtotal cannot be negative" in str(result_dict["errors"])


def test_add_delivery_negative_collected(db_handler):
    import json

    result = db_handler.add_delivery(
        1, None, "2023-01-03", "#1003", "Cash", 10.00, -5.00, -15.00, 0, 1.0
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert "collected cannot be negative" in str(result_dict["errors"])


def test_add_delivery_too_many_decimals(db_handler):
    import json

    result = db_handler.add_delivery(
        1, None, "2023-01-03", "#1003", "Cash", 10.999, 15.00, 4.001, 0, 1.111
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert "more than 2 decimal places" in str(result_dict["errors"])


def test_add_delivery_valid_values(db_handler):
    import json

    result = db_handler.add_delivery(
        1, None, "2023-01-03", "#1003", "Credit", 25.50, 32.75, 7.25, 0, 2.25
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == True


def test_add_delivery_collected_less_than_subtotal(db_handler):
    import json

    # Test that amount collected cannot be less than subtotal
    result = db_handler.add_delivery(
        1, None, "2023-01-03", "#1003", "Cash", 30.00, 25.00, -5.00, 0, 1.0
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
        1, 1, "2023-01-01", "#1001", "Cash", -5.00, 10.00, 15.00, 0, 1.0
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False

    # Test update with too many decimals
    result = db_handler.update_delivery(
        1, 1, "2023-01-01", "#1001", "Cash", 25.123, 30.00, 4.877, 0, 1.0
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False

    # Test update with collected less than subtotal
    result = db_handler.update_delivery(
        1, 1, "2023-01-01", "#1001", "Cash", 40.00, 35.00, -5.00, 0, 1.0
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == False
    assert (
        "amount collected cannot be less than order subtotal"
        in str(result_dict["errors"]).lower()
    )

    # Test update with valid values
    result = db_handler.update_delivery(
        1, 1, "2023-01-01", "#1001", "Debit", 26.00, 31.50, 5.50, 0, 1.25
    )
    result_dict = json.loads(result)
    assert result_dict["success"] == True


def test_get_settings(db_handler):
    settings = db_handler.get_settings()
    import json

    settings_dict = json.loads(settings)
    assert settings_dict["default_mileage_rate"] == 0.65


def test_update_settings(db_handler):
    db_handler.update_settings(0.75)
    settings = db_handler.get_settings()
    import json

    settings_dict = json.loads(settings)
    assert settings_dict["default_mileage_rate"] == 0.75

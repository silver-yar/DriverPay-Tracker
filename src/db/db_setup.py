import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "driver_pay_tracker.db")


def create_database():
    """Create the SQLite database and tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
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
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            shift_id INTEGER,
            date TEXT NOT NULL,
            order_num INTEGER,
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

    # Migration support for existing databases without mileage on deliveries.
    cursor.execute("PRAGMA table_info(deliveries)")
    delivery_columns = [row[1] for row in cursor.fetchall()]
    if "mileage" not in delivery_columns:
        cursor.execute("ALTER TABLE deliveries ADD COLUMN mileage REAL DEFAULT 0.0")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            default_mileage_rate REAL NOT NULL DEFAULT 0.65
        )
    """)

    # Insert default settings if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO settings (id, default_mileage_rate)
        VALUES (1, 0.65)
    """)

    # Sample drivers
    cursor.execute("INSERT OR IGNORE INTO drivers (name) VALUES ('John Smith')")
    cursor.execute("INSERT OR IGNORE INTO drivers (name) VALUES ('Sarah Davis')")
    cursor.execute("INSERT OR IGNORE INTO drivers (name) VALUES ('Mike Johnson')")

    # Sample shifts. Values for mileage/cash/credit/owed are derived from deliveries below.
    cursor.execute("""
        INSERT OR IGNORE INTO shifts (driver_id, date, start_time, end_time, starting_mileage, ending_mileage, mileage, cash_tips, credit_tips, owed, mileage_rate)
        VALUES (1, '2026-01-05', '10:00', '16:00', 0, 0, 0, 0, 0, 0, 0.65)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO shifts (driver_id, date, start_time, end_time, starting_mileage, ending_mileage, mileage, cash_tips, credit_tips, owed, mileage_rate)
        VALUES (1, '2026-01-06', '11:30', '17:30', 0, 0, 0, 0, 0, 0, 0.65)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO shifts (driver_id, date, start_time, end_time, starting_mileage, ending_mileage, mileage, cash_tips, credit_tips, owed, mileage_rate)
        VALUES (2, '2026-01-05', '12:00', '18:00', 0, 0, 0, 0, 0, 0, 0.65)
    """)

    # Sample deliveries linked to shifts.
    # Shift totals are calculated from this delivery data.
    cursor.execute("""
        INSERT OR IGNORE INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage)
        VALUES (1, 1, '2026-01-05', 1001, 'Credit', 25.00, 30.00, 5.00, 0, 4.2)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage)
        VALUES (1, 1, '2026-01-05', 1002, 'Cash', 40.00, 50.00, 0, 10.00, 5.3)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage)
        VALUES (1, 2, '2026-01-06', 1003, 'Debit', 30.00, 38.00, 8.00, 0, 3.8)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage)
        VALUES (1, 2, '2026-01-06', 1004, 'Credit', 20.00, 25.00, 5.00, 0, 2.9)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage)
        VALUES (2, 3, '2026-01-05', 2001, 'Cash', 28.00, 35.00, 0, 7.00, 4.1)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage)
        VALUES (2, 3, '2026-01-05', 2002, 'Credit', 22.00, 27.00, 5.00, 0, 3.6)
    """)

    # Sync shift totals from deliveries (single source of truth).
    cursor.execute("""
        UPDATE shifts SET
            mileage = ROUND((SELECT COALESCE(SUM(mileage), 0) FROM deliveries WHERE shift_id = shifts.id), 2),
            credit_tips = (SELECT COALESCE(SUM(card_tip), 0) FROM deliveries WHERE shift_id = shifts.id),
            cash_tips = (SELECT COALESCE(SUM(cash_tip), 0) FROM deliveries WHERE shift_id = shifts.id),
            owed = (SELECT COALESCE(SUM(card_tip), 0) FROM deliveries WHERE shift_id = shifts.id) +
                   (SELECT COALESCE(SUM(cash_tip), 0) FROM deliveries WHERE shift_id = shifts.id) -
                   (SELECT COALESCE(SUM(CASE WHEN payment_type = 'Cash' THEN amount_collected ELSE 0 END), 0) FROM deliveries WHERE shift_id = shifts.id)
    """)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    create_database()

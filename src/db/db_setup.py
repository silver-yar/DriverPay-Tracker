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
            mileage REAL NOT NULL,
            cash_tips REAL NOT NULL,
            credit_tips REAL NOT NULL,
            owed REAL NOT NULL,
            hourly_rate REAL NOT NULL,
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        )
    """)

    # Sample data
    cursor.execute("INSERT OR IGNORE INTO drivers (name) VALUES ('John Smith')")
    cursor.execute("INSERT OR IGNORE INTO drivers (name) VALUES ('Sarah Davis')")
    cursor.execute("INSERT OR IGNORE INTO drivers (name) VALUES ('Mike Johnson')")

    # Sample shifts
    cursor.execute("""
        INSERT OR IGNORE INTO shifts (driver_id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate)
        VALUES (1, '2026-01-05', '10:00', '16:00', 45.0, 30.00, 25.00, 15.00, 18.50)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO shifts (driver_id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate)
        VALUES (1, '2026-01-06', '11:30', '17:30', 60.0, 25.00, 35.00, 20.00, 20.00)
    """)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    create_database()

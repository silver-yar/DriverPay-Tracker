import json
import os
import sqlite3

from PySide6.QtCore import QObject, Slot


class DBHandler(QObject):
    def __init__(self):
        super().__init__()
        db_path = os.path.join(os.path.dirname(__file__), "..", "driver_pay_tracker.db")
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    @Slot(result=str)
    def get_drivers(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM drivers")
        drivers = cursor.fetchall()
        return json.dumps([dict(row) for row in drivers])

    @Slot(str, result=str)
    def get_shifts(self, driver_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               SELECT date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate
               FROM shifts WHERE driver_id = ?
               ORDER BY date DESC
           """,
            (driver_id,),
        )
        shifts = cursor.fetchall()
        result = []
        for row in shifts:
            result.append(
                {
                    "date": row["date"],
                    "start": row["start_time"],
                    "end": row["end_time"],
                    "mileage": row["mileage"],
                    "cash": f"${row['cash_tips']:.2f}",
                    "credit": f"${row['credit_tips']:.2f}",
                    "owed": f"${row['owed']:.2f}",
                    "hourly": f"${row['hourly_rate']:.2f}",
                }
            )
        return json.dumps(result)

    @Slot(str, str, str, str, float, float, float, float, float)
    def add_shift(
        self,
        driver_id,
        date,
        start_time,
        end_time,
        mileage,
        cash_tips,
        credit_tips,
        owed,
        hourly_rate,
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               INSERT INTO shifts (driver_id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           """,
            (
                driver_id,
                date,
                start_time,
                end_time,
                mileage,
                cash_tips,
                credit_tips,
                owed,
                hourly_rate,
            ),
        )
        self.conn.commit()

    @Slot(str, result=str)
    def get_summary(self, driver_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               SELECT
                   SUM(mileage) as total_mileage,
                   SUM(cash_tips) as total_cash,
                   SUM(credit_tips) as total_credit,
                   SUM(owed) as total_owed,
                   AVG(hourly_rate) as avg_hourly
               FROM shifts WHERE driver_id = ?
           """,
            (driver_id,),
        )
        row = cursor.fetchone()
        return json.dumps(
            {
                "total_mileage": row["total_mileage"] or 0,
                "total_cash": row["total_cash"] or 0,
                "total_credit": row["total_credit"] or 0,
                "total_owed": row["total_owed"] or 0,
                "avg_hourly": row["avg_hourly"] or 0,
            }
        )

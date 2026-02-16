import json
import os
import sqlite3

from PySide6.QtCore import QObject, Slot


class DBHandler(QObject):
    def __init__(self, db_path=None):
        super().__init__()
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__), "..", "driver_pay_tracker.db"
            )
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    @Slot(result=str)
    def get_drivers(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM drivers")
        drivers = cursor.fetchall()
        return json.dumps([dict(row) for row in drivers])

    @Slot(str, str, str, result=str)
    def get_shifts(self, driver_id, start_date="", end_date=""):
        cursor = self.conn.cursor()
        query = """
           SELECT id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate
           FROM shifts WHERE driver_id = ?
        """
        params = [driver_id]
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        query += " ORDER BY date DESC"
        cursor.execute(query, params)
        shifts = cursor.fetchall()
        result = []
        for row in shifts:
            result.append(
                {
                    "id": row["id"],
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

    @Slot(str, result=str)
    def get_shift(self, shift_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               SELECT id, driver_id, date, start_time, end_time, mileage, cash_tips, credit_tips, owed, hourly_rate
               FROM shifts WHERE id = ?
           """,
            (shift_id,),
        )
        row = cursor.fetchone()
        if row:
            return json.dumps(dict(row))
        else:
            return json.dumps({})

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

    @Slot(str, str, str, str, float, float, float, float, float)
    def update_shift(
        self,
        shift_id,
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
               UPDATE shifts SET date = ?, start_time = ?, end_time = ?, mileage = ?, cash_tips = ?, credit_tips = ?, owed = ?, hourly_rate = ?
               WHERE id = ?
           """,
            (
                date,
                start_time,
                end_time,
                mileage,
                cash_tips,
                credit_tips,
                owed,
                hourly_rate,
                shift_id,
            ),
        )
        self.conn.commit()

    @Slot(str)
    def delete_shift(self, shift_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM shifts WHERE id = ?", (shift_id,))
        self.conn.commit()

    @Slot(str, str, str, result=str)
    def get_summary(self, driver_id, start_date="", end_date=""):
        cursor = self.conn.cursor()
        query = """
           SELECT
               SUM(mileage) as total_mileage,
               SUM(cash_tips) as total_cash,
               SUM(credit_tips) as total_credit,
               SUM(owed) as total_owed,
               AVG(hourly_rate) as avg_hourly
           FROM shifts WHERE driver_id = ?
        """
        params = [driver_id]
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        cursor.execute(query, params)
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

    @Slot(str, str, str, result=str)
    def get_deliveries(self, driver_id, start_date="", end_date=""):
        cursor = self.conn.cursor()
        query = """
           SELECT id, date, order_num, payment_type, order_subtotal, amount_collected, tip
           FROM deliveries WHERE driver_id = ?
        """
        params = [driver_id]
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        query += " ORDER BY date DESC"
        cursor.execute(query, params)
        deliveries = cursor.fetchall()
        result = []
        for row in deliveries:
            result.append(
                {
                    "id": row["id"],
                    "date": row["date"],
                    "order_num": row["order_num"] or "",
                    "payment_type": row["payment_type"],
                    "order_subtotal": f"${row['order_subtotal']:.2f}",
                    "amount_collected": f"${row['amount_collected']:.2f}",
                    "tip": f"${row['tip']:.2f}",
                }
            )
        return json.dumps(result)

    @Slot(str, result=str)
    def get_delivery(self, delivery_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               SELECT id, driver_id, date, order_num, payment_type, order_subtotal, amount_collected, tip
               FROM deliveries WHERE id = ?
           """,
            (delivery_id,),
        )
        row = cursor.fetchone()
        if row:
            return json.dumps(dict(row))
        else:
            return json.dumps({})

    @Slot(str, str, str, str, float, float, float)
    def add_delivery(
        self,
        driver_id,
        date,
        order_num,
        payment_type,
        order_subtotal,
        amount_collected,
        tip,
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               INSERT INTO deliveries (driver_id, date, order_num, payment_type, order_subtotal, amount_collected, tip)
               VALUES (?, ?, ?, ?, ?, ?, ?)
           """,
            (
                driver_id,
                date,
                order_num,
                payment_type,
                order_subtotal,
                amount_collected,
                tip,
            ),
        )
        self.conn.commit()

    @Slot(str, str, str, str, float, float, float)
    def update_delivery(
        self,
        delivery_id,
        date,
        order_num,
        payment_type,
        order_subtotal,
        amount_collected,
        tip,
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               UPDATE deliveries SET date = ?, order_num = ?, payment_type = ?, order_subtotal = ?, amount_collected = ?, tip = ?
               WHERE id = ?
           """,
            (
                date,
                order_num,
                payment_type,
                order_subtotal,
                amount_collected,
                tip,
                delivery_id,
            ),
        )
        self.conn.commit()

    @Slot(str)
    def delete_delivery(self, delivery_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM deliveries WHERE id = ?", (delivery_id,))
        self.conn.commit()

    @Slot(str, str, str, result=str)
    def get_deliveries_summary(self, driver_id, start_date="", end_date=""):
        cursor = self.conn.cursor()
        query = """
           SELECT
               SUM(order_subtotal) as total_subtotal,
               SUM(amount_collected) as total_collected,
               SUM(tip) as total_tips,
               COUNT(*) as delivery_count
           FROM deliveries WHERE driver_id = ?
        """
        params = [driver_id]
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        cursor.execute(query, params)
        row = cursor.fetchone()
        return json.dumps(
            {
                "total_subtotal": row["total_subtotal"] or 0,
                "total_collected": row["total_collected"] or 0,
                "total_tips": row["total_tips"] or 0,
                "delivery_count": row["delivery_count"] or 0,
            }
        )

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
        self._ensure_delivery_mileage_column()

    def _ensure_delivery_mileage_column(self):
        """Ensure legacy databases include the deliveries.mileage column."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='deliveries'"
        )
        if cursor.fetchone() is None:
            return

        cursor.execute("PRAGMA table_info(deliveries)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "mileage" not in columns:
            cursor.execute("ALTER TABLE deliveries ADD COLUMN mileage REAL DEFAULT 0.0")
            self.conn.commit()

    @Slot(result=str)
    def get_drivers(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM drivers")
        drivers = cursor.fetchall()
        return json.dumps([dict(row) for row in drivers])

    @Slot(str, result=str)
    def add_driver(self, name):
        clean_name = (name or "").strip()
        if not clean_name:
            return json.dumps(
                {"success": False, "error": "Driver name cannot be empty."}
            )

        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO drivers (name) VALUES (?)", (clean_name,))
            self.conn.commit()
            return json.dumps(
                {"success": True, "driver_id": cursor.lastrowid, "name": clean_name}
            )
        except sqlite3.IntegrityError:
            return json.dumps({"success": False, "error": "Driver already exists."})

    @Slot(str, result=str)
    def delete_driver(self, name):
        clean_name = (name or "").strip()
        if not clean_name:
            return json.dumps(
                {"success": False, "error": "Driver name cannot be empty."}
            )

        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM drivers WHERE name = ?", (clean_name,))
        row = cursor.fetchone()
        if not row:
            return json.dumps({"success": False, "error": "Driver not found."})

        driver_id = row["id"]
        cursor.execute("DELETE FROM deliveries WHERE driver_id = ?", (driver_id,))
        cursor.execute("DELETE FROM shifts WHERE driver_id = ?", (driver_id,))
        cursor.execute("DELETE FROM drivers WHERE id = ?", (driver_id,))
        self.conn.commit()
        return json.dumps({"success": True, "driver_id": driver_id})

    @Slot(str, str, str, result=str)
    def get_shifts(self, driver_id, start_date="", end_date=""):
        self._sync_shift_totals(driver_id=driver_id)
        cursor = self.conn.cursor()
        query = """
           SELECT s.id, s.date, s.start_time, s.end_time, s.starting_mileage, s.ending_mileage, s.mileage, s.owed, s.mileage_rate,
                  s.cash_tips, s.credit_tips
           FROM shifts s
           WHERE s.driver_id = ?
        """
        params = [driver_id]
        if start_date and end_date:
            query += " AND s.date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        query += " ORDER BY s.date DESC"
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
                    "starting_mileage": row["starting_mileage"],
                    "ending_mileage": row["ending_mileage"],
                    "mileage": row["mileage"],
                    "cash": f"${row['cash_tips']:.2f}",
                    "credit": f"${row['credit_tips']:.2f}",
                    "owed": f"${row['owed']:.2f}",
                    "mileage_rate": f"${row['mileage_rate']:.2f}",
                }
            )
        return json.dumps(result)

    @Slot(str, result=str)
    def get_shift(self, shift_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               SELECT id, driver_id, date, start_time, end_time, starting_mileage, ending_mileage, mileage, cash_tips, credit_tips, owed, mileage_rate
               FROM shifts WHERE id = ?
           """,
            (shift_id,),
        )
        row = cursor.fetchone()
        if row:
            return json.dumps(dict(row))
        else:
            return json.dumps({})

    @Slot(str, str, str, str, float, float, float, float, float, float)
    def add_shift(
        self,
        driver_id,
        date,
        start_time,
        end_time,
        starting_mileage,
        ending_mileage,
        cash_tips,
        credit_tips,
        owed,
        mileage_rate,
    ):
        # Calculate total mileage
        mileage = ending_mileage - starting_mileage
        cursor = self.conn.cursor()
        cursor.execute(
            """
               INSERT INTO shifts (driver_id, date, start_time, end_time, starting_mileage, ending_mileage, mileage, cash_tips, credit_tips, owed, mileage_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           """,
            (
                driver_id,
                date,
                start_time,
                end_time,
                starting_mileage,
                ending_mileage,
                mileage,
                cash_tips,
                credit_tips,
                owed,
                mileage_rate,
            ),
        )
        self.conn.commit()

    @Slot(str, str, str, str, float, float, float, float, float, float)
    def update_shift(
        self,
        shift_id,
        date,
        start_time,
        end_time,
        starting_mileage,
        ending_mileage,
        cash_tips,
        credit_tips,
        owed,
        mileage_rate,
    ):
        # Calculate total mileage
        mileage = ending_mileage - starting_mileage
        cursor = self.conn.cursor()
        cursor.execute(
            """
               UPDATE shifts SET date = ?, start_time = ?, end_time = ?, starting_mileage = ?, ending_mileage = ?, mileage = ?, cash_tips = ?, credit_tips = ?, owed = ?, mileage_rate = ?
               WHERE id = ?
           """,
            (
                date,
                start_time,
                end_time,
                starting_mileage,
                ending_mileage,
                mileage,
                cash_tips,
                credit_tips,
                owed,
                mileage_rate,
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
        self._sync_shift_totals(driver_id=driver_id)
        cursor = self.conn.cursor()
        query = """
           SELECT
               SUM(mileage) as total_mileage,
               SUM(cash_tips) as total_cash,
               SUM(credit_tips) as total_credit,
               SUM(owed) as total_owed,
               AVG(mileage_rate) as avg_mileage_rate
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
                "avg_mileage_rate": row["avg_mileage_rate"] or 0,
            }
        )

    @Slot(str, str, str, result=str)
    def get_deliveries(self, driver_id, start_date="", end_date=""):
        cursor = self.conn.cursor()
        query = """
           SELECT id, driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage
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
                    "driver_id": row["driver_id"],
                    "shift_id": row["shift_id"],
                    "date": row["date"],
                    "order_num": row["order_num"] or "",
                    "payment_type": row["payment_type"],
                    "order_subtotal": f"${row['order_subtotal']:.2f}",
                    "amount_collected": f"${row['amount_collected']:.2f}",
                    "card_tip": f"${row['card_tip']:.2f}",
                    "cash_tip": row["cash_tip"] or 0,
                    "mileage": row["mileage"] or 0,
                }
            )
        return json.dumps(result)

    @Slot(str, result=str)
    def get_delivery(self, delivery_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
               SELECT id, driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage
               FROM deliveries WHERE id = ?
           """,
            (delivery_id,),
        )
        row = cursor.fetchone()
        if row:
            return json.dumps(dict(row))
        else:
            return json.dumps({})

    def _validate_delivery_amounts(self, order_subtotal, amount_collected, mileage):
        """Validate delivery amounts and mileage."""
        errors = []

        # Check for non-negative values
        if order_subtotal < 0:
            errors.append("Order subtotal cannot be negative.")
        if amount_collected < 0:
            errors.append("Amount collected cannot be negative.")

        # Check that amount collected is not less than subtotal
        if amount_collected < order_subtotal:
            errors.append("Amount collected cannot be less than order subtotal.")
        if mileage < 0:
            errors.append("Mileage cannot be negative.")

        # Check for maximum 2 decimal places
        def has_more_than_2_decimals(value):
            str_value = str(value)
            if "." in str_value:
                decimals = len(str_value.split(".")[1])
                return decimals > 2
            return False

        if has_more_than_2_decimals(order_subtotal):
            errors.append("Order subtotal cannot have more than 2 decimal places.")
        if has_more_than_2_decimals(amount_collected):
            errors.append("Amount collected cannot have more than 2 decimal places.")
        if has_more_than_2_decimals(mileage):
            errors.append("Mileage cannot have more than 2 decimal places.")

        return errors

    @Slot(str, str, str, str, str, float, float, float, float, float, result=str)
    def add_delivery(
        self,
        driver_id,
        shift_id,
        date,
        order_num,
        payment_type,
        order_subtotal,
        amount_collected,
        card_tip,
        cash_tip=0,
        mileage=0,
    ):
        # Validate inputs
        errors = self._validate_delivery_amounts(order_subtotal, amount_collected, mileage)
        if errors:
            return json.dumps({"success": False, "errors": errors})

        cursor = self.conn.cursor()
        cursor.execute(
            """
               INSERT INTO deliveries (driver_id, shift_id, date, order_num, payment_type, order_subtotal, amount_collected, card_tip, cash_tip, mileage)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           """,
            (
                driver_id,
                shift_id if shift_id else None,
                date,
                order_num,
                payment_type,
                order_subtotal,
                amount_collected,
                card_tip,
                cash_tip,
                mileage,
            ),
        )
        self.conn.commit()

        # Update shift tip totals if shift_id is provided
        if shift_id:
            self._update_shift_tip_totals(shift_id)

        return json.dumps({"success": True})

    @Slot(str, str, str, str, str, float, float, float, float, float, result=str)
    def update_delivery(
        self,
        delivery_id,
        shift_id,
        date,
        order_num,
        payment_type,
        order_subtotal,
        amount_collected,
        card_tip,
        cash_tip=0,
        mileage=0,
    ):
        # Validate inputs
        errors = self._validate_delivery_amounts(order_subtotal, amount_collected, mileage)
        if errors:
            return json.dumps({"success": False, "errors": errors})

        # Get current shift_id before update
        cursor = self.conn.cursor()
        cursor.execute("SELECT shift_id FROM deliveries WHERE id = ?", (delivery_id,))
        row = cursor.fetchone()
        old_shift_id = row["shift_id"] if row else None

        cursor.execute(
            """
               UPDATE deliveries SET shift_id = ?, date = ?, order_num = ?, payment_type = ?, order_subtotal = ?, amount_collected = ?, card_tip = ?, cash_tip = ?, mileage = ?
               WHERE id = ?
           """,
            (
                shift_id if shift_id else None,
                date,
                order_num,
                payment_type,
                order_subtotal,
                amount_collected,
                card_tip,
                cash_tip,
                mileage,
                delivery_id,
            ),
        )
        self.conn.commit()

        # Update tip totals for both old and new shift if they differ
        if old_shift_id and old_shift_id != shift_id:
            self._update_shift_tip_totals(old_shift_id)
        if shift_id:
            self._update_shift_tip_totals(shift_id)

        return json.dumps({"success": True})

    @Slot(str)
    def delete_delivery(self, delivery_id):
        # Get shift_id before deletion
        cursor = self.conn.cursor()
        cursor.execute("SELECT shift_id FROM deliveries WHERE id = ?", (delivery_id,))
        row = cursor.fetchone()
        shift_id = row["shift_id"] if row else None

        cursor.execute("DELETE FROM deliveries WHERE id = ?", (delivery_id,))
        self.conn.commit()

        # Update shift tip totals if delivery was linked to a shift
        if shift_id:
            self._update_shift_tip_totals(shift_id)

    def _update_shift_tip_totals(self, shift_id):
        """Synchronize tip totals and owed on a shift from its deliveries."""
        self._sync_shift_totals(shift_id=shift_id)

    def _sync_shift_totals(self, driver_id=None, shift_id=None):
        """Keep shift cash/credit/owed directly linked to delivery records."""
        cursor = self.conn.cursor()
        query = """
            UPDATE shifts
            SET
                credit_tips = COALESCE(
                    (SELECT SUM(card_tip) FROM deliveries WHERE shift_id = shifts.id), 0
                ),
                cash_tips = COALESCE(
                    (SELECT SUM(cash_tip) FROM deliveries WHERE shift_id = shifts.id), 0
                ),
                mileage = COALESCE(
                    (SELECT SUM(mileage) FROM deliveries WHERE shift_id = shifts.id), 0
                ),
                owed = COALESCE(
                    (SELECT SUM(card_tip) FROM deliveries WHERE shift_id = shifts.id), 0
                ) + COALESCE(
                    (SELECT SUM(cash_tip) FROM deliveries WHERE shift_id = shifts.id), 0
                ) - COALESCE(
                    (
                        SELECT SUM(
                            CASE WHEN payment_type = 'Cash' THEN amount_collected ELSE 0 END
                        )
                        FROM deliveries
                        WHERE shift_id = shifts.id
                    ),
                    0
                )
        """
        params = []
        if shift_id is not None:
            query += " WHERE id = ?"
            params.append(shift_id)
        elif driver_id is not None:
            query += " WHERE driver_id = ?"
            params.append(driver_id)

        cursor.execute(query, params)
        self.conn.commit()

    @Slot(str, str, str, result=str)
    def get_deliveries_summary(self, driver_id, start_date="", end_date=""):
        cursor = self.conn.cursor()
        query = """
           SELECT
               SUM(order_subtotal) as total_subtotal,
               SUM(amount_collected) as total_collected,
               SUM(card_tip) as total_tips,
               SUM(cash_tip) as total_cash_tips,
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
                "total_cash_tips": row["total_cash_tips"] or 0,
                "delivery_count": row["delivery_count"] or 0,
            }
        )

    @Slot(str, str, result=str)
    def get_shifts_for_dropdown(self, driver_id, date=""):
        """Get shifts for dropdown selection in delivery modal."""
        cursor = self.conn.cursor()
        query = """
               SELECT id, date, start_time, end_time
               FROM shifts WHERE driver_id = ?
           """
        params = [driver_id]
        if date:
            query += " AND date = ?"
            params.append(date)
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
                }
            )
        return json.dumps(result)

    @Slot(result=str)
    def get_settings(self):
        """Get application settings."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT default_mileage_rate FROM settings WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return json.dumps({"default_mileage_rate": row["default_mileage_rate"]})
        return json.dumps({"default_mileage_rate": 0.65})

    @Slot(float)
    def update_settings(self, default_mileage_rate):
        """Update application settings."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE settings SET default_mileage_rate = ? WHERE id = 1",
            (default_mileage_rate,),
        )
        self.conn.commit()

"""
database.py
Enhanced database and business logic engine for Asset Tracker.
Uses SQLite for robust, ACID-compliant local storage.
Enforces real-world enterprise constraints:
- 1 active loan per student policy (configurable)
- Asset availability state checks (available, borrowed, maintenance, retired)
- Overdue tracking and auto-flagging
- Comprehensive Admin CRUD operations and audit logging
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent / "lendtrack.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and default settings. Safe to call on startup."""
    conn = get_connection()
    cur = conn.cursor()

    # Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            enrollment_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            contact TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Laptops table (without location and notes)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS laptops (
            laptop_id TEXT PRIMARY KEY,
            brand TEXT NOT NULL DEFAULT 'Generic',
            model TEXT NOT NULL,
            serial_no TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'available'
                CHECK (status IN ('available', 'borrowed', 'maintenance', 'retired')),
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Transactions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            laptop_id TEXT NOT NULL,
            enrollment_no TEXT NOT NULL,
            action TEXT NOT NULL CHECK (action IN ('borrow', 'return')),
            timestamp TEXT DEFAULT (datetime('now', 'localtime')),
            expected_return TEXT,
            return_timestamp TEXT,
            status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'active', 'overdue', 'cancelled')),
            admin_override INTEGER DEFAULT 0,
            FOREIGN KEY (laptop_id) REFERENCES laptops(laptop_id) ON UPDATE CASCADE,
            FOREIGN KEY (enrollment_no) REFERENCES students(enrollment_no) ON UPDATE CASCADE
        )
    """)

    # System settings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Auto-migrate columns if tables existed with older schemas
    def add_col_if_missing(table, col_def, col_name):
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        except sqlite3.OperationalError:
            pass  # Column already exists

    add_col_if_missing("students", "email TEXT", "email")
    add_col_if_missing("students", "department TEXT DEFAULT 'General'", "department")
    add_col_if_missing("students", "contact TEXT", "contact")
    add_col_if_missing("students", "status TEXT NOT NULL DEFAULT 'active'", "status")

    add_col_if_missing("laptops", "brand TEXT DEFAULT 'Generic'", "brand")
    add_col_if_missing("laptops", "serial_no TEXT DEFAULT ''", "serial_no")
    add_col_if_missing("laptops", "status TEXT NOT NULL DEFAULT 'available'", "status")

    add_col_if_missing("transactions", "expected_return TEXT", "expected_return")
    add_col_if_missing("transactions", "return_timestamp TEXT", "return_timestamp")
    add_col_if_missing("transactions", "status TEXT NOT NULL DEFAULT 'completed'", "status")
    add_col_if_missing("transactions", "admin_override INTEGER DEFAULT 0", "admin_override")

    # Insert default settings if missing
    defaults = {
        "institution_name": "Asset Tracker System",
        "overdue_hours": "8",
        "max_laptops_per_student": "1",
        "admin_pin": "admin123",
        "auto_flag_overdue": "1"
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()


# ---------------- System Settings Operations ----------------

def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_all_settings() -> Dict[str, str]:
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


# ---------------- Business Logic & Validation ----------------

class TransactionError(Exception):
    """Raised when an operation violates a business rule."""
    pass


def get_student(enrollment_no: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE enrollment_no = ?", (enrollment_no.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_laptop(laptop_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM laptops WHERE laptop_id = ?", (laptop_id.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_loan_for_student(enrollment_no: str) -> Optional[Dict[str, Any]]:
    """Returns details of any laptop currently borrowed by this student."""
    conn = get_connection()
    row = conn.execute("""
        SELECT l.laptop_id, l.brand, l.model, t.timestamp AS borrowed_since, t.id AS transaction_id
        FROM laptops l
        JOIN transactions t ON t.laptop_id = l.laptop_id
        WHERE l.status = 'borrowed'
          AND t.enrollment_no = ?
          AND t.action = 'borrow'
          AND t.id = (SELECT MAX(t2.id) FROM transactions t2 WHERE t2.laptop_id = l.laptop_id)
    """, (enrollment_no.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_current_borrower(laptop_id: str) -> Optional[Dict[str, Any]]:
    """Returns the student who currently holds this laptop."""
    conn = get_connection()
    row = conn.execute("""
        SELECT s.enrollment_no, s.name, s.department, s.email, t.timestamp AS borrowed_since, t.id AS transaction_id
        FROM transactions t
        JOIN students s ON s.enrollment_no = t.enrollment_no
        WHERE t.laptop_id = ?
          AND t.action = 'borrow'
          AND t.id = (SELECT MAX(t2.id) FROM transactions t2 WHERE t2.laptop_id = ?)
    """, (laptop_id.strip(), laptop_id.strip())).fetchone()
    conn.close()
    return dict(row) if row else None


def record_transaction(laptop_id: str, enrollment_no: str, action: str, admin_override: bool = False) -> Dict[str, Any]:
    """
    Executes a borrow or return transaction enforcing strict business rules:
    1. Student must exist and be 'active' (not suspended).
    2. Laptop must exist.
    3. On Borrow:
       - Laptop must be 'available' (not borrowed, maintenance, or retired).
       - Student must not already have an active loan (unless admin_override is True).
    4. On Return:
       - Laptop must currently be 'borrowed'.
    """
    laptop_id = laptop_id.strip()
    enrollment_no = enrollment_no.strip()
    action = action.strip().lower()

    if action not in ("borrow", "return"):
        raise TransactionError(f"Invalid transaction action: '{action}'. Must be 'borrow' or 'return'.")

    conn = get_connection()
    cur = conn.cursor()

    # 1. Check Student
    student = cur.execute("SELECT * FROM students WHERE enrollment_no = ?", (enrollment_no,)).fetchone()
    if not student:
        conn.close()
        raise TransactionError(f"Student ID '{enrollment_no}' not found in database. Please register student first.")
    
    if student["status"] == "suspended" and not admin_override:
        conn.close()
        raise TransactionError(f"Student '{student['name']}' ({enrollment_no}) is currently SUSPENDED from borrowing.")

    # 2. Check Laptop
    laptop = cur.execute("SELECT * FROM laptops WHERE laptop_id = ?", (laptop_id,)).fetchone()
    if not laptop:
        conn.close()
        raise TransactionError(f"Laptop ID '{laptop_id}' is not registered in system.")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Process Borrow
    if action == "borrow":
        if laptop["status"] == "borrowed":
            current_holder = get_current_borrower(laptop_id)
            holder_name = current_holder["name"] if current_holder else "another student"
            conn.close()
            raise TransactionError(f"Laptop {laptop_id} is already checked out to {holder_name}.")

        if laptop["status"] == "maintenance":
            conn.close()
            raise TransactionError(f"Laptop {laptop_id} is currently under MAINTENANCE and cannot be borrowed.")

        if laptop["status"] == "retired":
            conn.close()
            raise TransactionError(f"Laptop {laptop_id} is RETIRED from fleet.")

        # Check existing loan limit
        active_loan = get_active_loan_for_student(enrollment_no)
        if active_loan and not admin_override:
            conn.close()
            raise TransactionError(
                f"Student {student['name']} already has laptop {active_loan['laptop_id']} ({active_loan['model']}) "
                f"checked out since {active_loan['borrowed_since']}."
            )

        # Calculate expected return time based on setting
        overdue_hrs = int(get_setting("overdue_hours", "8"))
        expected_return = (datetime.now() + timedelta(hours=overdue_hrs)).strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("UPDATE laptops SET status = 'borrowed' WHERE laptop_id = ?", (laptop_id,))
        cur.execute("""
            INSERT INTO transactions (laptop_id, enrollment_no, action, timestamp, expected_return, status, admin_override)
            VALUES (?, ?, 'borrow', ?, ?, 'active', ?)
        """, (laptop_id, enrollment_no, now_str, expected_return, 1 if admin_override else 0))

    # 4. Process Return
    elif action == "return":
        if laptop["status"] != "borrowed":
            conn.close()
            raise TransactionError(f"Laptop {laptop_id} is currently marked as '{laptop['status']}', not borrowed.")

        # Check who borrowed it
        current_holder = get_current_borrower(laptop_id)
        if current_holder and current_holder["enrollment_no"] != enrollment_no and not admin_override:
            conn.close()
            raise TransactionError(
                f"Borrower Mismatch! Laptop {laptop_id} was borrowed by '{current_holder['name']}' ({current_holder['enrollment_no']}), "
                f"not '{student['name']}' ({enrollment_no}). Only the authorized borrower or admin can return this laptop."
            )

        cur.execute("UPDATE laptops SET status = 'available' WHERE laptop_id = ?", (laptop_id,))
        cur.execute("""
            INSERT INTO transactions (laptop_id, enrollment_no, action, timestamp, return_timestamp, status, admin_override)
            VALUES (?, ?, 'return', ?, ?, 'completed', ?)
        """, (laptop_id, enrollment_no, now_str, now_str, 1 if admin_override else 0))

        # Close the active borrow transaction status
        cur.execute("""
            UPDATE transactions
            SET status = 'completed', return_timestamp = ?
            WHERE laptop_id = ? AND action = 'borrow' AND status IN ('active', 'overdue')
        """, (now_str, laptop_id))

    conn.commit()
    conn.close()

    return {
        "laptop_id": laptop_id,
        "laptop_model": f"{laptop['brand']} {laptop['model']}",
        "enrollment_no": enrollment_no,
        "student_name": student["name"],
        "action": action,
        "timestamp": now_str
    }


# ---------------- Queries & Fleet Status ----------------

def currently_borrowed_list() -> List[Dict[str, Any]]:
    """Returns all currently borrowed laptops with borrower details, duration, and overdue flag."""
    conn = get_connection()
    overdue_hours = float(get_setting("overdue_hours", "8"))
    now = datetime.now()

    rows = conn.execute("""
        SELECT 
            l.laptop_id, l.brand, l.model,
            s.enrollment_no, s.name AS student_name, s.department, s.email, s.contact,
            t.timestamp AS borrowed_at, t.expected_return, t.id AS transaction_id
        FROM laptops l
        JOIN transactions t ON t.laptop_id = l.laptop_id
        JOIN students s ON s.enrollment_no = t.enrollment_no
        WHERE l.status = 'borrowed'
          AND t.id = (SELECT MAX(id) FROM transactions t2 WHERE t2.laptop_id = l.laptop_id)
        ORDER BY t.timestamp ASC
    """).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        borrowed_time = datetime.strptime(d["borrowed_at"], "%Y-%m-%d %H:%M:%S")
        elapsed_delta = now - borrowed_time
        elapsed_hours = elapsed_delta.total_seconds() / 3600.0
        
        is_overdue = elapsed_hours > overdue_hours
        d["elapsed_hours"] = round(elapsed_hours, 1)
        d["is_overdue"] = is_overdue
        d["hours_overdue"] = round(elapsed_hours - overdue_hours, 1) if is_overdue else 0.0

        # Formatted readable duration
        hours = int(elapsed_delta.total_seconds() // 3600)
        minutes = int((elapsed_delta.total_seconds() % 3600) // 60)
        d["duration_str"] = f"{hours}h {minutes}m"
        results.append(d)

    return results


def get_fleet_summary() -> Dict[str, Any]:
    """Returns quick inventory KPIs."""
    conn = get_connection()
    total_laptops = conn.execute("SELECT COUNT(*) FROM laptops").fetchone()[0]
    available_laptops = conn.execute("SELECT COUNT(*) FROM laptops WHERE status = 'available'").fetchone()[0]
    borrowed_laptops = conn.execute("SELECT COUNT(*) FROM laptops WHERE status = 'borrowed'").fetchone()[0]
    maintenance_laptops = conn.execute("SELECT COUNT(*) FROM laptops WHERE status = 'maintenance'").fetchone()[0]
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    
    # Count today's transactions
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_txs = conn.execute("SELECT COUNT(*) FROM transactions WHERE timestamp LIKE ?", (f"{today_str}%",)).fetchone()[0]
    
    conn.close()

    borrowed_items = currently_borrowed_list()
    overdue_count = sum(1 for item in borrowed_items if item["is_overdue"])

    return {
        "total_laptops": total_laptops,
        "available_laptops": available_laptops,
        "borrowed_laptops": borrowed_laptops,
        "maintenance_laptops": maintenance_laptops,
        "total_students": total_students,
        "today_transactions": today_txs,
        "overdue_count": overdue_count
    }


# ---------------- Admin CRUD Operations ----------------

def add_student(enrollment_no: str, name: str, email: str, department: str, contact: str, status: str = "active") -> bool:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO students (enrollment_no, name, email, department, contact, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (enrollment_no.strip(), name.strip(), email.strip(), department.strip(), contact.strip(), status))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_student(enrollment_no: str, name: str, email: str, department: str, contact: str, status: str):
    conn = get_connection()
    conn.execute("""
        UPDATE students
        SET name = ?, email = ?, department = ?, contact = ?, status = ?
        WHERE enrollment_no = ?
    """, (name.strip(), email.strip(), department.strip(), contact.strip(), status, enrollment_no.strip()))
    conn.commit()
    conn.close()


def delete_student(enrollment_no: str):
    """Deletes student if they have no active loan."""
    active_loan = get_active_loan_for_student(enrollment_no)
    if active_loan:
        raise TransactionError(f"Cannot delete student {enrollment_no} while they currently hold laptop {active_loan['laptop_id']}.")
    
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE enrollment_no = ?", (enrollment_no.strip(),))
    conn.execute("DELETE FROM students WHERE enrollment_no = ?", (enrollment_no.strip(),))
    conn.commit()
    conn.close()


def add_laptop(laptop_id: str, brand: str, model: str, serial_no: str = "", status: str = "available") -> bool:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO laptops (laptop_id, brand, model, serial_no, status)
            VALUES (?, ?, ?, ?, ?)
        """, (laptop_id.strip(), brand.strip(), model.strip(), serial_no.strip(), status))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_laptop(laptop_id: str, brand: str, model: str, serial_no: str, status: str):
    conn = get_connection()
    conn.execute("""
        UPDATE laptops
        SET brand = ?, model = ?, serial_no = ?, status = ?
        WHERE laptop_id = ?
    """, (brand.strip(), model.strip(), serial_no.strip(), status, laptop_id.strip()))
    conn.commit()
    conn.close()


def delete_laptop(laptop_id: str):
    """Deletes laptop if not currently borrowed."""
    laptop = get_laptop(laptop_id)
    if laptop and laptop["status"] == "borrowed":
        raise TransactionError(f"Cannot delete laptop {laptop_id} while it is currently checked out to a student.")

    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE laptop_id = ?", (laptop_id.strip(),))
    conn.execute("DELETE FROM laptops WHERE laptop_id = ?", (laptop_id.strip(),))
    conn.commit()
    conn.close()


def delete_transaction(transaction_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


def get_all_students() -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY enrollment_no ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_laptops() -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT laptop_id, brand, model, serial_no, status, created_at FROM laptops ORDER BY laptop_id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_transactions(limit: int = 500) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(f"""
        SELECT 
            t.id, t.laptop_id, l.brand, l.model AS laptop_model,
            t.enrollment_no, s.name AS student_name, s.department,
            t.action, t.timestamp, t.return_timestamp, t.status, t.admin_override
        FROM transactions t
        LEFT JOIN laptops l ON l.laptop_id = t.laptop_id
        LEFT JOIN students s ON s.enrollment_no = t.enrollment_no
        ORDER BY t.id DESC
        LIMIT {limit}
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- Demo Data Seeder ----------------

def seed_demo_data():
    """Populates realistic starter data for quick demonstration and testing."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    demo_students = [
        ("STU-2024-001", "Muhammad Hamza", "hamza@pmsyd.edu.pk", "Artificial Intelligence", "+92 300 1234567", "active"),
        ("STU-2024-002", "Ayesha Khan", "ayesha.k@pmsyd.edu.pk", "Data Science", "+92 301 2345678", "active"),
        ("STU-2024-003", "Bilal Ahmed", "bilal.ahmed@pmsyd.edu.pk", "Software Engineering", "+92 302 3456789", "active"),
        ("STU-2024-004", "Fatima Noor", "fatima.noor@pmsyd.edu.pk", "Cyber Security", "+92 303 4567890", "active"),
        ("STU-2024-005", "Zain Ali", "zain.ali@pmsyd.edu.pk", "Cloud Computing", "+92 304 5678901", "active"),
        ("STU-2024-006", "Sara Tariq", "sara.t@pmsyd.edu.pk", "Artificial Intelligence", "+92 305 6789012", "active"),
    ]

    for s in demo_students:
        cur.execute("""
            INSERT OR IGNORE INTO students (enrollment_no, name, email, department, contact, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, s)

    demo_laptops = [
        ("LAP-001", "Dell", "Latitude 5420 (i7, 16GB)", "SN-DL-5420-01", "available"),
        ("LAP-002", "Dell", "Latitude 5430 (i5, 16GB)", "SN-DL-5430-02", "available"),
        ("LAP-003", "HP", "EliteBook 840 G8 (i7, 32GB)", "SN-HP-840-03", "available"),
        ("LAP-004", "Lenovo", "ThinkPad T14 Gen 3 (Ryzen 7)", "SN-LN-T14-04", "available"),
        ("LAP-005", "Apple", "MacBook Pro 14 (M2 Pro, 16GB)", "SN-AP-MBP-05", "available"),
        ("LAP-006", "Asus", "ExpertBook B9 (i7, 16GB)", "SN-AS-B9-06", "maintenance"),
    ]

    for l in demo_laptops:
        cur.execute("""
            INSERT OR IGNORE INTO laptops (laptop_id, brand, model, serial_no, status)
            VALUES (?, ?, ?, ?, ?)
        """, l)

    conn.commit()
    conn.close()


def reset_database():
    """Wipes all data and re-initializes fresh empty schema."""
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute("DROP TABLE IF EXISTS laptops")
    conn.execute("DROP TABLE IF EXISTS students")
    conn.execute("DROP TABLE IF EXISTS settings")
    conn.commit()
    conn.close()
    init_db()


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print(f"Database initialized and seeded successfully at {DB_PATH}")
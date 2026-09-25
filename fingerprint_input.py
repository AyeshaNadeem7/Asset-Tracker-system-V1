"""
fingerprint_input.py
Handles student biometric identification for Asset Tracker.
Supports:
1. HID Keyboard Emulation Mode (standard USB fingerprint scanners like ZKTeco, Mantra, DigitalPersona).
2. Direct terminal/kiosk input with retry handling and auto-whitespace trimming.
3. Verification against student database.
"""

from typing import Optional
import database as db


def get_student_id_from_fingerprint(
    prompt: str = "👆 Place finger on biometric scanner (or enter Enrollment ID): ",
    max_retries: int = 3
) -> Optional[str]:
    """
    Captures biometric ID string with retry loops and validation.
    """
    retries = 0
    while retries < max_retries:
        enrollment_no = input(prompt).strip()
        if not enrollment_no:
            print("⚠️ No input received. Please try again.")
            retries += 1
            continue

        student = db.get_student(enrollment_no)
        if not student:
            print(f"❌ Student ID '{enrollment_no}' not found in registry. Retry ({retries + 1}/{max_retries})...")
            retries += 1
            continue

        if student.get("status") == "suspended":
            print(f"⛔ Student '{student['name']}' ({enrollment_no}) is SUSPENDED. Access denied.")
            return None

        print(f"✅ Biometric Match: {student['name']} ({student['department']})")
        return enrollment_no

    print("❌ Identification timed out or maximum retries exceeded.")
    return None


if __name__ == "__main__":
    db.init_db()
    eid = get_student_id_from_fingerprint()
    if eid:
        print(f"Verified Enrollment No: {eid}")
"""
main.py
CLI Checkpoint Dispatcher for Asset Tracker.
Operates at physical check-in / check-out desks.
"""

import time
import database as db
from scan_qr import scan_qr_from_webcam
from fingerprint_input import get_student_id_from_fingerprint


def print_banner():
    print("=" * 65)
    print("      💻 ASSET TRACKER — HARDWARE CHECKPOINT DISPATCHER")
    print("=" * 65)


def run_kiosk_cycle():
    db.init_db()
    print_banner()

    print("\nSelect Mode:")
    print("1. [Auto-Detect] Smart Borrow / Return (Scans laptop first)")
    print("2. [Manual] Borrow Laptop")
    print("3. [Manual] Return Laptop")
    print("4. [Exit]")

    choice = input("\nEnter choice (1-4) [default: 1]: ").strip() or "1"
    if choice == "4":
        return False

    print("\n--- STEP 1: SCAN LAPTOP QR CODE ---")
    laptop_id = scan_qr_from_webcam()
    if not laptop_id:
        # Fallback to manual entry if camera not present or cancelled
        laptop_id = input("Enter Laptop ID manually (or press Enter to cancel): ").strip()
        if not laptop_id:
            print("❌ Cancelled.")
            return True

    laptop = db.get_laptop(laptop_id)
    if not laptop:
        print(f"❌ Unknown laptop ID: '{laptop_id}'. Register asset first in Admin portal.")
        return True

    print(f"✅ Laptop Identified: {laptop['laptop_id']} — {laptop['brand']} {laptop['model']} (Status: {laptop['status'].upper()})")

    # Determine Action
    if choice == "1":
        action = "return" if laptop["status"] == "borrowed" else "borrow"
        print(f"💡 Auto-selected Action: {action.upper()}")
    elif choice == "2":
        action = "borrow"
    else:
        action = "return"

    print("\n--- STEP 2: BIOMETRIC IDENTIFICATION ---")
    enrollment_no = get_student_id_from_fingerprint()
    if not enrollment_no:
        print("❌ Biometric match failed. Transaction aborted.")
        return True

    # Complete Transaction
    print("\n--- PROCESSING TRANSACTION ---")
    try:
        res = db.record_transaction(laptop_id, enrollment_no, action)
        print("\n" + "*" * 60)
        print(f"🎉 SUCCESS: Laptop {res['laptop_id']} successfully {res['action'].upper()}ED!")
        print(f"   Student : {res['student_name']} ({res['enrollment_no']})")
        print(f"   Asset   : {res['laptop_model']}")
        print(f"   Time    : {res['timestamp']}")
        print("*" * 60)
    except db.TransactionError as err:
        print(f"\n⛔ TRANSACTION REJECTED: {err}")

    time.sleep(2)
    return True


def main():
    while True:
        try:
            continue_running = run_kiosk_cycle()
            if not continue_running:
                print("\nGoodbye!")
                break
            input("\nPress [ENTER] to process next student...")
        except KeyboardInterrupt:
            print("\nShutting down checkpoint.")
            break


if __name__ == "__main__":
    main()
"""
scan_qr.py
High-speed classical Computer Vision QR & Barcode scanner for Asset Tracker.
Uses pyzbar + OpenCV VideoCapture to capture and decode frames directly from the webcam.
Handles GUI and headless environments safely without crashing on imshow/destroyAllWindows.
"""

import cv2
from pyzbar.pyzbar import decode
from typing import Optional


def decode_qr_from_frame(frame) -> Optional[str]:
    """Decodes QR code from an OpenCV frame (numpy array)."""
    if frame is None:
        return None
    try:
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            data = obj.data.decode("utf-8").strip()
            if data:
                return data
    except Exception:
        pass
    return None


def scan_qr_from_webcam(camera_index: int = 0, timeout_seconds: int = 20) -> Optional[str]:
    """
    Opens the laptop webcam, reads frames, decodes QR code with pyzbar,
    and returns scanned string as soon as a QR code is detected.
    Safe against headless OpenCV environments.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    if fps <= 0:
        fps = 30
    max_frames = int(timeout_seconds * fps)
    frames_checked = 0
    result = None

    try:
        while frames_checked < max_frames:
            ok, frame = cap.read()
            if not ok or frame is None:
                frames_checked += 1
                continue

            # Decode QR code from frame
            decoded_text = decode_qr_from_frame(frame)
            if decoded_text:
                result = decoded_text
                break

            # Safely attempt GUI display if supported, else continue silently
            try:
                cv2.imshow("Scan Laptop QR Code (Hold QR in front of camera)", frame)
                if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                    break
            except Exception:
                pass  # Ignore highgui GUI exceptions in headless builds

            frames_checked += 1
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    return result


if __name__ == "__main__":
    print("Point laptop QR code at webcam...")
    code = scan_qr_from_webcam()
    if code:
        print(f"Scanned: {code}")
    else:
        print("No QR code detected.")
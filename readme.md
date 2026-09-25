# ⚡ Asset Tracker — Enterprise Laptop Lending & Asset Management System

**Asset Tracker** is a production-ready, interactive hardware-assisted Laptop Lending & Biometric Asset Tracking System designed for universities, IT enterprises, and technical training institutes (PMYSD AI Course).

---

## 🌟 Key Features

1. **Dual Identification Checkpoint**:
   - **Laptop Identification**: High-speed QR & Barcode scanning via webcam/camera using classical Computer Vision (`pyzbar` + `OpenCV` — 0-latency, 100% deterministic, no external API keys required).
   - **Student Identification**: Biometric fingerprint recognition supporting USB HID keyboard emulation mode (ZKTeco, Mantra, DigitalPersona) or direct ID entry with retry handling.
2. **Strict Real-World Business Rules**:
   - **1-Laptop Loan Policy**: Prevents students from borrowing multiple laptops simultaneously.
   - **State Locking**: Prohibits checking out laptops that are already borrowed, retired, or under maintenance.
   - **Smart Return Validation**: Validates return states with full administrative audit logs.
   - **Overdue Tracking**: Automatically computes loan duration and flags overdue assets with visual warning badges.
3. **Dedicated Secure Admin Portal**:
   - Protected by master Security PIN (Default: `admin123`).
   - Full CRUD operations for Student Directory and Laptop Inventory Fleet with mandatory input validation on all fields.
   - Live Database Controls and audit logging.
   - Configurable Loan Policies (Overdue hour threshold, Organization branding, Admin PIN management).
4. **Printable QR Asset Tag Studio**:
   - Generates high-resolution branded asset sticker tags (with header, border, QR code, Laptop ID, and specs).
   - Single PNG download for physical asset labeling.
5. **Analytics & Multi-Sheet Excel Reports**:
   - Interactive Plotly visualizations (Fleet Availability Donut Chart, Departmental Loan Velocity).
   - One-click styled Excel export (`openpyxl`) featuring Executive Summary KPIs, active loans, student roster, and full transaction history.

---

## 🛠️ Technology Stack

| Layer | Tool / Library |
|---|---|
| **User Interface & Kiosk** | Streamlit (Python) + Custom Glassmorphic CSS |
| **Computer Vision / QR** | OpenCV (`cv2`) + `pyzbar` |
| **QR Badge Generator** | `qrcode` + Pillow (`PIL`) |
| **Biometric Identification** | USB HID Scanner Emulation / Python |
| **Database Engine** | SQLite3 (`lendtrack.db` with ACID guarantees & foreign key enforcement) |
| **Analytics & Plotting** | Plotly Express & Plotly Graph Objects |
| **Corporate Reporting** | Pandas + `openpyxl` |

---

## 🚀 Quick Start Guide

### 1. Installation
Install all required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launching the Web Application
Start the interactive Streamlit kiosk and management portal:
```bash
streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

### 3. Launching Terminal Checkpoint (Optional CLI Mode)
For physical check-in desks running on low-resource micro-PCs or kiosks:
```bash
python main.py
```

### 4. Admin Portal Login
- Go to the **🔐 Admin Management Portal** tab in the sidebar.
- Default Security PIN: `admin123` *(Can be changed anytime under System Policies)*.

---

## 📁 Project Structure

```text
laptop lending system/
├── database.py             # SQLite schema, business rules engine, CRUD & seeding
├── streamlit_app.py        # Streamlit Web App (Kiosk, Monitor, Analytics, Admin Portal)
├── main.py                 # Standalone Terminal Checkpoint Dispatcher
├── scan_qr.py              # OpenCV + Pyzbar Webcam QR scanner with reticle overlay
├── generate_qr.py          # Branded Asset Tag sticker generator & batch builder
├── generate_report.py      # Styled Multi-Sheet Excel Report Builder
├── fingerprint_input.py    # Biometric HID keyboard emulation module
├── lendtrack.db            # SQLite database file
├── qr_codes/               # Directory for generated laptop QR stickers
├── reports/                # Directory for generated Excel reports
└── requirements.txt        # Python package dependencies
```

---

## 🔌 Hardware Setup Notes

- **QR Barcode Stickers**: Print the tags generated in the **QR Asset Tag Studio** (or via `python generate_qr.py`) and adhere them to the lid/base of each laptop.
- **Biometric Fingerprint Scanner**: Plug any standard USB fingerprint device into the checkpoint PC. In standard HID keyboard emulation mode, scanning a finger will type the enrolled student ID directly into the input field.

---

## ⚠️ System Limitations & Deployment Notes

1. **Hardware Camera Access on Cloud Deployments:**
   - **Localhost:** The OpenCV-based webcam QR scanner (`cv2.VideoCapture`) connects directly to your laptop/desktop camera for high-speed local scanning.
   - **Cloud Platforms (Streamlit Cloud, AWS, Heroku):** The Python code runs on a remote cloud server that has **no physical camera hardware attached**. Therefore, clicking the local camera button on cloud-hosted deployments will not open your device's webcam. The system is architected primarily for on-premise local checkpoint stations.

2. **Ephemeral Local Database on Cloud Containers:**
   - The project uses a local SQLite database (`lendtrack.db`). On free cloud platforms like Streamlit Cloud, containers are **ephemeral** and reset to the GitHub repository version upon app restarts or idle sleep. For continuous online production use, connect the system to an external cloud database (e.g., Supabase, PostgreSQL).

3. **Physical Biometric USB Devices:**
   - Hardware biometric fingerprint scanners (USB HID mode) require a direct physical USB connection to the host machine running the kiosk station.

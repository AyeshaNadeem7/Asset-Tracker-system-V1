"""
streamlit_app.py
Asset Tracker — Complete Asset Lending & Tracking System
Styled with the Light Blue Coastal Palette across the entire page,
Strict Form Validations, Clean Asset Fleet Management, and Robust Admin Portal.
"""

import io
from datetime import datetime
from pathlib import Path

import pandas as pd
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import database as db
from scan_qr import scan_qr_from_webcam
from generate_report import generate_full_report
from generate_qr import generate_styled_qr_badge

# ----------------- Page Configuration -----------------
st.set_page_config(
    page_title="Asset Tracker",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db.init_db()

# Initialize session state variables
if "scanned_laptop_id" not in st.session_state:
    st.session_state["scanned_laptop_id"] = ""

if "last_registered_student_msg" not in st.session_state:
    st.session_state["last_registered_student_msg"] = ""

if "last_registered_laptop_msg" not in st.session_state:
    st.session_state["last_registered_laptop_msg"] = ""

# ----------------- Light Blue Design System & Aesthetics -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Full Page Light Blue Background (Matching Sidebar) */
    .stApp, 
    div[data-testid="stAppViewContainer"],
    section.main,
    .main .block-container {
        background: linear-gradient(180deg, #EAF4FA 0%, #DCEEF8 100%) !important;
    }
    
    /* Light Blue Sidebar */
    section[data-testid="stSidebar"], 
    div[data-testid="stSidebarContent"], 
    div[data-testid="stSidebarUserContent"],
    [data-testid="stSidebarHeader"] {
        background: linear-gradient(180deg, #E2F0F7 0%, #D8ECF6 100%) !important;
        border-right: 1.5px solid #B8D9E8 !important;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #0B2545 !important;
    }
    
    /* Top Header Banner */
    .coastal-header {
        background: linear-gradient(135deg, #0B2545 0%, #00437A 45%, #005C9E 80%, #29729B 100%);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(11, 37, 69, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #FFFFFF;
    }
    
    .coastal-title {
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    
    .coastal-subtitle {
        color: #CBE4EF !important;
        font-size: 1rem;
        margin-top: 0.35rem;
        font-weight: 400;
    }
    
    /* Stat Cards */
    .stat-card {
        background: #FFFFFF;
        border: 1.5px solid #C4DFEE;
        border-radius: 14px;
        padding: 1.2rem 1rem;
        text-align: center;
        box-shadow: 0 4px 14px rgba(11, 37, 69, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0, 92, 158, 0.15);
        border-color: #005C9E;
    }
    .stat-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #005C9E, #64A7C4);
    }
    
    .stat-label {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #29729B;
        margin-bottom: 0.35rem;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        color: #0B2545;
    }
    
    .stat-blue { color: #005C9E; }
    .stat-teal { color: #29729B; }
    .stat-red { color: #E11D48; }
    
    /* Step Titles */
    .step-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0B2545;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Info and Content Cards */
    .coastal-card {
        background: #FFFFFF;
        border: 1.5px solid #B8DCED;
        border-left: 6px solid #005C9E;
        padding: 1.1rem 1.35rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        color: #0B2545;
        box-shadow: 0 3px 10px rgba(11, 37, 69, 0.05);
    }
    
    .coastal-card-warning {
        background: #FFFFFF;
        border: 1.5px solid #FECACA;
        border-left: 6px solid #EF4444;
        padding: 1.1rem 1.35rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        color: #991B1B;
        box-shadow: 0 3px 10px rgba(239, 68, 68, 0.08);
    }

    /* Container Box Styling for Crisp Contrast */
    div[data-testid="stForm"],
    div[data-testid="stExpander"],
    .stDataFrame {
        background: #FFFFFF !important;
        border-radius: 14px !important;
        border: 1.5px solid #C4DFEE !important;
        padding: 1.25rem !important;
        box-shadow: 0 4px 14px rgba(11, 37, 69, 0.05) !important;
    }
    
    /* Inputs Styling */
    div[data-baseweb="input"] {
        background-color: #F7FBFE !important;
        border-radius: 8px !important;
    }
    
    /* Buttons with Primary Gradient */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #005C9E 0%, #29729B 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 1.4rem;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 4px 12px rgba(0, 92, 158, 0.25);
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #00437A 0%, #005C9E 100%);
        box-shadow: 0 6px 16px rgba(0, 67, 122, 0.35);
        transform: translateY(-1px);
        color: #FFFFFF !important;
    }
    
    .badge-coastal {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        background: #E0F0F8;
        color: #005C9E;
    }
</style>
""", unsafe_allow_html=True)


# ----------------- Top Header Banner -----------------

summary = db.get_fleet_summary()

header_html = (
    '<div class="coastal-header">'
    '<div style="display:flex; align-items:center; gap: 14px;">'
    '<svg width="40" height="40" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">'
    '<rect width="36" height="36" rx="10" fill="#00437A"/>'
    '<path d="M9 11C9 9.89543 9.89543 9 11 9H25C26.1046 9 27 9.89543 27 11V20C27 21.1046 26.1046 22 25 22H11C9.89543 22 9 21.1046 9 20V11Z" stroke="#FFFFFF" stroke-width="1.8"/>'
    '<path d="M7 24C7 23.4477 7.44772 23 8 23H28C28.5523 23 29 23.4477 29 24C29 25.1046 28.1046 26 27 26H9C7.89543 26 7 25.1046 7 24Z" fill="#38BDF8"/>'
    '<circle cx="18" cy="15.5" r="2" fill="#38BDF8"/>'
    '</svg>'
    '<div>'
    '<h1 class="coastal-title">Asset Tracker</h1>'
    '<p class="coastal-subtitle">Modern Laptop Lending, Inventory & Real-Time Asset Tracking System</p>'
    '</div>'
    '</div>'
    '</div>'
)
st.markdown(header_html, unsafe_allow_html=True)

# 4 Stat Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="stat-card"><div class="stat-label">Total Laptops</div><div class="stat-number">{summary["total_laptops"]}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><div class="stat-label">Available Laptops</div><div class="stat-number stat-blue">{summary["available_laptops"]}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-card"><div class="stat-label">Currently Borrowed</div><div class="stat-number stat-teal">{summary["borrowed_laptops"]}</div></div>', unsafe_allow_html=True)
with c4:
    overdue_cls = "stat-red" if summary['overdue_count'] > 0 else ""
    st.markdown(f'<div class="stat-card"><div class="stat-label">Overdue Laptops</div><div class="stat-number {overdue_cls}">{summary["overdue_count"]}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ----------------- Main Sidebar Navigation -----------------

sidebar_header_html = (
    '<div style="padding: 0.5rem 0 1.25rem 0; display: flex; align-items: center; justify-content: center; gap: 10px;">'
    '<svg width="28" height="28" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="36" height="36" rx="8" fill="#005C9E"/>'
    '<path d="M9 11C9 9.89543 9.89543 9 11 9H25C26.1046 9 27 9.89543 27 11V20C27 21.1046 26.1046 22 25 22H11C9.89543 22 9 21.1046 9 20V11Z" stroke="#FFFFFF" stroke-width="1.8"/>'
    '<path d="M7 24C7 23.4477 7.44772 23 8 23H28C28.5523 23 29 23.4477 29 24C29 25.1046 28.1046 26 27 26H9C7.89543 26 7 25.1046 7 24Z" fill="#38BDF8"/>'
    '<circle cx="18" cy="15.5" r="2" fill="#38BDF8"/>'
    '</svg>'
    '<h2 style="color: #0B2545 !important; margin:0; font-weight:800; font-size:1.35rem; display:inline;">Asset Tracker</h2>'
    '</div>'
)
st.sidebar.markdown(sidebar_header_html, unsafe_allow_html=True)

menu_choice = st.sidebar.radio(
    "Navigation Menu:",
    [
        "🔄 Borrow & Return Laptops",
        "📋 Laptop Status & Borrowers",
        "📊 Reports & Charts",
        "🔐 Admin Portal"
    ]
)

st.sidebar.divider()
policy_sidebar_html = (
    f'<div style="background: #FFFFFF; border: 1.5px solid #B8D9E8; border-radius: 10px; padding: 0.85rem; font-size: 0.85rem; color: #0B2545; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">'
    f'ℹ️ <b>Rule:</b> 1 student can borrow 1 laptop.<br>'
    f'⏱️ <b>Limit:</b> {db.get_setting("overdue_hours", "8")} hours max duration.'
    f'</div>'
)
st.sidebar.markdown(policy_sidebar_html, unsafe_allow_html=True)


# =========================================================================
# 1. BORROW & RETURN LAPTOPS (WITH STRICT BORROWER MATCHING)
# =========================================================================

if menu_choice == "🔄 Borrow & Return Laptops":
    st.subheader("🔄 Borrow or Return a Laptop")
    st.caption("Complete the steps below in sequence to borrow or return a laptop.")

    # Select Action
    action_type = st.radio(
        "Select Action:",
        ["📥 Borrow a Laptop", "📤 Return a Laptop"],
        horizontal=True
    )
    action = "borrow" if "Borrow" in action_type else "return"

    st.markdown("<br>", unsafe_allow_html=True)

    # STEP 1: Scan Laptop Camera (Webcam)
    st.markdown('<div class="step-title">1️⃣ Identify Laptop</div>', unsafe_allow_html=True)
    st.info("💡 Click the button below to turn on your laptop's camera. Hold the QR sticker in front of it to scan instantly!")

    selected_laptop_id = st.session_state["scanned_laptop_id"]

    if st.button("🎥 Open Laptop Camera & Scan QR", type="primary"):
        with st.spinner("Activating camera... Please hold your QR code in front of the lens."):
            scanned_code = scan_qr_from_webcam(timeout_seconds=15)
            if scanned_code:
                st.session_state["scanned_laptop_id"] = scanned_code
                selected_laptop_id = scanned_code
                st.success(f"🎉 Successfully Scanned: **{scanned_code}**")
                st.rerun()
            else:
                st.warning("Camera finished. No QR code detected (or camera was closed). Please click the button to try again.")

    # Selected Laptop Info Card & Current Borrower Look-up
    laptop_info = db.get_laptop(selected_laptop_id) if selected_laptop_id else None
    current_borrower = db.get_current_borrower(selected_laptop_id) if selected_laptop_id else None

    if laptop_info:
        st.success(f"✅ **Laptop Identified:** `{laptop_info['laptop_id']}`")
        
        borrower_line = ""
        if current_borrower:
            borrower_line = f'<br>👤 <b>Current Borrower:</b> {current_borrower["name"]} (<code>{current_borrower["enrollment_no"]}</code>) | {current_borrower["department"]}'

        card_html = (
            f'<div class="coastal-card">'
            f'<div style="font-weight:700; font-size:1.05rem; color:#0B2545;">{laptop_info["brand"]} {laptop_info["model"]}</div>'
            f'<div style="color:#29729B; font-size:0.9rem; margin-top:4px;">'
            f'Status: <span class="badge-coastal">{laptop_info["status"].upper()}</span>'
            f'{borrower_line}'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        if st.button("🔄 Clear / Scan Different Laptop"):
            st.session_state["scanned_laptop_id"] = ""
            st.rerun()
    elif selected_laptop_id:
        st.error(f"❌ Laptop '{selected_laptop_id}' not found in database.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # STEP 2: Identify Student (Appears directly BELOW Identify Laptop)
    st.markdown('<div class="step-title">2️⃣ Identify Student</div>', unsafe_allow_html=True)
    
    students_list = db.get_all_students()
    s_options = ["-- Select Registered Student --"] + [f"{s['enrollment_no']} - {s['name']} ({s['department']})" for s in students_list]
    s_picked = st.selectbox("Select Registered Student:", s_options)
    
    selected_student_id = ""
    if s_picked and s_picked != "-- Select Registered Student --":
        selected_student_id = s_picked.split(" - ")[0].strip()

    # Selected Student Info Card
    student_info = db.get_student(selected_student_id) if selected_student_id else None
    has_mismatch = False

    if student_info:
        st.success(f"✅ **Student Verified:** {student_info['name']}")
        active_loan = db.get_active_loan_for_student(student_info["enrollment_no"])
        loan_msg = f'⚠️ Holds Laptop: <b>{active_loan["laptop_id"]}</b>' if active_loan else "🟢 No Active Borrowings"
        
        stu_card_html = (
            f'<div class="coastal-card">'
            f'<div style="font-weight:700; font-size:1.05rem; color:#0B2545;">{student_info["name"]} ({student_info["enrollment_no"]})</div>'
            f'<div style="color:#29729B; font-size:0.9rem; margin-top:4px;">'
            f'🎓 Dept: <b>{student_info["department"]}</b> &nbsp;|&nbsp; '
            f'{loan_msg}'
            f'</div>'
            f'</div>'
        )
        st.markdown(stu_card_html, unsafe_allow_html=True)

        # Check for return mismatch
        if action == "return" and current_borrower:
            if current_borrower["enrollment_no"] != student_info["enrollment_no"]:
                has_mismatch = True
                warn_html = (
                    f'<div class="coastal-card-warning">'
                    f'<b>⛔ Authorization Warning:</b><br>'
                    f'Laptop <b>{laptop_info["laptop_id"]}</b> was borrowed by <b>{current_borrower["name"]}</b> ({current_borrower["enrollment_no"]}).<br>'
                    f'Selected student <b>{student_info["name"]}</b> ({student_info["enrollment_no"]}) is not authorized to return this laptop.'
                    f'</div>'
                )
                st.markdown(warn_html, unsafe_allow_html=True)

        # Check for borrow if already holds a laptop
        elif action == "borrow" and active_loan:
            notice_html = (
                f'<div class="coastal-card" style="border-left: 6px solid #29729B;">'
                f'ℹ️ <b>Active Loan Notice:</b><br>'
                f'Student <b>{student_info["name"]}</b> currently has laptop <b>{active_loan["laptop_id"]}</b>.<br>'
                f'You can issue an additional laptop with permission or return {active_loan["laptop_id"]} first.'
                f'</div>'
            )
            st.markdown(notice_html, unsafe_allow_html=True)

    elif selected_student_id:
        st.error(f"❌ Student ID '{selected_student_id}' is not registered.")

    # STEP 3: Confirm Button
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="step-title">3️⃣ Confirm & Complete Transaction</div>', unsafe_allow_html=True)

    admin_override_checked = False
    if has_mismatch:
        admin_override_checked = st.checkbox("🔓 Admin Override (Allow return by proxy)", value=False)
    elif action == "borrow" and student_info and db.get_active_loan_for_student(student_info["enrollment_no"]):
        admin_override_checked = st.checkbox("🔓 Allow Additional Laptop Loan", value=True)

    ready = bool(laptop_info and student_info)
    
    # Disable button if mismatch exists without admin override
    if has_mismatch and not admin_override_checked:
        ready = False

    button_title = f"🚀 Complete {action.capitalize()} Transaction"

    if st.button(button_title, type="primary", disabled=not ready, use_container_width=True):
        try:
            res = db.record_transaction(
                laptop_id=laptop_info["laptop_id"],
                enrollment_no=student_info["enrollment_no"],
                action=action,
                admin_override=admin_override_checked
            )
            st.balloons()
            st.success(f"""
            🎉 **Transaction Successful!**
            - **Laptop:** {res['laptop_id']} ({res['laptop_model']})
            - **Action:** {res['action'].upper()}
            - **Student:** {res['student_name']} ({res['enrollment_no']})
            - **Timestamp:** {res['timestamp']}
            """)
            st.session_state["scanned_laptop_id"] = ""
            st.rerun()
        except db.TransactionError as err:
            st.error(f"❌ **Transaction Blocked:** {err}")


# =========================================================================
# 2. LAPTOP STATUS & BORROWERS (BEAUTIFUL TABLE)
# =========================================================================

elif menu_choice == "📋 Laptop Status & Borrowers":
    st.subheader("📋 Laptop Status & Active Borrowers")
    st.caption("Live asset tracking list. Quickly search who holds which laptop and see who is overdue.")

    search_text = st.text_input("🔍 Search by Laptop ID, Brand, Model, Student Name, or Department:", "")

    borrowed_items = db.currently_borrowed_list()
    all_laptops = db.get_all_laptops()

    borrowed_map = {item["laptop_id"]: item for item in borrowed_items}

    table_data = []
    for lap in all_laptops:
        lid = lap["laptop_id"]
        row = {
            "Laptop ID": lid,
            "Brand": lap["brand"],
            "Model": lap["model"],
            "Status": lap["status"].capitalize(),
            "Borrower Name": "—",
            "Student Roll No": "—",
            "Department": "—",
            "Borrowed Time": "—",
            "Time Elapsed": "—",
            "Overdue?": "No"
        }
        if lid in borrowed_map:
            b = borrowed_map[lid]
            row["Borrower Name"] = b["student_name"]
            row["Student Roll No"] = b["enrollment_no"]
            row["Department"] = b["department"]
            row["Borrowed Time"] = b["borrowed_at"]
            row["Time Elapsed"] = b["duration_str"]
            row["Overdue?"] = "⚠️ YES" if b["is_overdue"] else "No"
        table_data.append(row)

    df = pd.DataFrame(table_data)

    if search_text.strip():
        q = search_text.lower()
        df = df[df.apply(lambda r: any(q in str(val).lower() for val in r), axis=1)]

    st.dataframe(df, use_container_width=True, hide_index=True)


# =========================================================================
# 3. REPORTS & CHARTS (COASTAL BLUES PALETTE CHARTS)
# =========================================================================

elif menu_choice == "📊 Reports & Charts":
    st.subheader("📊 Reports & Visual Analytics")
    st.caption("Visual insights rendered in the Coastal palette with one-click Excel report export.")

    col_chart1, col_chart2 = st.columns(2)

    # Chart 1: Donut with Coastal colors
    with col_chart1:
        st.markdown("##### 💻 Laptop Availability Breakdown")
        labels = ["Available", "Borrowed", "Maintenance"]
        values = [summary["available_laptops"], summary["borrowed_laptops"], summary["maintenance_laptops"]]
        coastal_donut_colors = ["#005C9E", "#4892B0", "#8CBED6"]
        
        fig1 = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.55,
            marker=dict(colors=coastal_donut_colors, line=dict(color='#FFFFFF', width=2)),
            textinfo="label+value"
        )])
        fig1.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig1, use_container_width=True)

    # Chart 2: Bar Chart with Coastal color sequence
    with col_chart2:
        st.markdown("##### 🎓 Laptops Borrowed by Department")
        conn = db.get_connection()
        dept_df = pd.read_sql_query("""
            SELECT s.department AS "Department", COUNT(t.id) AS "Total Borrowed"
            FROM transactions t
            JOIN students s ON s.enrollment_no = t.enrollment_no
            WHERE t.action = 'borrow'
            GROUP BY s.department
            ORDER BY "Total Borrowed" DESC
        """, conn)
        conn.close()

        if not dept_df.empty:
            fig2 = px.bar(
                dept_df, x="Department", y="Total Borrowed",
                color="Total Borrowed",
                color_continuous_scale=["#64A7C4", "#29729B", "#005C9E", "#0B2545"]
            )
            fig2.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No transaction history yet.")

    st.divider()

    st.markdown("### 📥 Download Excel Report")
    st.write("Generate and download a complete Excel report containing all transactions, students, and laptop records.")

    if st.button("📊 Generate and Download Excel Report", type="primary"):
        with st.spinner("Compiling Excel report..."):
            report_path = generate_full_report()
            with open(report_path, "rb") as f:
                st.download_button(
                    label="⬇️ Click here to Download Excel (.xlsx)",
                    data=f,
                    file_name=report_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            st.success(f"Report ready: {report_path.name}")

    st.markdown("#### Recent Transactions History")
    recent = db.get_all_transactions(limit=15)
    if recent:
        st.dataframe(pd.DataFrame(recent), use_container_width=True, hide_index=True)


# =========================================================================
# 4. ADMIN PORTAL (CLEAN, STRICT VALIDATIONS & POLISHED)
# =========================================================================

elif menu_choice == "🔐 Admin Portal":
    st.subheader("🔐 Master Administration Portal")
    st.caption("Central management portal for registered students, laptop inventory fleet, QR stickers, and system policies.")

    admin_pin = db.get_setting("admin_pin", "admin123")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        col_login = st.columns([1, 1.2, 1])[1]
        with col_login:
            auth_box_html = (
                '<div style="background:#FFFFFF; border:1.5px solid #D6E8F2; padding:2rem; border-radius:16px; text-align:center; box-shadow:0 8px 24px rgba(11,37,69,0.08);">'
                '<div style="width:48px; height:48px; background:#E0F0F8; color:#005C9E; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 1rem auto; font-size:1.5rem;">🔒</div>'
                '<h3 style="color:#0B2545; margin:0 0 0.5rem 0; font-weight:800;">Admin Authentication</h3>'
                '<p style="color:#64748B; font-size:0.9rem; margin-bottom:1rem;">Enter your security PIN to unlock the master control center.</p>'
                '</div>'
            )
            st.markdown(auth_box_html, unsafe_allow_html=True)
            st.write("")
            pin_input = st.text_input("Security PIN", type="password", placeholder="Enter PIN...")
            if st.button("Unlock Admin Portal", type="primary", use_container_width=True):
                if pin_input.strip() == admin_pin.strip():
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Wrong PIN. Access denied.")
        st.stop()

    st.sidebar.success("🔓 Logged in as Admin")
    if st.sidebar.button("Logout Admin"):
        st.session_state.admin_logged_in = False
        st.rerun()

    # Admin KPI Header
    admin_students = db.get_all_students()
    admin_laptops = db.get_all_laptops()
    
    adm_kpi1, adm_kpi2, adm_kpi3 = st.columns(3)
    with adm_kpi1:
        st.markdown(f'<div style="background:#FFFFFF; border:1px solid #D6E8F2; border-radius:12px; padding:1rem; text-align:center; box-shadow:0 2px 6px rgba(0,0,0,0.03);"><div style="font-size:0.8rem; font-weight:700; color:#4892B0; text-transform:uppercase;">Registered Students</div><div style="font-size:1.6rem; font-weight:800; color:#0B2545; margin-top:4px;">{len(admin_students)}</div></div>', unsafe_allow_html=True)
    with adm_kpi2:
        st.markdown(f'<div style="background:#FFFFFF; border:1px solid #D6E8F2; border-radius:12px; padding:1rem; text-align:center; box-shadow:0 2px 6px rgba(0,0,0,0.03);"><div style="font-size:0.8rem; font-weight:700; color:#4892B0; text-transform:uppercase;">Total Registered Laptops</div><div style="font-size:1.6rem; font-weight:800; color:#005C9E; margin-top:4px;">{len(admin_laptops)}</div></div>', unsafe_allow_html=True)
    with adm_kpi3:
        st.markdown(f'<div style="background:#FFFFFF; border:1px solid #D6E8F2; border-radius:12px; padding:1rem; text-align:center; box-shadow:0 2px 6px rgba(0,0,0,0.03);"><div style="font-size:0.8rem; font-weight:700; color:#4892B0; text-transform:uppercase;">Loan Policy Duration</div><div style="font-size:1.6rem; font-weight:800; color:#29729B; margin-top:4px;">{db.get_setting("overdue_hours", "8")} Hours</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    admin_tabs = st.tabs([
        "👥 Student Directory & Management",
        "💻 Laptop Fleet & Asset Management",
        "🏷️ QR Asset Tag Studio",
        "⚙️ Policies & Settings"
    ])

    # ----------------- Tab 1: Student Management -----------------
    with admin_tabs[0]:
        st.markdown('<div class="step-title">👥 Student Directory Management</div>', unsafe_allow_html=True)

        if st.session_state["last_registered_student_msg"]:
            st.success(st.session_state["last_registered_student_msg"])
            st.session_state["last_registered_student_msg"] = ""

        stu_action = st.radio("Student Action:", ["➕ Register New Student", "📋 View All Students", "✏️ Edit Student", "🗑️ Delete Student"], horizontal=True)

        if stu_action == "➕ Register New Student":
            with st.form("register_student_form", clear_on_submit=True):
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    s_id = st.text_input("Student Roll / Enrollment No. *", placeholder="e.g. STU-2024-007")
                    s_name = st.text_input("Student Full Name *", placeholder="e.g. Ali Khan")
                    s_dept = st.text_input("Department *", placeholder="e.g. Artificial Intelligence")
                with c_s2:
                    s_email = st.text_input("Email *", placeholder="e.g. ali@gmail.com")
                    s_contact = st.text_input("Phone / Contact *", placeholder="e.g. 03001234567")
                    s_status = st.selectbox("Status", ["active", "suspended"])

                submit_stu = st.form_submit_button("✅ Register Student", type="primary")
                if submit_stu:
                    # Strict validation: ALL fields must be filled
                    if not s_id.strip() or not s_name.strip() or not s_dept.strip() or not s_email.strip() or not s_contact.strip():
                        st.error("⚠️ All input fields are mandatory! Please fill in Roll No, Name, Department, Email, and Contact.")
                    else:
                        success = db.add_student(s_id, s_name, s_email, s_dept, s_contact, s_status)
                        if success:
                            st.session_state["last_registered_student_msg"] = f"🎉 Successfully registered student '{s_name}' (Roll No: {s_id}) in the system!"
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ Student Roll No '{s_id}' is already registered in the database.")

        elif stu_action == "📋 View All Students":
            stu_data = db.get_all_students()
            if stu_data:
                st.dataframe(pd.DataFrame(stu_data), use_container_width=True, hide_index=True)
            else:
                st.info("No students registered yet.")

        elif stu_action == "✏️ Edit Student":
            st_list = db.get_all_students()
            if not st_list:
                st.info("No students found to edit.")
            else:
                opts = [f"{s['enrollment_no']} - {s['name']}" for s in st_list]
                selected = st.selectbox("Select Student to Edit:", opts)
                if selected:
                    eid = selected.split(" - ")[0]
                    s_obj = db.get_student(eid)
                    with st.form("edit_student_form"):
                        e1, e2 = st.columns(2)
                        with e1:
                            new_name = st.text_input("Full Name *", value=s_obj["name"])
                            new_dept = st.text_input("Department *", value=s_obj.get("department") or "")
                            new_status = st.selectbox("Status", ["active", "suspended"], index=0 if s_obj["status"] == "active" else 1)
                        with e2:
                            new_email = st.text_input("Email *", value=s_obj.get("email") or "")
                            new_contact = st.text_input("Contact *", value=s_obj.get("contact") or "")

                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            if not new_name.strip() or not new_dept.strip() or not new_email.strip() or not new_contact.strip():
                                st.error("⚠️ All fields are mandatory! Please fill in all fields.")
                            else:
                                db.update_student(eid, new_name, new_email, new_dept, new_contact, new_status)
                                st.success(f"✅ Successfully updated record for student {eid} ({new_name})!")
                                st.rerun()

        elif stu_action == "🗑️ Delete Student":
            st_list = db.get_all_students()
            if not st_list:
                st.info("No students registered.")
            else:
                opts = [f"{s['enrollment_no']} - {s['name']}" for s in st_list]
                selected_del = st.selectbox("Select Student to Delete:", opts)
                if selected_del:
                    del_id = selected_del.split(" - ")[0]
                    st.warning(f"Are you sure you want to delete student **{del_id}**?")
                    if st.button(f"🗑️ Yes, Delete {del_id}", type="primary"):
                        try:
                            db.delete_student(del_id)
                            st.success(f"✅ Student {del_id} deleted successfully.")
                            st.rerun()
                        except db.TransactionError as e:
                            st.error(str(e))

    # ----------------- Tab 2: Laptop Management -----------------
    with admin_tabs[1]:
        st.markdown('<div class="step-title">💻 Laptop Fleet & Asset Management</div>', unsafe_allow_html=True)

        if st.session_state["last_registered_laptop_msg"]:
            st.success(st.session_state["last_registered_laptop_msg"])
            st.session_state["last_registered_laptop_msg"] = ""

        lap_action = st.radio("Laptop Action:", ["➕ Register New Laptop", "📋 View All Laptops", "✏️ Edit Laptop", "🗑️ Delete Laptop"], horizontal=True)

        if lap_action == "➕ Register New Laptop":
            with st.form("register_laptop_form", clear_on_submit=True):
                c_l1, c_l2 = st.columns(2)
                with c_l1:
                    l_id = st.text_input("Laptop ID *", placeholder="e.g. LAP-007")
                    l_brand = st.text_input("Brand *", placeholder="e.g. Dell / HP / Lenovo / Apple")
                with c_l2:
                    l_model = st.text_input("Model & Specs *", placeholder="e.g. Latitude 5420 (i7, 16GB RAM)")
                    l_serial = st.text_input("Serial Number *", placeholder="e.g. SN-DL-5420-07")

                l_status = st.selectbox("Status", ["available", "maintenance", "retired"])

                submit_lap = st.form_submit_button("✅ Register Laptop", type="primary")
                if submit_lap:
                    # Strict validation: ALL fields must be filled
                    if not l_id.strip() or not l_brand.strip() or not l_model.strip() or not l_serial.strip():
                        st.error("⚠️ All input fields are mandatory! Please fill in Laptop ID, Brand, Model & Specs, and Serial Number.")
                    else:
                        success = db.add_laptop(
                            laptop_id=l_id.strip(),
                            brand=l_brand.strip(),
                            model=l_model.strip(),
                            serial_no=l_serial.strip(),
                            status=l_status
                        )
                        if success:
                            st.session_state["last_registered_laptop_msg"] = f"🎉 Successfully registered laptop '{l_id}' ({l_brand} {l_model}) in the fleet!"
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ Laptop ID '{l_id}' is already registered in the database.")

        elif lap_action == "📋 View All Laptops":
            laptops_data = db.get_all_laptops()
            if laptops_data:
                st.dataframe(pd.DataFrame(laptops_data), use_container_width=True, hide_index=True)
            else:
                st.info("No laptops registered yet.")

        elif lap_action == "✏️ Edit Laptop":
            l_list = db.get_all_laptops()
            if not l_list:
                st.info("No laptops found to edit.")
            else:
                opts = [f"{l['laptop_id']} - {l['brand']} {l['model']} ({l['status'].upper()})" for l in l_list]
                selected_lap = st.selectbox("Select Laptop to Edit:", opts)
                if selected_lap:
                    target_lid = selected_lap.split(" - ")[0]
                    l_obj = db.get_laptop(target_lid)
                    with st.form("edit_lap_form"):
                        e_l1, e_l2 = st.columns(2)
                        with e_l1:
                            new_brand = st.text_input("Brand *", value=l_obj.get("brand") or "")
                            new_model = st.text_input("Model *", value=l_obj.get("model") or "")
                        with e_l2:
                            new_serial = st.text_input("Serial No *", value=l_obj.get("serial_no") or "")
                            status_opts = ["available", "borrowed", "maintenance", "retired"]
                            idx = status_opts.index(l_obj["status"]) if l_obj["status"] in status_opts else 0
                            new_st = st.selectbox("Status", status_opts, index=idx)

                        if st.form_submit_button("💾 Save Laptop Changes", type="primary"):
                            if not new_brand.strip() or not new_model.strip() or not new_serial.strip():
                                st.error("⚠️ All fields are mandatory! Please fill in Brand, Model, and Serial Number.")
                            else:
                                db.update_laptop(target_lid, new_brand, new_model, new_serial, new_st)
                                st.success(f"✅ Successfully updated laptop {target_lid} ({new_brand} {new_model})!")
                                st.rerun()

        elif lap_action == "🗑️ Delete Laptop":
            l_list = db.get_all_laptops()
            if not l_list:
                st.info("No laptops registered.")
            else:
                opts = [f"{l['laptop_id']} - {l['brand']} {l['model']}" for l in l_list]
                selected_del_l = st.selectbox("Select Laptop to Delete:", opts)
                if selected_del_l:
                    del_lid = selected_del_l.split(" - ")[0]
                    st.warning(f"Are you sure you want to delete laptop **{del_lid}**?")
                    if st.button(f"🗑️ Yes, Delete {del_lid}", type="primary"):
                        try:
                            db.delete_laptop(del_lid)
                            st.success(f"✅ Laptop {del_lid} deleted successfully.")
                            st.rerun()
                        except db.TransactionError as err:
                            st.error(str(err))

    # ----------------- Tab 3: QR Code Generator -----------------
    with admin_tabs[2]:
        st.markdown('<div class="step-title">🏷️ Generate & Print Laptop QR Stickers</div>', unsafe_allow_html=True)
        st.caption("Generate high-resolution printable QR sticker tags to paste on physical laptops.")

        laps_for_qr = db.get_all_laptops()
        if laps_for_qr:
            col_q1, col_q2 = st.columns([1, 1.2])
            with col_q1:
                chosen = st.selectbox("Select Laptop:", [f"{l['laptop_id']} - {l['brand']} {l['model']}" for l in laps_for_qr])
                chosen_id = chosen.split(" - ")[0]
                lap_info = db.get_laptop(chosen_id)

                sticker_img = generate_styled_qr_badge(
                    laptop_id=lap_info["laptop_id"],
                    model_name=f"{lap_info['brand']} {lap_info['model']}",
                    institution="ASSET TRACKER"
                )

                buf = io.BytesIO()
                sticker_img.save(buf, format="PNG")
                buf.seek(0)

                st.download_button(
                    label=f"⬇️ Download QR Sticker for {chosen_id} (PNG)",
                    data=buf,
                    file_name=f"{chosen_id}_QR_Sticker.png",
                    mime="image/png",
                    type="primary"
                )

            with col_q2:
                st.markdown("##### Printable Sticker Preview:")
                st.image(sticker_img, caption=f"Sticker for {chosen_id}", width=240)
        else:
            st.info("No laptops registered yet. Register a laptop first to generate QR stickers.")

    # ----------------- Tab 4: Settings & Loan Policies -----------------
    with admin_tabs[3]:
        st.markdown('<div class="step-title">⚙️ System Settings & Policies</div>', unsafe_allow_html=True)

        st.markdown("##### 🛡️ Loan Policies & Security")
        curr_pin = db.get_setting("admin_pin", "admin123")
        new_pin = st.text_input("Change Admin PIN *:", value=curr_pin, type="password")

        curr_overdue = db.get_setting("overdue_hours", "8")
        new_overdue = st.number_input("Overdue Threshold (Hours) *:", min_value=1, max_value=168, value=int(curr_overdue))

        if st.button("💾 Save Settings", type="primary"):
            if not new_pin.strip():
                st.error("Admin PIN cannot be empty.")
            else:
                db.set_setting("admin_pin", new_pin.strip())
                db.set_setting("overdue_hours", str(new_overdue))
                st.success("✅ Settings updated successfully!")
                st.rerun()
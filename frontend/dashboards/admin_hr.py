import streamlit as st
from api import (
    get_all_attendance, get_all_users, get_user_attendance,
    mark_attendance_any, mark_by_model, register_user
)
from datetime import date
import cv2
import time
import numpy as np
from preprocess import predict_identity
from preprocess import run_yolo_on_frame, check_ppe_compliance 


# Set layout once globally
st.set_page_config(layout="wide")


def show_dashboard(token):
    if "screen" not in st.session_state:
        st.session_state.screen = "dashboard"

    if "camera_active" not in st.session_state:
        st.session_state.camera_active = False

    st.sidebar.markdown("## ⚙️ Admin Controls")

    # Sidebar Navigation Buttons
    if st.sidebar.button("📊 Dashboard"):
        st.session_state.screen = "dashboard"

    if st.sidebar.button("📷 Open Camera"):
        st.session_state.screen = "camera"

    if st.sidebar.button("🦺 PPE Detection"):
        st.session_state.screen = "ppe_detection"

    if st.sidebar.button("➕ Add New User"):
        st.session_state.screen = "add_user"

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    # -------- MAIN SCREENS -------- #

    if st.session_state.screen == "dashboard":
        st.header("📊 Admin/HR Dashboard")
        tab1, tab2, tab3 = st.tabs(["All Attendance", "Mark Attendance", "User Attendance"])

        with tab1:
            st.subheader("📋 All Attendance Records")
            with st.spinner("⏳ Loading all attendance data..."):
                data = get_all_attendance(token)
            st.dataframe(data)

        with tab2:
            st.subheader("📝 Mark Attendance for Any Employee")
            users = get_all_users(token)
            if not users:
                st.error("❌ No employees found.")
            else:
                user_dict = {f"{u['name']} ({u['username']})": u['employee_id'] for u in users}
                selected_user = st.selectbox("Select Employee", list(user_dict.keys()), key="mark_attendance_select")
                selected_id = user_dict[selected_user]

                status = st.selectbox("Status", ["Present", "Absent", "Late", "On Leave"], key="status_select")
                today = st.date_input("Date", value=date.today(), key="date_input")

                if st.button("Mark"):
                    with st.spinner("🕒 Submitting..."):
                        res = mark_attendance_any(token, {
                            "employee_id": selected_id,
                            "date": str(today),
                            "status": status
                        })
                    if res.ok:
                        st.success("✅ Attendance marked")
                    else:
                        st.error(f"❌ Failed: {res.json().get('msg', 'Unknown error')}")

        with tab3:
            st.subheader("👤 View Attendance by Employee")
            with st.spinner("⏳ Fetching employee list..."):
                users = get_all_users(token)
                if not users:
                    st.error("⚠️ Failed to load users.")
                else:
                    user_map = {f"{u['name']} ({u['username']})": u["employee_id"] for u in users}
                    selected_name = st.selectbox("Select Employee", list(user_map.keys()), key="view_attendance_user_select")

                    if st.button("Show Attendance"):
                        emp_id = user_map[selected_name]
                        with st.spinner(f"📅 Loading attendance for {selected_name}..."):
                            data = get_user_attendance(token, emp_id)
                        if data:
                            st.dataframe(data, use_container_width=True)
                        else:
                            st.info("No attendance records found.")

    elif st.session_state.screen == "camera":
        st.header("📱 Live iPhone Feed")
        st.info("Click the button below to start or stop the camera stream from your iPhone (DroidCam).")

        FRAME_WINDOW = st.empty()
        prediction_box = st.empty()
        status_box = st.empty()
        index = 1  # Use 0 or 1 based on your DroidCam

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎥 Start Camera"):
                st.session_state.camera_active = True

        with col2:
            if st.button("🛑 Stop Camera"):
                st.session_state.camera_active = False

        if st.session_state.camera_active:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

            if not cap.isOpened():
                st.error("❌ Cannot open DroidCam")
                st.session_state.camera_active = False
            else:
                st.success("✅ DroidCam Video stream opened")
                frame_count = 0

                # 🔁 Load user list once
                user_map = {}
                with st.spinner("🔍 Loading user data..."):
                    users = get_all_users(token)
                    user_map = {u["name"].lower(): u["employee_id"] for u in users}

                while st.session_state.camera_active:
                    ret, frame = cap.read()
                    if not ret or frame is None or frame.shape[0] == 0:
                        st.warning("⚠️ No frame received or invalid frame.")
                        break

                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    FRAME_WINDOW.image(frame_rgb, channels="RGB")

                    frame_count += 1
                    if frame_count % 5 == 0:
                        resized = cv2.resize(frame, (640, 480))
                        username = predict_identity(resized)

                        if username:
                            username = username.lower()
                            prediction_box.markdown(f"🧠 **Predicted:** `{username}`")
                            employee_id = user_map.get(username)
                            if employee_id:
                                res = mark_by_model(employee_id, status="Present")
                                if res.ok:
                                    status_box.success(f"✅ Attendance marked for: {username}")
                                else:
                                    status_box.error(f"❌ Failed to mark attendance: {res.status_code}")
                            else:
                                status_box.warning(f"⚠️ Username `{username}` not found.")
                        else:
                            prediction_box.markdown("🔍 No face detected")
                            status_box.empty()

                    time.sleep(0.03)

                cap.release()
                st.session_state.camera_active = False

    elif st.session_state.screen == "ppe_detection":
        st.header("🦺 Real-Time PPE Detection")
        st.info("Stream from DroidCam and monitor PPE compliance in real-time.")

        FRAME_WINDOW = st.empty()
        result_box = st.empty()
        index = 1  # Camera index

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎥 Start PPE Camera"):
                st.session_state.camera_active = True

        with col2:
            if st.button("🛑 Stop PPE Camera"):
                st.session_state.camera_active = False

        if st.session_state.camera_active:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

            if not cap.isOpened():
                st.error("❌ Cannot open camera.")
                st.session_state.camera_active = False
            else:
                st.success("✅ Video stream opened")
                frame_count = 0

                while st.session_state.camera_active:
                    ret, frame = cap.read()
                    if not ret or frame is None or frame.shape[0] == 0:
                        st.warning("⚠️ Invalid frame.")
                        break

                    frame_count += 1
                    if frame_count % 2 == 0:
                        resized_frame = cv2.resize(frame, (640, 640))
                        with st.spinner("🧠 Detecting PPE..."):
                            annotated_img, boxes_by_class, _ = run_yolo_on_frame(frame)
                            final_img, summary = check_ppe_compliance(annotated_img, boxes_by_class)
                            print("----"*10)
                            print(summary)
                            print("----"*10)
                            

                        FRAME_WINDOW.image(cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB), channels="RGB")
                        result_box.code("### 📋 PPE Compliance Summary:")
                        summary_block = ""

                        for idx, compliance in summary:
                            summary_block += f"🧍 Person {idx} Compliance:\n"
                            for item, ok in compliance.items():
                                summary_block += f"   - {item}: {'✅' if ok else '❌'}\n"
                            summary_block += "\n"

                        result_box.code(summary_block)

                    time.sleep(0.05)

                cap.release()
                st.session_state.camera_active = False

    elif st.session_state.screen == "add_user":
        st.header("🧾 Register a New User")

        name = st.text_input("Full Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Employee", "HR", "Admin"])
        department = st.text_input("Department")
        designation = st.text_input("Designation")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        join_date = st.date_input("Joining Date")
        status = st.selectbox("Status", ["Active", "Inactive"])

        if st.button("📝 Register User"):
            user_data = {
                "name": name,
                "username": username,
                "password": password,
                "role": role,
                "department": department,
                "designation": designation,
                "email": email,
                "phone": phone,
                "join_date": str(join_date),
                "status": status
            }

            with st.spinner("Registering user..."):
                res = register_user(token, user_data)

            if res and res.status_code == 201:
                st.success("✅ User registered successfully!")
            else:
                msg = res.json().get("msg", "Unknown error")
                st.error(f"❌ Failed: {msg}")

import streamlit as st
from auth import login_form
from dashboards import admin_hr, employee 
from api import get_my_info


st.set_page_config(
    page_title="Image Attendance", layout="centered", initial_sidebar_state="auto"
)


if "token" not in st.session_state:
    login_form()
else:
    role = st.session_state["role"]
    token = st.session_state["token"]

    if role in ["Admin", "HR"]:
        admin_hr.show_dashboard(token)
    elif role == "Employee":
        employee.show_dashboard(token)
    else:
        st.error("❌ Unauthorized role")

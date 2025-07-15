import streamlit as st
from api import get_my_info, get_own_attendance, mark_own_attendance

def show_dashboard(token):
    # Inject styling
    st.markdown("""
        <style>
            .employee-container {
                max-width: 1600px;
                margin: auto;
                padding: 2rem 3rem;
            }
      
            .stSelectbox > div {
                font-size: 16px;
            }
            .stDataFrame {
                margin-top: 1rem;
            }
            .stTabs [role="tab"] {
                font-size: 18px;
                padding: 0.5rem 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

    role = st.session_state["role"]
    token = st.session_state["token"]
    
    user_info = get_my_info(st.session_state["token"])

    if user_info:
        with st.sidebar:
            st.markdown("### 👤 **User Profile**")
            st.markdown("---")

            def profile_row(label, value, icon=""):
                col1, col2 = st.columns([3, 3.5])
                with col1:
                    st.markdown(f"{icon} **{label}**")
                with col2:
                    st.markdown(f"`{value}`")

            profile_row("Name", user_info["name"], "🧑")
            profile_row("Username", user_info["username"], "🆔")
            profile_row("Role", user_info["role"], "🎓")
            profile_row("Department", user_info["department"], "🏢")
            profile_row("Designation", user_info["designation"], "💼")
            profile_row("Email", user_info["email"], "📧")
            profile_row("Phone", user_info["phone"], "📞")
            profile_row("Join Date", user_info["join_date"], "📅")
            profile_row("Status", user_info["status"], "✅")

            st.markdown("---")
    else:
        st.sidebar.error("⚠️ Could not load user info.")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()



    st.markdown('<div class="employee-container">', unsafe_allow_html=True)
    st.title("🧍 Employee Dashboard")

    tab1, tab2 = st.tabs(["📅 My Attendance", "🕒 Mark Today"])

    with tab1:
        st.subheader("Your Attendance Records")
        with st.spinner("⏳ Loading your attendance..."):
            data = get_own_attendance(token)
        if data:
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No attendance records found.")

    with tab2:
        st.subheader("Mark Today’s Attendance")
        status = st.selectbox("Status", ["Present", "Absent", "Leave"])
        if st.button("Mark Attendance"):
            with st.spinner("📝 Submitting attendance..."):
                res = mark_own_attendance(token, status)
            if res.ok:
                st.success("✅ Attendance marked successfully!")
            else:
                st.error("❌ Failed to mark attendance.")

    st.markdown("</div>", unsafe_allow_html=True)

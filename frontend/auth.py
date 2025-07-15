import streamlit as st
from api import login_user

def login_form():
    st.set_page_config(page_title="Login", layout="centered")

    # ✅ Style injection
    st.markdown("""
    <style>
  
    .login-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
    }

  
    .stTextInput > div > input {
        text-align: center;
        width: 100%;
        max-width: 280px;
        margin: auto;
    }

    .stButton > button {
        background-color: #1f77b4;
        color: white;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
        margin-top:1rem;
    }

    .stButton > button:hover {
        background-color: #0000001A;
        transform: scale(1.03);
        border: 1px solid #FF6065
    }
                
    </style>
    """, unsafe_allow_html=True)

    # ✅ Wrap everything inside a single st.markdown to style outer box
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col21, col22, col23 = st.columns([1, 2, 1])
        with col22:
            st.markdown("""
                    <div class="login-title">🔐 Login</div>
                """, unsafe_allow_html=True)

         # ✅ Inputs (Streamlit components)
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
   
        if st.button("Login"):
            res = login_user(username, password)
            if res and "token" in res:
                st.session_state['token'] = res['token']
                st.session_state['role'] = res['role']
                st.session_state['username'] = username
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")



   
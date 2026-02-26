import streamlit as st
from auth import load_users
from ui import main_app
from auth import login_page, signup_page, forgot_password_page, save_users

st.set_page_config(page_title="AI-Based Spam Mail Detection", layout="wide")

# initialize session state (keeps original names)
for key, value in {
    "users": load_users(),
    "logged_in": False,
    "page": "login",
    "chat_history": [],
    "theme": "Light Mode",
    "last_mail": "",
    "splash_done": False,
    "username": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# simple splash (keeps existing behavior)
if not st.session_state["splash_done"]:
    splash_placeholder = st.empty()
    with splash_placeholder.container():
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.image("spam_header.jpg", width=10000)
        st.markdown("<h2 style='text-align:center;'>AI-Based Spam Mail Detector</h2>", unsafe_allow_html=True)
    import time; time.sleep(1)
    splash_placeholder.empty()
    st.session_state["splash_done"] = True

# route pages
if st.session_state["page"] == "login":
    login_page()
elif st.session_state["page"] == "signup":
    signup_page()
elif st.session_state["page"] == "forgot":
    forgot_password_page()
elif st.session_state["page"] == "main":
    main_app()

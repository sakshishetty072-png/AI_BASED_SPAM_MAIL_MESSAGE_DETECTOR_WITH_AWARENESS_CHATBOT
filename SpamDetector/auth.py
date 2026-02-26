import os
import pickle
import time
import streamlit as st

USER_FILE = "users.pkl"

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "rb") as f:
            users = pickle.load(f)
            for u in users:
                if "history" not in users[u] or not isinstance(users[u]["history"], list):
                    users[u]["history"] = []
            return users
    else:
        return {"admin": {"password": "admin123", "history": []}}

def save_users(users):
    with open(USER_FILE, "wb") as f:
        pickle.dump(users, f)

# --- helper callbacks (used by widgets) ---
def _do_logout():
    st.session_state["logged_in"] = False
    st.session_state["page"] = "login"
    # clear any transient auth messages so login page doesn't show stale success/error
    for k in ("_login_success", "_login_error", "_signup_success", "_signup_error", "_reset_success", "_reset_error"):
        st.session_state.pop(k, None)

def _goto_signup():
    # clear transient auth messages when switching pages
    for k in ("_login_success", "_login_error", "_signup_success", "_signup_error", "_reset_success", "_reset_error"):
        st.session_state.pop(k, None)
    st.session_state["page"] = "signup"

def _goto_forgot():
    for k in ("_login_success", "_login_error", "_signup_success", "_signup_error", "_reset_success", "_reset_error"):
        st.session_state.pop(k, None)
    st.session_state["page"] = "forgot"

def _goto_login():
    for k in ("_login_success", "_login_error", "_signup_success", "_signup_error", "_reset_success", "_reset_error"):
        st.session_state.pop(k, None)
    st.session_state["page"] = "login"

def _login_action():
    username = st.session_state.get("login_username", "").strip()
    password = st.session_state.get("login_password", "")
    users = st.session_state.get("users", {})
    if username in users and users[username]["password"] == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state["page"] = "main"
        st.session_state.pop("_login_error", None)
        st.session_state["_login_success"] = True
    else:
        st.session_state["_login_error"] = "❌ Invalid username or password."
        st.session_state.pop("_login_success", None)

def _signup_action():
    username = st.session_state.get("signup_username", "").strip()
    password = st.session_state.get("signup_password", "")
    confirm = st.session_state.get("signup_confirm", "")
    users = st.session_state.get("users", {})
    import re
    pw_ok = re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$', password)
    if username in users:
        st.session_state["_signup_error"] = "⚠ Username already exists."
        st.session_state.pop("_signup_success", None)
    elif password != confirm:
        st.session_state["_signup_error"] = "⚠ Passwords don’t match."
        st.session_state.pop("_signup_success", None)
    elif not pw_ok:
        st.session_state["_signup_error"] = ("⚠ Password must be at least 8 characters and include a letter, "
                                            "a number and a special character. Example: Thirsha@456")
        st.session_state.pop("_signup_success", None)
    else:
        users[username] = {"password": password, "history": []}
        save_users(users)
        st.session_state["_signup_success"] = True
        st.session_state.pop("_signup_error", None)
        st.session_state["page"] = "login"

def _reset_action():
    username = st.session_state.get("reset_username", "").strip()
    new_pass = st.session_state.get("reset_new_pass", "")
    confirm = st.session_state.get("reset_confirm", "")
    users = st.session_state.get("users", {})
    if username not in users:
        st.session_state["_reset_error"] = "❌ Username not found."
        st.session_state.pop("_reset_success", None)
    elif new_pass != confirm:
        st.session_state["_reset_error"] = "⚠ Passwords do not match."
        st.session_state.pop("_reset_success", None)
    else:
        users[username]["password"] = new_pass
        save_users(users)
        st.session_state["_reset_success"] = True
        st.session_state.pop("_reset_error", None)
        st.session_state["page"] = "login"

# --- pages ---
def profile_page():
    st.write(f"Username: {st.session_state.get('username','')}")
    st.button("🚪 Logout", on_click=_do_logout)

def login_page():
    if st.session_state.get("logged_in", False):
        return
    st.title("🔐 Login")
    with st.form("login_form"):
        st.text_input("Username", key="login_username")
        st.text_input("Password", type="password", key="login_password")
        st.form_submit_button("Login", on_click=_login_action)
    # show messages set by callback
    if st.session_state.pop("_login_success", False):
        st.success("✅ Login successful!")
        time.sleep(0.01)
    if msg := st.session_state.pop("_login_error", None):
        st.error(msg)

    col1, col2 = st.columns(2)
    with col1:
        st.button("🆕 Sign Up", on_click=_goto_signup)
    with col2:
        st.button("🔑 Forgot Password", on_click=_goto_forgot)

def signup_page():
    st.title("🆕 Create Account")
    with st.form("signup_form"):
        st.text_input("Choose Username", key="signup_username")
        st.text_input("Choose Password", type="password", key="signup_password")
        st.text_input("Confirm Password", type="password", key="signup_confirm")
        st.form_submit_button("Sign Up", on_click=_signup_action)
    # st.caption("Password must be at least 8 characters and include a letter, a number and a special character (e.g., Thirsha@456)")
    if st.session_state.pop("_signup_success", False):
        st.success("✅ Account created! Please login.")
        time.sleep(0.2)
    if msg := st.session_state.pop("_signup_error", None):
        st.error(msg)

    st.button("⬅ Back to Login", on_click=_goto_login)

def forgot_password_page():
    st.title("🔑 Reset Password")
    with st.form("reset_form"):
        st.text_input("Enter your username", key="reset_username")
        st.text_input("Enter new password", type="password", key="reset_new_pass")
        st.text_input("Confirm new password", type="password", key="reset_confirm")
        st.form_submit_button("Reset Password", on_click=_reset_action)
    if st.session_state.pop("_reset_success", False):
        st.success("✅ Password reset successfully! Please login again.")
        time.sleep(0.2)
    if msg := st.session_state.pop("_reset_error", None):
        st.error(msg)

    st.button("⬅ Back to Login", on_click=_goto_login) 

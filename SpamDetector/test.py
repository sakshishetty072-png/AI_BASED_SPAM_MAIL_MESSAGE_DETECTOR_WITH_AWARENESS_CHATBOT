import streamlit as st
import pickle
import os
import re
import time

st.set_page_config(page_title="AI-Based Spam Mail Detection", layout="wide")

# ---------------------------
# Load Model and Vectorizer
# ---------------------------
model = pickle.load(open("spam_classifier.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# ---------------------------
# Helper Files
# ---------------------------
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

# ---------------------------
# Initialize Session State
# ---------------------------
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

# ---------------------------
# Splash Screen
# ---------------------------
if not st.session_state["splash_done"]:
    splash_placeholder = st.empty()
    with splash_placeholder.container():
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.image("spam_header.png", width=10000)
        st.markdown("<h2 style='text-align:center;'>AI-Based Spam Mail Detector</h2>", unsafe_allow_html=True)
    time.sleep(1)
    splash_placeholder.empty()
    st.session_state["splash_done"] = True

# ---------------------------
# Text Cleaning
# ---------------------------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

# ---------------------------
# Spam Prediction
# ---------------------------
def predict_spam(email_text):
    cleaned = clean_text(email_text)
    vec = vectorizer.transform([cleaned])
    pred = model.predict(vec)[0]
    return "Spam" if pred == 1 else "Ham", model.predict_proba(vec)[0]

# ---------------------------
# Scam Type Detection
# ---------------------------
def predict_scam_type(message):
    text = message.lower()
    if any(word in text for word in ["win", "prize", "lottery", "reward", "free gift"]):
        return "🎁 Lottery / Reward Scam"
    elif any(word in text for word in ["bank", "account", "verify", "password", "login", "otp"]):
        return "🏦 Bank / Phishing Scam"
    elif any(word in text for word in ["job", "hiring", "vacancy", "work from home"]):
        return "💼 Fake Job Offer"
    elif any(word in text for word in ["love", "relationship", "dating", "marriage"]):
        return "💔 Romance Scam"
    elif any(word in text for word in ["investment", "bitcoin", "crypto", "trading"]):
        return "💰 Investment Fraud"
    else:
        return "⚠ General Scam / Unknown Category"

# ---------------------------
# Awareness Tips
# ---------------------------
def scam_awareness_tips(scam_type):
    tips = {
        "🎁 Lottery / Reward Scam": [
            "Never click links claiming you've won prizes.",
            "Legit companies don’t ask for money to claim rewards.",
            "Be cautious of emails with 'Congratulations!' in the subject."
        ],
        "🏦 Bank / Phishing Scam": [
            "Banks never ask for OTP or passwords through email/SMS.",
            "Avoid clicking links asking to 'verify your account'.",
            "Always log in via official bank websites."
        ],
        "💼 Fake Job Offer": [
            "Avoid job offers that ask for money.",
            "Check company websites before responding.",
            "Be careful of 'work-from-home' jobs with huge pay."
        ],
        "💔 Romance Scam": [
            "Don’t share personal or financial details online.",
            "Scammers often pretend to fall in love quickly.",
            "Never send money to someone you haven’t met."
        ],
        "💰 Investment Fraud": [
            "Avoid schemes promising 'guaranteed returns'.",
            "Research companies before investing.",
            "Be careful of random crypto or trading offers."
        ],
        "⚠ General Scam / Unknown Category": [
            "Avoid clicking suspicious links.",
            "Check sender email before replying."
        ]
    }
    return tips.get(scam_type, ["Be cautious and double-check suspicious messages."])

# ---------------------------
# Theme
# ---------------------------
def apply_theme(theme_choice):
    if theme_choice == "Dark Mode":
        st.markdown("""
        <style>
        body, .stApp {background-color: #121212; color: white;}
        textarea, .stButton>button {background-color: #1e1e1e !important; color: white !important;}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        body, .stApp {background-color: #ffffff; color: black;}
        textarea, .stButton>button {background-color: #f9f9f9 !important; color: black !important;}
        </style>
        """, unsafe_allow_html=True)

# ---------------------------
# Profile Page
# ---------------------------
def profile_page():
    st.write(f"Username: {st.session_state['username']}")
    if st.button("🚪 Logout"):
        st.session_state["logged_in"] = False
        st.session_state["page"] = "login"

# ---------------------------
# Forgot Password
# ---------------------------
def forgot_password():
    st.title("🔑 Reset Password")
    with st.form("reset_form"):
        username = st.text_input("Enter your username")
        new_pass = st.text_input("Enter new password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Reset Password")

    if submitted:
        users = st.session_state["users"]
        if username not in users:
            st.error("❌ Username not found.")
        elif new_pass != confirm:
            st.warning("⚠ Passwords do not match.")
        else:
            users[username]["password"] = new_pass
            save_users(users)
            st.success("✅ Password reset successfully! Please login again.")
            time.sleep(0.2)
            st.session_state["page"] = "login"

    if st.button("⬅ Back to Login"):
        st.session_state["page"] = "login"

# ---------------------------
# Login Page
# ---------------------------
def login():
    if st.session_state["logged_in"]:
        return

    st.title("🔐 Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        users = st.session_state["users"]
        if username in users and users[username]["password"] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("✅ Login successful!")
            time.sleep(0.01)
            st.session_state["page"] = "main"  # <- login page disappears
            return  # <- immediately stop rendering login page
        else:
            st.error("❌ Invalid username or password.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 Sign Up"):
            st.session_state["page"] = "signup"
            return
    with col2:
        if st.button("🔑 Forgot Password"):
            st.session_state["page"] = "forgot"
            return


# ---------------------------
# Signup Page
# ---------------------------
def signup():
    st.title("🆕 Create Account")
    with st.form("signup_form"):
        username = st.text_input("Choose Username")
        password = st.text_input("Choose Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign Up")

    if submitted:
        if username in st.session_state["users"]:
            st.error("⚠ Username already exists.")
        elif password != confirm:
            st.error("⚠ Passwords don’t match.")
        else:
            st.session_state["users"][username] = {"password": password, "history": []}
            save_users(st.session_state["users"])
            st.success("✅ Account created! Please login.")
            time.sleep(0.2)
            st.session_state["page"] = "login"

    if st.button("⬅ Back to Login"):
        st.session_state["page"] = "login"

# ---------------------------
# Main App
# ---------------------------
def main_app():
    st.title("🤖 AI Scam Awareness Chatbot")
    st.subheader("AI-powered assistant to detect and learn about scam messages 📩")

    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1])

    with col1:
        with st.expander("❓ Help"):
            st.write("""
            How to Use:
            1. Paste a suspicious message below.
            2. Click "CHECK".
            3. The chatbot will tell if it’s spam/ham, and confidence level.
            4. Ask follow-up questions in the second box for scam type and tips.
            """)
    with col2:
        with st.expander("ℹ About"):
            st.write("""
            Project Title: AI Scam Awareness Chatbot  
            Guide: Dr. Padmanayana (HOD, AI & DS)  
            Team Members:  
            - Ruby  
            - Sakshi  
            - Sudeepthi  
            - Thrisha  
            """)
    with col3:
        with st.expander("🎨 Theme"):
            theme = st.radio("Select Theme", ["Light Mode", "Dark Mode"], key="theme")
            apply_theme(theme)
    with col4:
        with st.expander("📜 Chat History"):
            history = st.session_state["users"][st.session_state["username"]]["history"]
            if history:
                for msg in history[-5:]:
                    st.write(f"🧾 {msg}")
            else:
                st.write("No chat history yet.")
    with col5:
        with st.expander("👤 Profile"):
            profile_page()

    st.markdown("---")

    # ---------------------------
    # CHECK Form
    # ---------------------------
    with st.form("check_form"):
        user_input = st.text_area("Paste suspicious mail/message here:", height=120)
        submitted = st.form_submit_button("CHECK")

    if submitted:
        if user_input.strip() == "":
            st.warning("⚠ Please enter a message.")
        else:
            result, proba = predict_spam(user_input)
            ham_confidence = round(proba[0]*100, 2)
            spam_confidence = round(proba[1]*100, 2)

            if result == "Ham":
                bot_reply = f'<p style="color:green;">✅ This message seems <b>safe (Ham)</b>.<br>Confidence: {ham_confidence}%</p>'
            else:
                bot_reply = f'<p style="color:red;">🚨 This message seems <b>Spam</b>.<br>Confidence: {spam_confidence}%</p>'

            st.markdown(bot_reply, unsafe_allow_html=True)
            st.session_state["users"][st.session_state["username"]]["history"].append(user_input)
            st.session_state["last_mail"] = user_input
            save_users(st.session_state["users"])
            st.session_state["chat_history"].append(("Bot", bot_reply))

    # ---------------------------
    # Ask Bot Form
    # ---------------------------
    st.markdown("### 💭 Chat Conversation")
    with st.form("ask_form"):
        followup = st.text_input("Ask about this message (e.g., Is it safe? What scam type?)")
        ask_submitted = st.form_submit_button("Ask Bot")

    followup_placeholder = st.empty()

    if ask_submitted:
        if st.session_state["last_mail"] == "":
            followup_placeholder.info("⚠ Start by checking a suspicious message above.")
        elif followup.strip() != "":
            mail = st.session_state["last_mail"]
            result, _ = predict_spam(mail)
            scam_type = predict_scam_type(mail)
            tips = scam_awareness_tips(scam_type)
            color = "green" if result == "Ham" else "red"

            if "safe" in followup.lower() or "spam" in followup.lower():
                answer = f"This message is classified as <b>{result}</b>."
            elif "type" in followup.lower() or "category" in followup.lower():
                if result == "Spam":
                    answer = f"This message is a <b>{scam_type}</b>."
                else:
                    answer = "This message is safe; no scam type applicable."
            elif "tip" in followup.lower() or "advice" in followup.lower():
                if result == "Spam":
                    answer = "Here are some tips:<br>" + "<br>".join(f"- {tip}" for tip in tips)
                else:
                    answer = "This message is safe; no tips needed."
            else:
                if result == "Spam":
                    answer = f"The message is <b>{result}</b>. It's categorized as <b>{scam_type}</b>.<br>Tips:<br>" + "<br>".join(f"- {tip}" for tip in tips)
                else:
                    answer = f"The message is <b>{result}</b>."

            answer_colored = f'<p style="color:{color};">{answer}</p>'
            followup_placeholder.markdown(answer_colored, unsafe_allow_html=True)
            st.session_state["chat_history"].append(("Bot", answer_colored))

# ---------------------------
# Run App
# ---------------------------
if st.session_state["page"] == "login":
    login()
elif st.session_state["page"] == "signup":
    signup()
elif st.session_state["page"] == "forgot":
    forgot_password()
elif st.session_state["page"] == "main":
    main_app() 

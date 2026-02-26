import streamlit as st
from auth import profile_page, load_users, save_users
from model import predict_spam
from model import load_model_and_vectorizer
from text_utils import clean_text

def apply_theme(theme_choice):
    if theme_choice == "Dark Mode":
        st.markdown("""
        <style>
        /* Page background and primary text */
        body, .stApp, .block-container { background-color: #0b1220 !important; color: #e6eef8 !important; }

        /* Headings, markdown and labels */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown { color: #e6eef8 !important; }

        /* Inputs, textareas, selects */
        input[type="text"], input[type="password"], textarea, .stTextInput>div>input, .stTextArea>div>textarea,
        .stSelectbox, .stMultiSelect { background-color: #0f1724 !important; color: #e6eef8 !important; border: 1px solid #1f2937 !important; }

        /* Buttons */
        .stButton>button { background-color: #111827 !important; color: #e6eef8 !important; border: 1px solid #374151 !important; }

        /* Expander and containers */
        .stExpander, .st-expander { background-color: transparent !important; color: #e6eef8 !important; }
        .stSidebar, .css-1d391kg { background-color: #071025 !important; color: #e6eef8 !important; }

        /* Placeholders, small text */
        small, .stCaption, .stMetric { color: #c8d6e8 !important; }

        /* Links */
        a { color: #7dd3fc !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        /* Page background and primary text */
        body, .stApp, .block-container { background-color: #ffffff !important; color: #0b1220 !important; }

        /* Headings, markdown and labels */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown { color: #0b1220 !important; }

        /* Inputs, textareas, selects */
        input[type="text"], input[type="password"], textarea, .stTextInput>div>input, .stTextArea>div>textarea,
        .stSelectbox, .stMultiSelect { background-color: #ffffff !important; color: #0b1220 !important; border: 1px solid #e6e6e6 !important; }

        /* Buttons */
        .stButton>button { background-color: #f3f4f6 !important; color: #0b1220 !important; border: 1px solid #d1d5db !important; }

        /* Expander and containers */
        .stExpander, .st-expander { background-color: transparent !important; color: #0b1220 !important; }
        .stSidebar, .css-1d391kg { background-color: #ffffff !important; color: #0b1220 !important; }

        /* Placeholders, small text */
        small, .stCaption, .stMetric { color: #374151 !important; }

        /* Links */
        a { color: #1d4ed8 !important; }
        </style>
        """, unsafe_allow_html=True)

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

# --- new callbacks to avoid accidental page changes / key collisions ---
def _check_action():
    inp = st.session_state.get("check_user_input", "").strip()
    if not inp:
        st.session_state["_check_warning"] = True
        return
    result, proba = predict_spam(inp)
    st.session_state["last_mail"] = inp
    st.session_state["last_result"] = result
    # store plain list so session_state is serializable
    st.session_state["last_proba"] = list(proba)
    # append history as (message, label) and persist
    entry = (inp, result)  # (text, "Spam" / "Ham")
    st.session_state["users"][st.session_state["username"]]["history"].append(entry)
    save_users(st.session_state["users"])
    st.session_state["_checked"] = True
    st.session_state.pop("_check_warning", None)
    # also keep last label for UI
    st.session_state["last_label"] = result

def _ask_action():
    followup = st.session_state.get("ask_followup", "").strip()
    if st.session_state.get("last_mail", "") == "":
        st.session_state["_ask_info"] = "start_by_check"
        return
    if followup == "":
        st.session_state["_ask_info"] = "empty_question"
        return

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

    # ensure theme CSS can't override the inline color by using !important
    answer_colored = f'<p style="color:{color} !important;">{answer}</p>'
    st.session_state["_ask_response"] = answer_colored
    st.session_state["_ask_info"] = None
    st.session_state["_asked"] = True

def main_app():
    # guard: ensure logged in
    if not st.session_state.get("logged_in", False):
        st.session_state["page"] = "login"
        return

    # load model once
    load_model_and_vectorizer()
    st.title("🤖 AI-Based Spam Mail & Message Detector with Awareness Chatbot")
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
            # raw history (may contain legacy plain strings or tuples)
            history = st.session_state["users"][st.session_state["username"]]["history"]

            # normalize history into list of (text, label)
            normalized = []
            changed = False
            for item in history:
                if isinstance(item, tuple) and len(item) == 2:
                    normalized.append(item)
                elif isinstance(item, list) and len(item) >= 2:
                    normalized.append((item[0], item[1]))
                    changed = True
                elif isinstance(item, str):
                    # re-classify legacy entries
                    lbl, _ = predict_spam(item)
                    normalized.append((item, lbl))
                    changed = True
                else:
                    # fallback: convert to string and classify
                    text = str(item)
                    try:
                        lbl, _ = predict_spam(text)
                    except Exception:
                        lbl = "Unknown"
                    normalized.append((text, lbl))
                    changed = True

            # if we normalized anything, persist back to session and disk
            if changed:
                st.session_state["users"][st.session_state["username"]]["history"] = normalized
                save_users(st.session_state["users"])
                history = normalized
            else:
                history = normalized

            # counts
            spam_count = sum(1 for _, lbl in history if lbl == "Spam")
            ham_count = sum(1 for _, lbl in history if lbl == "Ham")
            total_count = len(history)
            st.write(f"Total: {total_count}  —  Spam: {spam_count}  —  Ham: {ham_count}")

            # filter selector
            filt = st.radio("Show", ["All", "Spam", "Ham"], index=0, key="history_filter")

            # display most recent first
            items = list(reversed(history))
            if filt == "Spam":
                items = [it for it in items if it[1] == "Spam"]
            elif filt == "Ham":
                items = [it for it in items if it[1] == "Ham"]

            if items:
                for text, lbl in items[:20]:
                    color = "red" if lbl == "Spam" else ("green" if lbl == "Ham" else "gray")
                    # add !important to prevent theme from overriding inline color
                    st.markdown(f'<p style="color:{color} !important;margin:4px 0;"><b>{lbl}:</b> {text}</p>', unsafe_allow_html=True)
            else:
                st.write("No chat history for this category.")
    with col5:
        with st.expander("👤 Profile"):
            profile_page()

    st.markdown("---")

    # CHECK form: explicit key for text area and use on_click callback
    with st.form("check_form"):
        st.text_area("Paste suspicious mail/message here:", height=120, key="check_user_input")
        st.form_submit_button("CHECK", on_click=_check_action)

    # show check results if present
    if st.session_state.pop("_check_warning", False):
        st.warning("⚠ Please enter a message.")
    if st.session_state.pop("_checked", False):
        # read stored result/proba
        result = st.session_state.get("last_result", "")
        proba = st.session_state.get("last_proba", [0.0, 0.0])
        ham_confidence = round(proba[0]*100, 2)
        spam_confidence = round(proba[1]*100, 2)
        if result == "Ham":
            # use !important so theme CSS doesn't override color
            bot_reply = f'<p style="color:green !important;">✅ This message seems <b>safe (Ham)</b>.<br>Confidence: {ham_confidence}%</p>'
        else:
            bot_reply = f'<p style="color:red !important;">🚨 This message seems <b>Spam</b>.<br>Confidence: {spam_confidence}%</p>'
        st.markdown(bot_reply, unsafe_allow_html=True)
        st.session_state["chat_history"].append(("Bot", bot_reply))

    st.markdown("### 💭 Chat Conversation")

    # ASK form: explicit key and callback to avoid accidental collisions
    with st.form("ask_form"):
        st.text_input("Ask about this message (e.g., Is it safe? What scam type?)", key="ask_followup")
        st.form_submit_button("Ask Bot", on_click=_ask_action)

    # show ask response / messages
    if st.session_state.get("_ask_info") == "start_by_check":
        st.info("⚠ Start by checking a suspicious message above.")
        st.session_state.pop("_ask_info", None)
    elif st.session_state.get("_ask_info") == "empty_question":
        st.info("⚠ Please enter a question for the bot.")
        st.session_state.pop("_ask_info", None)
    elif resp := st.session_state.pop("_ask_response", None):
        st.markdown(resp, unsafe_allow_html=True)
        st.session_state["chat_history"].append(("Bot", resp)) 

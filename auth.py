"""
FlowIndia — Lightweight in-memory auth.

For the demo we don't need a real DB. Users are stored in
st.session_state during the session. Passwords are SHA-256 hashed
(not bcrypt) — strictly demo-grade. For production you'd swap this
out for proper auth (Auth0, Firebase, or your own bcrypt + Postgres).
"""
import hashlib
import streamlit as st


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def init_auth_state():
    """Set up session-state defaults on first load."""
    if "users" not in st.session_state:
        # demo seed account so judges/testers don't have to sign up
        st.session_state.users = {
            "demo@flowindia.app": {
                "name": "Sreekar Yeduru",
                "phone": "+91 98xxxxxxxx",
                "area": "Whitefield",
                "pw_hash": _hash("demo123"),
            }
        }
    if "current_user" not in st.session_state:
        st.session_state.current_user = None


def login(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    user = st.session_state.users.get(email)
    if not user:
        return False, "No account with that email. Sign up instead?"
    if user["pw_hash"] != _hash(password):
        return False, "Wrong password."
    st.session_state.current_user = {"email": email, **user}
    return True, "Welcome back!"


def signup(name: str, email: str, phone: str, password: str, area: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not name or not email or not password:
        return False, "Name, email, and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if email in st.session_state.users:
        return False, "An account with this email already exists."
    st.session_state.users[email] = {
        "name": name,
        "phone": phone,
        "area": area,
        "pw_hash": _hash(password),
    }
    st.session_state.current_user = {"email": email, "name": name, "phone": phone, "area": area}
    return True, "Account created. Welcome to FlowIndia!"


def logout():
    st.session_state.current_user = None


def is_logged_in() -> bool:
    return st.session_state.get("current_user") is not None


def render_auth_screen():
    """Full-page login/signup UI. Returns True if a user is now logged in."""
    init_auth_state()
    if is_logged_in():
        return True

    st.markdown(
        """
        <style>
        .auth-hero { text-align: center; padding: 1rem 0 2rem; }
        .auth-logo { font-size: 42px; font-weight: 600; color: #FBBF24;
                     letter-spacing: -1px; margin-bottom: 0; }
        .auth-tagline { color: #888; font-size: 14px; margin-top: 4px; }
        </style>
        <div class="auth-hero">
            <p class="auth-logo">⚡ FlowIndia</p>
            <p class="auth-tagline">Smarter mobility for India · Bengaluru pilot</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_main, col_right = st.columns([1, 2, 1])
    with col_main:
        tab_login, tab_signup = st.tabs(["🔐  Log in", "✨  Sign up"])

        with tab_login:
            st.markdown("##### Welcome back")
            st.caption("Use **demo@flowindia.app** / **demo123** for a quick test login")
            email = st.text_input("Email", key="li_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="li_pw",
                                     placeholder="••••••••")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Log in →", use_container_width=True, type="primary",
                             key="login_btn"):
                    ok, msg = login(email, password)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with c2:
                if st.button("Quick demo login", use_container_width=True,
                             key="demo_btn"):
                    ok, _ = login("demo@flowindia.app", "demo123")
                    if ok:
                        st.rerun()

        with tab_signup:
            st.markdown("##### Create your FlowIndia account")
            name = st.text_input("Full name", key="su_name", placeholder="Sreekar Yeduru")
            su_email = st.text_input("Email", key="su_email")
            phone = st.text_input("Phone", key="su_phone", placeholder="+91 98xxx xxxxx")
            su_pw = st.text_input("Password", type="password", key="su_pw",
                                  placeholder="At least 6 characters")
            area = st.selectbox("Home area in Bengaluru", [
                "Whitefield", "Koramangala", "Indiranagar", "HSR Layout",
                "Electronic City", "Jayanagar", "Hebbal", "Marathahalli",
                "BTM Layout", "Banashankari", "JP Nagar", "Yelahanka", "Sarjapur",
            ], key="su_area")
            agree = st.checkbox(
                "I agree to FlowIndia's terms and to share anonymised trip "
                "data to help reduce city congestion.",
                value=True, key="su_tos",
            )
            if st.button("Create account →", use_container_width=True, type="primary",
                         key="signup_btn"):
                if not agree:
                    st.error("You must agree to the terms to continue.")
                else:
                    ok, msg = signup(name, su_email, phone, su_pw, area)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    return False

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st


MODEL_PATH = Path("models/fraud_model.joblib")
METRICS_PATH = Path("reports/metrics.json")
DATA_PATH = Path("data/insurance_claims.csv")
USERS_PATH = Path("data/users.json")
ACTIVITY_LOG_PATH = Path("data/activity_log.json")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "insurance_portal")


FEATURE_COLUMNS = [
    "insurance_type",
    "age",
    "vehicle_age",
    "claim_amount",
    "annual_premium",
    "incidents",
    "witness_count",
    "policy_type",
    "collision_type",
    "police_report",
]

INSURANCE_OPTIONS = ["auto", "health", "property"]
POLICY_OPTIONS = ["basic", "standard", "premium"]
COLLISION_OPTIONS = ["rear", "side", "front", "none"]
POLICE_OPTIONS = ["yes", "no"]
ROLE_OPTIONS = ["admin", "analytics"]


def load_css():
    with open("style/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def normalize_users(data: dict) -> dict:
    users = {}
    for username, payload in data.items():
        if isinstance(payload, str):
            users[username] = {"password_hash": payload, "role": "analytics"}
        elif isinstance(payload, dict):
            password_hash = payload.get("password_hash")
            if not password_hash and "password" in payload:
                password_hash = payload.get("password")
            role = str(payload.get("role", "analytics")).lower()
            if role not in ROLE_OPTIONS:
                role = "analytics"
            if isinstance(password_hash, str) and password_hash:
                users[username] = {"password_hash": password_hash, "role": role}
    return users


def get_mongo_collections():
    try:
        from pymongo import MongoClient
    except Exception:
        return None, None

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        db = client[MONGO_DB_NAME]
        return db["users"], db["activity_logs"]
    except Exception:
        return None, None


def seed_users_from_json(users_col) -> None:
    if users_col is None or users_col.count_documents({}) > 0 or not USERS_PATH.exists():
        return
    try:
        raw = json.loads(USERS_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return
        users = normalize_users(raw)
        docs = [{"username": u, **payload} for u, payload in users.items()]
        if docs:
            users_col.insert_many(docs, ordered=False)
    except Exception:
        pass


def seed_activity_from_json(activity_col) -> None:
    if activity_col is None or activity_col.count_documents({}) > 0 or not ACTIVITY_LOG_PATH.exists():
        return
    try:
        raw = json.loads(ACTIVITY_LOG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            docs = [row for row in raw if isinstance(row, dict)]
            if docs:
                activity_col.insert_many(docs, ordered=False)
    except Exception:
        pass


def load_users() -> dict:
    users_col, _ = get_mongo_collections()
    if users_col is not None:
        seed_users_from_json(users_col)
        users = {}
        for doc in users_col.find({}, {"_id": 0}):
            username = str(doc.get("username", "")).strip().lower()
            password_hash = doc.get("password_hash")
            role = str(doc.get("role", "analytics")).lower()
            if not username or not isinstance(password_hash, str):
                continue
            if role not in ROLE_OPTIONS:
                role = "analytics"
            users[username] = {"password_hash": password_hash, "role": role}
        return users

    if not USERS_PATH.exists():
        return {}
    try:
        raw = json.loads(USERS_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        users = normalize_users(raw)
        if users != raw:
            save_users(users)
        return users
    except json.JSONDecodeError:
        return {}


def save_users(users: dict) -> None:
    users_col, _ = get_mongo_collections()
    if users_col is not None:
        try:
            from pymongo import UpdateOne

            normalized = normalize_users(users)
            keep_usernames = list(normalized.keys())
            users_col.delete_many({"username": {"$nin": keep_usernames}})
            ops = [
                UpdateOne(
                    {"username": username},
                    {"$set": {"username": username, **payload}},
                    upsert=True,
                )
                for username, payload in normalized.items()
            ]
            if ops:
                users_col.bulk_write(ops, ordered=False)
            return
        except Exception:
            pass

    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def init_auth_state() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("role", "")
    st.session_state.setdefault("latest_fraud_probability", None)


def register_user(username: str, password: str, confirm_password: str, role: str) -> tuple[bool, str]:
    username = username.strip().lower()
    role = role.strip().lower()

    if not username:
        return False, "Username is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if password != confirm_password:
        return False, "Passwords do not match."
    if role not in ROLE_OPTIONS:
        return False, "Please select a valid role."

    users = load_users()
    if username in users:
        return False, "Username already exists."

    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
    }
    save_users(users)
    return True, "Registration successful. You can now login."


def login_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    users = load_users()
    user = users.get(username)

    if not user:
        return False, "Invalid username or password."

    if user["password_hash"] != hash_password(password):
        return False, "Invalid username or password."

    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = user["role"]
    return True, "Login successful."


def logout() -> None:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.rerun()


def load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def load_metrics() -> dict:
    if not METRICS_PATH.exists():
        return {}
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_activity_logs() -> list[dict]:
    _, activity_col = get_mongo_collections()
    if activity_col is not None:
        seed_activity_from_json(activity_col)
        logs = []
        for doc in activity_col.find({}, {"_id": 0}):
            if isinstance(doc, dict):
                logs.append(doc)
        return logs

    if not ACTIVITY_LOG_PATH.exists():
        return []
    try:
        raw = json.loads(ACTIVITY_LOG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [row for row in raw if isinstance(row, dict)]
    except json.JSONDecodeError:
        return []
    return []


def save_activity_logs(logs: list[dict]) -> None:
    _, activity_col = get_mongo_collections()
    if activity_col is not None:
        try:
            activity_col.delete_many({})
            docs = [row for row in logs if isinstance(row, dict)]
            if docs:
                activity_col.insert_many(docs, ordered=False)
            return
        except Exception:
            pass

    ACTIVITY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVITY_LOG_PATH.write_text(json.dumps(logs, indent=2), encoding="utf-8")


def add_activity_log(
    action: str,
    insurance_type: str,
    record_count: int,
    details: str,
    fraud_count: int | None = None,
) -> None:
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": st.session_state.get("username", "unknown"),
        "role": st.session_state.get("role", "unknown"),
        "action": action,
        "insurance_type": insurance_type,
        "record_count": int(record_count),
        "details": details,
    }
    if fraud_count is not None:
        row["fraud_count"] = int(fraud_count)

    _, activity_col = get_mongo_collections()
    if activity_col is not None:
        try:
            activity_col.insert_one(row)
            total = activity_col.count_documents({})
            overflow = total - 2000
            if overflow > 0:
                old_docs = activity_col.find({}, {"_id": 1}).sort("timestamp", 1).limit(overflow)
                old_ids = [doc["_id"] for doc in old_docs]
                if old_ids:
                    activity_col.delete_many({"_id": {"$in": old_ids}})
            return
        except Exception:
            pass

    logs = load_activity_logs()
    logs.append(row)
    save_activity_logs(logs[-2000:])


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return df[FEATURE_COLUMNS].copy()


def score_dataframe(model, df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    clean = ensure_columns(df)
    proba = model.predict_proba(clean)[:, 1]
    pred = (proba >= threshold).astype(int)

    output = clean.copy()
    output["fraud_probability"] = proba.round(4)
    output["predicted_fraud"] = pred
    output["risk_level"] = pd.cut(
        output["fraud_probability"],
        bins=[-0.001, 0.2, 0.5, 1.0],
        labels=["Low", "Medium", "High"],
    )
    return output


def render_auth_page() -> None:
    left, center, right = st.columns([1.2, 2, 1.2])
    with center:
        st.markdown('<div class="auth-page">', unsafe_allow_html=True)
        st.markdown("<h1>Insurance Portal</h1>", unsafe_allow_html=True)
        st.markdown("<p>Login or register with a role to access modules.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                ok, message = login_user(username, password)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_register:
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=True):
                username = st.text_input("New Username")
                password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                role = st.selectbox("Select Module Role", options=ROLE_OPTIONS, index=1)
                submitted = st.form_submit_button("Register", use_container_width=True)

            if submitted:
                ok, message = register_user(username, password, confirm_password, role)
                if ok:
                    st.success(message)
                else:
                    st.error(message)
            st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar(metrics: dict, threshold: float) -> None:
    with st.sidebar:
        user_initial = (st.session_state["username"][:1] or "U").upper()
        st.markdown(
            f"""
            <div class="sidebar-user-brand">
                <div class="sidebar-user-avatar">{user_initial}</div>
                <div class="sidebar-user-meta">
                    <div class="sidebar-user-name">{st.session_state['username']}</div>
                    <div class="sidebar-user-role">{st.session_state['role']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.subheader("Account")
        st.write(f"User: `{st.session_state['username']}`")
        st.write(f"Role: `{st.session_state['role']}`")
        if st.button("Logout", use_container_width=True):
            logout()

        st.divider()
        st.subheader("Model")
        st.metric("Threshold", f"{threshold:.3f}")
        st.metric("Precision", f"{metrics.get('precision', 0.0):.3f}")
        st.metric("Recall", f"{metrics.get('recall', 0.0):.3f}")
        st.metric("ROC-AUC", f"{metrics.get('roc_auc', 0.0):.3f}")


def render_prediction_form(model, threshold: float) -> None:
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.subheader("Analytics Module")
    st.caption("Select insurance type and enter required details only.")

    insurance_type = st.selectbox(
        "Insurance Type",
        INSURANCE_OPTIONS,
        index=0,
        key="insurance_type_selector",
    )

    with st.form("single_claim_form"):
        st.markdown(f"#### Required Details for `{insurance_type.title()}` Insurance")

        # Defaults keep model feature schema complete while the UI shows only relevant fields.
        age = 35
        vehicle_age = 0
        claim_amount = 4000.0
        annual_premium = 2500.0
        incidents = 0
        witness_count = 0
        policy_type = "standard"
        collision_type = "none"
        police_report = "no"

        if insurance_type == "auto":
            st.info("Auto required: age, vehicle age, claim amount, annual premium, incidents, witness count, policy type, collision type, police report.")
            col1, col2, col3 = st.columns(3)
            with col1:
                age = st.number_input("Customer Age", min_value=18, max_value=100, value=35, step=1)
                vehicle_age = st.number_input("Vehicle Age", min_value=0, max_value=50, value=5, step=1)
                incidents = st.number_input("Previous Incidents", min_value=0, max_value=20, value=1, step=1)
            with col2:
                claim_amount = st.number_input("Claim Amount", min_value=0.0, value=4000.0, step=100.0)
                annual_premium = st.number_input("Annual Premium", min_value=0.0, value=2500.0, step=100.0)
                witness_count = st.number_input("Witness Count", min_value=0, max_value=10, value=1, step=1)
            with col3:
                policy_type = st.selectbox("Policy Type", POLICY_OPTIONS, index=1)
                collision_type = st.selectbox("Collision Type", COLLISION_OPTIONS, index=0)
                police_report = st.selectbox("Police Report", POLICE_OPTIONS, index=0)

        elif insurance_type == "health":
            st.info("Health required: age, claim amount, annual premium, incidents, policy type.")
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Patient Age", min_value=0, max_value=100, value=40, step=1)
                claim_amount = st.number_input("Medical Claim Amount", min_value=0.0, value=3000.0, step=100.0)
                annual_premium = st.number_input("Annual Premium", min_value=0.0, value=2000.0, step=100.0)
            with col2:
                incidents = st.number_input("Previous Claims", min_value=0, max_value=20, value=1, step=1)
                policy_type = st.selectbox("Policy Type", POLICY_OPTIONS, index=1)

        else:
            st.info("Property required: owner age, claim amount, annual premium, incidents, witness count, policy type, police report.")
            col1, col2, col3 = st.columns(3)
            with col1:
                age = st.number_input("Owner Age", min_value=18, max_value=100, value=42, step=1)
                claim_amount = st.number_input("Property Claim Amount", min_value=0.0, value=6000.0, step=100.0)
            with col2:
                annual_premium = st.number_input("Annual Premium", min_value=0.0, value=3200.0, step=100.0)
                incidents = st.number_input("Previous Incidents", min_value=0, max_value=20, value=1, step=1)
            with col3:
                witness_count = st.number_input("Witness Count", min_value=0, max_value=10, value=0, step=1)
                policy_type = st.selectbox("Policy Type", POLICY_OPTIONS, index=1)
                police_report = st.selectbox("Police Report", POLICE_OPTIONS, index=0)

        submitted = st.form_submit_button("Predict", use_container_width=True)

    if submitted:
        row = pd.DataFrame(
            [
                {
                    "insurance_type": insurance_type,
                    "age": age,
                    "vehicle_age": vehicle_age,
                    "claim_amount": claim_amount,
                    "annual_premium": annual_premium,
                    "incidents": incidents,
                    "witness_count": witness_count,
                    "policy_type": policy_type,
                    "collision_type": collision_type,
                    "police_report": police_report,
                }
            ]
        )

        scored = score_dataframe(model, row, threshold)
        prob = float(scored.loc[0, "fraud_probability"])
        pred = int(scored.loc[0, "predicted_fraud"])
        prediction_label = "Fraud" if pred == 1 else "Claim"
        st.session_state["latest_fraud_probability"] = prob

        add_activity_log(
            action="single_prediction",
            insurance_type=insurance_type,
            record_count=1,
            details=f"result={prediction_label}, probability={prob:.4f}",
            fraud_count=pred,
        )

        if pred == 1:
            st.markdown(
                f'<div class="result-fraud"><b>Prediction:</b> Fraud<br><b>Fraud Probability:</b> {prob:.2%}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="result-claim"><b>Prediction:</b> Claim (Valid)<br><b>Fraud Probability:</b> {prob:.2%}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


def render_fraud_risk_gauge() -> None:
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.subheader("Fraud Risk Gauge Chart")
    prob = st.session_state.get("latest_fraud_probability")

    if prob is None:
        st.info("Run a single prediction to view the fraud risk gauge.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    value = max(0, min(100, int(round(prob * 100))))
    if value >= 70:
        gauge_color = "#dc2626"
        risk_text = "High Risk"
    elif value >= 35:
        gauge_color = "#d97706"
        risk_text = "Medium Risk"
    else:
        gauge_color = "#16a34a"
        risk_text = "Low Risk"

    st.markdown(
        f"""
        <div class="gauge-wrapper">
            <div class="gauge-ring" style="--value:{value}; --gauge-color:{gauge_color};">
                <div class="gauge-center">
                    <div class="gauge-value">{value}%</div>
                    <div class="gauge-label">{risk_text}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_claim_statistics_charts() -> None:
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.subheader("Claim Statistics Charts")

    if not DATA_PATH.exists():
        st.info("No local dataset found for charting.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    try:
        df = pd.read_csv(DATA_PATH)
        if df.empty:
            st.info("Dataset is empty.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        col1, col2 = st.columns(2)

        with col1:
            st.caption("Claims by Insurance Type")
            type_counts = df["insurance_type"].value_counts().rename_axis("insurance_type").to_frame("count")
            st.bar_chart(type_counts)

        with col2:
            st.caption("Fraud vs Valid Claims")
            if "is_fraud" in df.columns:
                outcome = df["is_fraud"].map({1: "Fraud", 0: "Valid Claim"}).value_counts()
                outcome_df = outcome.rename_axis("claim_result").to_frame("count")
                st.bar_chart(outcome_df)
            else:
                st.info("`is_fraud` column not found in dataset.")

        if "is_fraud" in df.columns:
            st.caption("Fraud Rate by Insurance Type")
            fraud_rate = (
                df.groupby("insurance_type", as_index=True)["is_fraud"]
                .mean()
                .mul(100)
                .round(2)
                .to_frame("fraud_rate_percent")
            )
            st.bar_chart(fraud_rate)
    except Exception as exc:
        st.error(f"Could not build claim statistics charts: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)


def render_admin_module() -> None:
    users = load_users()
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.subheader("Admin Module")
    st.caption("Manage user overview and inspect latest records.")

    if users:
        user_rows = [{"username": u, "role": info["role"]} for u, info in sorted(users.items())]
        st.write("Registered Users")
        st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No registered users yet.")

    if DATA_PATH.exists():
        st.write("Sample Data Preview")
        st.dataframe(pd.read_csv(DATA_PATH).head(15), use_container_width=True)
    else:
        st.info("No local dataset found. Run `python src/generate_sample_data.py` first.")

    st.write("Analytics Activity History")
    activity_logs = load_activity_logs()
    if activity_logs:
        history_df = pd.DataFrame(activity_logs)
        history_df = history_df.sort_values("timestamp", ascending=False).reset_index(drop=True)
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.info("No analytics activity found yet.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_analytics_module(model, threshold: float) -> None:
    tab1, tab2 = st.tabs(["Single Prediction", "Batch CSV"])

    with tab1:
        render_prediction_form(model, threshold)
        render_fraud_risk_gauge()
        render_claim_statistics_charts()

    with tab2:
        st.markdown('<div class="module-card">', unsafe_allow_html=True)
        st.subheader("Batch Prediction")
        st.write("Upload a CSV with required columns:")
        st.code(", ".join(FEATURE_COLUMNS), language="text")

        uploaded = st.file_uploader("Upload claims CSV", type=["csv"])
        if uploaded is not None:
            try:
                df_in = pd.read_csv(uploaded)
                scored = score_dataframe(model, df_in, threshold)
                scored["prediction_label"] = scored["predicted_fraud"].map({1: "Fraud", 0: "Claim"})
                st.success(f"Scored {len(scored)} records.")
                st.dataframe(scored, use_container_width=True)

                add_activity_log(
                    action="batch_prediction",
                    insurance_type="mixed",
                    record_count=len(scored),
                    details=f"file={uploaded.name}",
                    fraud_count=int(scored["predicted_fraud"].sum()),
                )

                csv_bytes = scored.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Results",
                    data=csv_bytes,
                    file_name="scored_claims.csv",
                    mime="text/csv",
                )
            except Exception as exc:
                st.error(str(exc))

        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Insurance Fraud Portal", page_icon=":shield:", layout="wide")
    load_css()
    init_auth_state()

    if not st.session_state["authenticated"]:
        render_auth_page()
        return

    model = load_model()
    metrics = load_metrics()
    threshold = float(metrics.get("threshold", 0.5))

    if model is None:
        st.error("Model not found. Run `python src/train.py` first to generate `models/fraud_model.joblib`.")
        st.stop()

    st.markdown(
        """
        <div class="top-brand-toolbar">
            <div class="brand-mark brand-mark--header">
                <div class="brand-icon">IG</div>
                <div class="brand-text">
                    <h1>InsuraGuard</h1>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="header-card">
            <div class="header-shell">
                <div class="header-left">
                    <h2>Insurance Fraud Detection System</h2>
                    <p>Role-based modules with clean claim analysis workflow.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_sidebar(metrics, threshold)

    role = st.session_state["role"]
    if role == "admin":
        render_admin_module()
    else:
        render_analytics_module(model, threshold)


if __name__ == "__main__":
    main()

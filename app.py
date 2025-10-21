import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
import ssl
import io
import os
from datetime import datetime
import time
import random

# ------------------------
# AutoRecruit-SA (single-file Streamlit app)
# ------------------------
# Features:
# - Upload recruiter list (CSV or Excel)
# - Upload CV (PDF/DOCX)
# - Compose message template with placeholders (e.g., {AgencyName}, {City})
# - Configure SMTP settings (Gmail/Outlook/Custom)
# - Send personalized emails with attachment
# - Log sent emails to a local CSV (logs/application_log.csv)
#
# Run: pip install streamlit pandas openpyxl
# Then: streamlit run AutoRecruit-SA_app.py


st.set_page_config(page_title="AutoRecruit-SA", layout="wide")

# Ensure logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

LOG_PATH = "logs/application_log.csv"

# Initialize session state
if "recruiters_df" not in st.session_state:
    st.session_state.recruiters_df = None
if "cv_bytes" not in st.session_state:
    st.session_state.cv_bytes = None
if "cv_filename" not in st.session_state:
    st.session_state.cv_filename = None
if "message_template" not in st.session_state:
    st.session_state.message_template = (
        "Dear {AgencyName} Recruitment Team,\n\n"
        "My name is Aviwe Matoti, a postgraduate student in Business and Financial Analytics. "
        "I have experience in data analytics, financial modeling, and data-driven decision-making.\n\n"
        "Please find my CV attached for your consideration.\n\n"
        "Kind regards,\n"
        "Aviwe Matoti\n"
        "Bloemfontein, South Africa\n"
        "📧 your.email@example.com\n"
        "📞 +27 71 000 0000\n"
    )
if "log_df" not in st.session_state:
    if os.path.exists(LOG_PATH):
        try:
            st.session_state.log_df = pd.read_csv(LOG_PATH)
        except Exception:
            st.session_state.log_df = pd.DataFrame(
                columns=["Timestamp", "Agency", "Email", "Status", "Error", "MessagePreview"]
            )
    else:
        st.session_state.log_df = pd.DataFrame(
            columns=["Timestamp", "Agency", "Email", "Status", "Error", "MessagePreview"]
        )

# ------------------------
# Helper functions
# ------------------------

def load_recruiters(uploaded_file):
    """Load recruiters CSV or Excel into pandas DataFrame."""
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

    # Normalize expected columns
    expected_cols = ["AgencyName", "Email", "City", "Website", "Notes"]
    # Try to map common variations
    col_map = {}
    for col in df.columns:
        if col.lower() in ["agency", "agencyname", "recruiter", "company"]:
            col_map[col] = "AgencyName"
        if "email" in col.lower():
            col_map[col] = "Email"
        if col.lower() in ["city", "location"]:
            col_map[col] = "City"
        if "web" in col.lower():
            col_map[col] = "Website"

    df = df.rename(columns=col_map)
    # Ensure columns exist
    for c in expected_cols:
        if c not in df.columns:
            df[c] = ""

    # Drop rows without email
    df = df[df["Email"].notna() & (df["Email"].astype(str).str.strip() != "")]
    df = df.reset_index(drop=True)
    return df


def save_log_row(agency, email, status, error, preview):
    ts = datetime.now().isoformat(sep=" ", timespec="seconds")
    row = {"Timestamp": ts, "Agency": agency, "Email": email, "Status": status, "Error": error, "MessagePreview": preview}
    st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([row])], ignore_index=True)
    # Save to disk
    try:
        st.session_state.log_df.to_csv(LOG_PATH, index=False)
    except Exception as e:
        st.warning(f"Could not save log to disk: {e}")


# Basic email send function using smtplib

def send_email_smtp(smtp_host, smtp_port, smtp_user, smtp_password, use_tls, to_email, subject, body_text, attachment_bytes=None, attachment_filename=None):
    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body_text)

    if attachment_bytes is not None and attachment_filename is not None:
        maintype = "application"
        subtype = "octet-stream"
        msg.add_attachment(attachment_bytes, maintype=maintype, subtype=subtype, filename=attachment_filename)

    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=60)
        if use_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)


# ------------------------
# Streamlit UI
# ------------------------

st.title("AutoRecruit-SA — Streamlined Recruiter Outreach")
st.markdown(
    "Automate polite, personalized outreach to South African recruitment agencies.\n"
    "Upload a CSV/Excel of agencies, upload your CV, craft a message template, and send.\n"
    "**Security note:** Your email credentials are used only for the active session and not stored.**"
)

# Sidebar for navigation
page = st.sidebar.radio("Navigation", ["Home", "Upload & Template", "Send Applications", "Logs & Export"])

# ------------------------
# Home
# ------------------------
if page == "Home":
    st.header("Welcome, Aviwe 🎯")
    st.write("This app will help you contact recruiting agencies in a controlled, respectful, and trackable way.")
    st.subheader("Quick Start")
    st.markdown(
        "1. Go to **Upload & Template** to upload your recruiter list and CV and tweak your message.\n"
        "2. Go to **Send Applications** to configure SMTP and send messages.\n"
        "3. Check **Logs & Export** to review and export the history."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Agencies loaded", len(st.session_state.recruiters_df) if st.session_state.recruiters_df is not None else 0)
    with col2:
        sent = len(st.session_state.log_df[st.session_state.log_df["Status"] == "SENT"]) if not st.session_state.log_df.empty else 0
        st.metric("Emails sent", sent)
    with col3:
        failures = len(st.session_state.log_df[st.session_state.log_df["Status"] == "FAILED"]) if not st.session_state.log_df.empty else 0
        st.metric("Failures", failures)

    st.info("Recommended: send in small batches (10-20 per day) with randomized delays to avoid spam flags.")

# ------------------------
# Upload & Template
# ------------------------
elif page == "Upload & Template":
    st.header("1) Upload recruiter list and CV")
    st.write("Upload a CSV or Excel file containing at least an Email column. Helpful columns: AgencyName, Email, City, Website.")

    uploaded = st.file_uploader("Upload recruiter CSV or Excel", type=["csv", "xlsx", "xls"], key="recruiter_upload")
    if uploaded is not None:
        df = load_recruiters(uploaded)
        if df is not None:
            st.session_state.recruiters_df = df
            st.success(f"Loaded {len(df)} recruiters (rows with empty emails dropped).")

    if st.session_state.recruiters_df is not None:
        st.subheader("Preview recruiters")
        st.dataframe(st.session_state.recruiters_df.head(200))

    st.write("\n---\n")
    st.header("2) Upload your CV (PDF/DOCX)")
    cv_file = st.file_uploader("Upload CV to attach to emails", type=["pdf", "doc", "docx"], key="cv_upload")
    if cv_file is not None:
        bytes_data = cv_file.read()
        st.session_state.cv_bytes = bytes_data
        st.session_state.cv_filename = cv_file.name
        st.success(f"Uploaded CV: {cv_file.name} ({len(bytes_data)} bytes)")

    st.write("\n---\n")
    st.header("3) Message template")
    st.write("Use placeholders like {AgencyName}, {City}, {Website}. They will be replaced per-row.")
    message = st.text_area("Message template", value=st.session_state.message_template, height=300)
    st.session_state.message_template = message

    st.subheader("Preview message for first recruiter (if available)")
    if st.session_state.recruiters_df is not None and not st.session_state.recruiters_df.empty:
        first = st.session_state.recruiters_df.iloc[0]
        preview = message.format(**{k: first.get(k, "") for k in ["AgencyName", "City", "Website"]})
        st.code(preview)
    else:
        st.write("Upload a recruiter list to preview message.")

# ------------------------
# Send Applications
# ------------------------
elif page == "Send Applications":
    st.header("Send Applications — SMTP Settings & Send Controls")

    if st.session_state.recruiters_df is None:
        st.warning("Upload a recruiter list first in the 'Upload & Template' page.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            provider = st.selectbox("Email provider", ["Gmail (smtp.gmail.com)", "Outlook/Office365 (smtp.office365.com)", "Custom SMTP"], index=0)
            if provider.startswith("Gmail"):
                smtp_host = "smtp.gmail.com"
                smtp_port = 587
                use_tls = True
            elif provider.startswith("Outlook"):
                smtp_host = "smtp.office365.com"
                smtp_port = 587
                use_tls = True
            else:
                smtp_host = st.text_input("SMTP host", value="smtp.example.com")
                smtp_port = st.number_input("SMTP port", value=587)
                use_tls = st.checkbox("Use TLS", value=True)

            smtp_user = st.text_input("Your email address (SMTP username)")
            smtp_password = st.text_input("SMTP password or app password", type="password")

        with col2:
            subject_template = st.text_input("Email subject template", value="Application: {AgencyName} - Candidate: Aviwe Matoti")
            batch_size = st.number_input("Batch size (how many recipients to send in one run)", min_value=1, max_value=500, value=20)
            delay_min = st.number_input("Min delay between emails (seconds)", value=5)
            delay_max = st.number_input("Max delay between emails (seconds)", value=12)
            follow_up_days = st.number_input("Default follow-up days (used later)", value=7)

        st.write("\n---\n")
        st.subheader("Recipients selection")
        recruiters = st.session_state.recruiters_df.copy()
        recruiters["Selected"] = True
        recruiters["PreviewMessage"] = recruiters.apply(lambda r: st.session_state.message_template.format(**{"AgencyName": r.get("AgencyName", ""), "City": r.get("City", ""), "Website": r.get("Website", "")}), axis=1)

        # Show a small editable table for selection
        st.write("You can filter the list before sending. Use the search box below to keep rows that match.")
        search = st.text_input("Filter recruiters (search across AgencyName, City, Email)")
        if search:
            mask = recruiters["AgencyName"].str.contains(search, case=False, na=False) | recruiters["City"].str.contains(search, case=False, na=False) | recruiters["Email"].str.contains(search, case=False, na=False)
            recruiters = recruiters[mask]

        st.write(f"Showing {len(recruiters)} recruiters to potentially send to.")
        st.dataframe(recruiters[["AgencyName", "Email", "City", "Website"]].head(300))

        start_send = st.button("Start sending")
        if start_send:
            if smtp_user.strip() == "" or smtp_password.strip() == "":
                st.error("Enter your SMTP credentials before sending.")
            elif st.session_state.cv_bytes is None:
                st.warning("You did not upload a CV. Emails will be sent without attachment. Continue?")

            total = len(recruiters)
            progress = st.progress(0)
            status_col = st.empty()

            sent_count = 0
            failed_count = 0

            # Loop through recipients up to the batch_size
            for idx, row in recruiters.head(batch_size).iterrows():
                agency = row.get("AgencyName", "")
                email = row.get("Email")
                preview_msg = st.session_state.message_template.format(**{"AgencyName": agency, "City": row.get("City", ""), "Website": row.get("Website", "")})
                subject = subject_template.format(**{"AgencyName": agency, "City": row.get("City", ""), "Website": row.get("Website", "")})

                # send
                success, error = send_email_smtp(
                    smtp_host=smtp_host,
                    smtp_port=int(smtp_port),
                    smtp_user=smtp_user,
                    smtp_password=smtp_password,
                    use_tls=use_tls,
                    to_email=email,
                    subject=subject,
                    body_text=preview_msg,
                    attachment_bytes=st.session_state.cv_bytes,
                    attachment_filename=st.session_state.cv_filename,
                )

                if success:
                    save_log_row(agency, email, "SENT", "", preview_msg[:1000])
                    sent_count += 1
                    status_col.write(f"Sent to {agency} <{email}> ✔️")
                else:
                    save_log_row(agency, email, "FAILED", error, preview_msg[:1000])
                    failed_count += 1
                    status_col.write(f"Failed to {agency} <{email}> ❌ — {error}")

                progress.progress(int(((idx + 1) / batch_size) * 100))

                # Delay
                delay = random.uniform(max(0, delay_min), max(delay_min, delay_max))
                time.sleep(delay)

            st.success(f"Finished sending run. Sent: {sent_count}, Failed: {failed_count}")

# ------------------------
# Logs & Export
# ------------------------
elif page == "Logs & Export":
    st.header("Logs & Export")

    df_logs = st.session_state.log_df
    st.write(f"Total records: {len(df_logs)}")
    if not df_logs.empty:
        st.dataframe(df_logs.tail(200))

        col1, col2 = st.columns(2)
        with col1:
            csv = df_logs.to_csv(index=False).encode("utf-8")
            st.download_button("Download logs as CSV", data=csv, file_name="application_log.csv", mime="text/csv")
        with col2:
            if st.button("Clear logs (this will delete local log file)"):
                try:
                    os.remove(LOG_PATH)
                except Exception:
                    pass
                st.session_state.log_df = pd.DataFrame(columns=df_logs.columns)
                st.success("Logs cleared.")
    else:
        st.info("No logs yet. Send some emails from the 'Send Applications' page.")


# ------------------------
# Footer / Tips
# ------------------------
st.sidebar.markdown("---")
st.sidebar.header("Tips & Next Steps")
st.sidebar.markdown(
    "- Start small: 10–20 contacts per day.\n"
    "- Use application-specific passwords (Gmail App Passwords or Outlook App Passwords) where possible.\n"
    "- Consider personalization: add a sentence referencing their specialty.\n"
    "- Next: we can add LinkedIn integration, AI-powered personalization, and automated follow-ups step by step."
)


# End of script


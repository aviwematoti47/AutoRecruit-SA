# AutoRecruit-SA  
**Founder & Developer:** Aviwe Matoti  

AutoRecruit-SA is a Streamlit-based automation app that helps South African job seekers contact multiple recruitment agencies efficiently and professionally.  

The app automates outreach by allowing users to upload recruiter contact lists, attach their CVs, and send personalized application emails securely — all while maintaining full control over message timing and logs.

---

##  Features

- 📁 Upload recruiter lists (CSV or Excel)
- 📎 Attach your CV (PDF/DOCX)
- ✉️ Create dynamic, personalized email templates with placeholders (`{AgencyName}`, `{City}`)
- 🔐 Secure email sending through Gmail, Outlook, or any SMTP service
- 🕒 Adjustable send delay to avoid spam detection
- 📊 Logging system with timestamps and delivery status
- 💾 Downloadable logs of all sent applications
- 🧠 Built for future AI and LinkedIn integration

---

## 🧩 Tech Stack

- **Frontend:** Streamlit  
- **Backend:** Python (pandas, smtplib, ssl, email.message)  
- **Data Handling:** pandas + openpyxl  
- **Logging:** CSV-based logging system  

---
python -m venv venv
source venv/bin/activate     # (Mac/Linux)
venv\Scripts\activate        # (Windows)


# EduManage — College Admission Management System

![EduManage Banner](https://img.shields.io/badge/EduManage-College%20Admission%20System-6558e8?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-black?style=for-the-badge&logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Render%20Persistent-336791?style=for-the-badge&logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

A full-stack, production-grade **College Admission Management System** designed for modern higher education institutions. Features a public student admission portal and a comprehensive administrative management dashboard backed by persistent database storage (PostgreSQL on Render, SQLite locally).

---

## 🌟 Key Features

### 🎓 1. Public Student Admission Portal
* **College Overview:** Highlights institutional achievements, UGC recognition, NAAC accreditation, campus infrastructure, and faculty credentials.
* **Interactive Academic Programmes:** Dynamic degree catalogue showcasing course code, duration, seat quota, annual tuition fee, and eligibility requirements.
* **Direct Course Selection:** One-click course selection that smoothly scrolls to the application form with pre-selected programme details.
* **Admission Process Guide:** Transparent 4-step flowchart explaining guidelines, document checklists, and key admission deadlines.
* **Online Admission Application Form:**
  * Candidate personal details (name, date of birth, gender, parent/guardian info).
  * Contact information (email, 10-digit mobile, address, city, state, PIN code).
  * Academic qualifications (exam, board/university, passing year, score/percentage).
  * Robust client-side and server-side validation.
  * Duplicate application prevention (prevents multiple active submissions for same student and course).
* **Instant Application Number:** Auto-generates a unique formatted application ID (e.g. `EDU-2026-48291`).
* **Printable Acknowledgement Slip:** One-click printable admission receipt with official college letterhead.
* **Application Status Tracker:** Secure verification using Application ID + registered mobile number/email to check live admission status without exposing private data.

---

### 🛡️ 2. College Administration Dashboard
* **Secure Administrator Authentication:** Session-based authentication protecting all admin endpoints with bcrypt/scrypt password hashing.
* **Live Analytics & KPI Cards:** Real-time metrics calculated from database records:
  * Total enrolled students
  * Total online applications
  * Approved / admitted candidates
  * Total fee collection (₹)
* **Application Management:**
  * Search by candidate name, application number, email, or mobile.
  * Filter applications by status (`Pending`, `Under Review`, `Approved`, `Rejected`) and academic programme.
  * Detailed modal inspector viewing full candidate academic history and contact details.
  * 1-Click status update with custom administrative remarks.
  * **1-Click Student Enrollment:** Instantly converts an approved applicant into an active student record with auto-assigned Student ID (e.g. `STU-2026-0012`).
* **Student Record Management:**
  * View, search, add, edit, and delete enrolled student records.
  * Track academic year progression (1st Year, 2nd Year, 3rd Year).
* **Academic Course Management:**
  * Create, edit, and delete academic programmes.
  * Configure seat quotas, annual tuition fees, icons, and eligibility rules.
* **Fee Collection & Payment Tracking:**
  * Record fee payments (Tuition, Admission, Semester, Exam, Library fees).
  * Auto-generates unique receipt numbers (e.g. `REC-2026-001-4921`).
  * Supports multiple payment modes (Online/UPI, Net Banking, Demand Draft, Cash).
* **Reports & Analytics:**
  * Visual distribution of students across programmes.
  * Programme capacity utilization table (seats vs enrolled).
  * Printable admission report view.
* **CSV Data Export:**
  * Export real-time data to CSV for Applications, Students, Courses, and Payments.
* **Admin Security & Settings:**
  * In-app password change tool with password hashing.
  * College contact information configuration.

---

## 🔐 Administrator Credentials

| Role | Email | Default Initial Password |
| :--- | :--- | :--- |
| **Super Admin** | `admin@college.com` | `Admin@123` |

> **Security Note:** Set strong environment variables (`SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`) in production on Render. The administrator password can also be changed at any time from the **Settings** tab inside the admin portal.

---

## 🛠️ Tech Stack & Architecture

* **Backend:** Python Flask 3.1
* **Database ORM:** SQLAlchemy / Flask-SQLAlchemy 3.1
* **Database:** PostgreSQL (Render Managed Database) / SQLite (Local development)
* **WSGI Production Server:** Gunicorn
* **Frontend:** Responsive HTML5, Modern Vanilla CSS with CSS Grid/Flexbox, JavaScript (ES6+)
* **Typography:** Plus Jakarta Sans & Inter via Google Fonts

---

## 🚀 Local Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/divekarsaniya6-maker/edumanage-admission.git
cd edumanage-admission
```

### 2. Create and activate a virtual environment
**On Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000** for the public admission website or **http://127.0.0.1:5000/admin** for the administration dashboard.

---

## ☁️ Deployment on Render

This project includes a **Render Blueprint** specification (`render.yaml`) that automatically provisions both the Flask Web Service and a persistent PostgreSQL database.

### Blueprint Configuration (`render.yaml`)
```yaml
services:
  - type: web
    name: edumanage-admission
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.7
      - key: SECRET_KEY
        generateValue: true
      - key: ADMIN_EMAIL
        value: admin@college.com
      - key: ADMIN_PASSWORD
        value: Admin@123
      - key: DATABASE_URL
        fromDatabase:
          name: edumanage-postgres
          property: connectionString

databases:
  - name: edumanage-postgres
    databaseName: edumanage_db
    user: edumanage_user
    plan: free
```

### Steps to Deploy:
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Blueprint**.
3. Connect your repository: `https://github.com/divekarsaniya6-maker/edumanage-admission`.
4. Render will parse `render.yaml`, provision the persistent PostgreSQL database, set up the web service, and deploy automatically!
5. Once deployment completes, your live website will be available at:
   `https://edumanage-admission.onrender.com`

---

## 🧪 Automated Testing

Run the automated test suite locally to verify all endpoints, database operations, security validations, and CSV exports:

```bash
python test_edumanage.py
```

---

## 📄 License
This project is licensed under the MIT License.

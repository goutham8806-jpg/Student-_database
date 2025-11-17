🎓 Student Portal & Admin Management System (Flask)

This is a complete Student Portal + Admin Dashboard built using Flask, designed for training institutes, colleges, and coaching centers.

Both students and admins get their own login systems with different permissions.

🚀 Features
👨‍🎓 Student Features

Student Registration

Login with email & password

Student Dashboard (home page)

View own profile

Edit/update own details

Submit profile update requests

Change password

Restricted access to admin-only features

👨‍💼 Admin Features

Secure Admin Login

Admin Dashboard

Add new students

View all students

View student profiles

Approve/reject edit requests

Edit student details

Delete students

Filters + Search bar

Pagination

Export data to Excel/PDF (if implemented)

Manage batches, trainers (if included)

📂 Project Structure
student_portal_final/
│
├── app.py                 # Flask application (routes, logic)
├── db.py                  # Database initialization & connection
├── run.py                 # Run file for production (Gunicorn/UWSGI)
├── requirements.txt       # Project dependencies
│
├── static/
│   └── style.css          # Global stylesheet
│
└── templates/
    ├── layout.html        # Base layout template
    ├── admin_login.html
    ├── student_register.html
    ├── student_login.html
    ├── dashboard.html
    ├── edit_requests.html
    ├── add_student.html
    ├── edit_student.html
    ├── view_students.html
    ├── student_home.html
    ├── student_profile.html
    ├── student_edit.html
    └── change_password.html

🛠️ Tech Stack
Purpose	Technology
Backend	Flask (Python)
Frontend	HTML, CSS, Bootstrap (optional)
Templates	Jinja2
Database	SQLite / MySQL (depending on your db.py)
Exports	openpyxl, pandas, reportlab
Authentication	Flask Session
⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/your-username/student_portal_final.git
cd student_portal_final

2️⃣ Create a virtual environment

Windows:

python -m venv venv
venv\Scripts\activate


Mac/Linux:

python3 -m venv venv
source venv/bin/activate

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Initialize the database

The app will auto-create tables on first run (based on db.py).
Otherwise run manually:

python db.py

5️⃣ Start the application
python app.py


App will run at:
👉 http://127.0.0.1:5000

🔑 Default Admin Credentials

(Modify or remove if needed)

Username: admin
Password: admin123

🧪 How Students Use the System

Open website

Go to Student Register

Fill details → account created

Login using email & password

Access student dashboard

Edit profile, view profile, or request changes

Admin reviews all changes via dashboard

🧪 How Admins Use the System

Login via /admin_login

Open admin dashboard

Manage existing students

Approve profile changes

Add/edit/delete students

Export or filter records

📤 Deployment Guide
Deploy on Render

Build Command → pip install -r requirements.txt

Start Command → gunicorn run:app

Deploy on PythonAnywhere

Upload project

Add web app (Flask)

Point WSGI file to app

Deploy on VPS

Nginx + Gunicorn setup

📄 requirements.txt (Example)
Flask
pandas
openpyxl
reportlab
gunicorn

📝 License

This project is for learning and educational use.

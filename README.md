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

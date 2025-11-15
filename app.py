# app.py
import io
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from werkzeug.security import generate_password_hash, check_password_hash

from db import init_db, get_connection

app = Flask(__name__)
app.secret_key = 'change_this_secret_change_in_prod'

# ensure DB
init_db()

@app.route("/")
def home():
    return render_template("index.html")


def query_db_app(query, params=None, fetch=False, one=False):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params or ())
    rows = None
    if fetch:
        rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    if one:
        return rows[0] if rows else None
    return rows

def safe_one(query, params=()):
    return query_db_app(query, params, fetch=True, one=True)

# ----------------- ADMIN LOGIN -----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = safe_one("SELECT * FROM users WHERE username=%s AND role='admin'", (username,))
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = 'admin'
            return redirect(url_for('dashboard'))
        flash("Invalid admin credentials")
        return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

# ----------------- STUDENT REGISTER / LOGIN -----------------
@app.route('/student_register', methods=['GET','POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('student_name','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        if not email or not password:
            flash("Email and password required")
            return redirect(url_for('student_register'))
        exists = safe_one("SELECT * FROM users WHERE username=%s", (email,))
        if exists:
            flash("Email already registered. Please login.")
            return redirect(url_for('student_login'))
        hashed = generate_password_hash(password)
        query_db_app("INSERT INTO users (username, password, role) VALUES (%s,%s,'student')", (email, hashed))
        user = safe_one("SELECT * FROM users WHERE username=%s", (email,))
        if user:
            query_db_app("INSERT INTO students (user_id, email, student_name, is_locked, edit_requested) VALUES (%s,%s,%s,0,0)", (user['id'], email, name))
        flash("Registered. Please login.")
        return redirect(url_for('student_login'))
    return render_template('student_register.html')


@app.route('/student_login', methods=['GET','POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        user = safe_one("SELECT * FROM users WHERE username=%s AND role='student'", (email,))
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = 'student'
            return redirect(url_for('student_home'))
        flash("Invalid student credentials")
        return redirect(url_for('student_login'))
    return render_template('student_login.html')

# ----------------- LOGOUT -----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('student_login'))

# ----------------- ADMIN DASHBOARD -----------------
@app.route('/dashboard')
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    search = request.args.get('search','').strip()
    page = int(request.args.get('page',1))
    per_page = 10
    offset = (page-1)*per_page

    where = " WHERE 1=1 "
    params = []
    if search:
        where += " AND (student_name LIKE %s OR phone LIKE %s OR email LIKE %s) "
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]

    total_row = query_db_app("SELECT COUNT(*) AS cnt FROM students" + where, tuple(params), fetch=True)
    total = total_row[0]['cnt'] if total_row else 0
    total_pages = (total + per_page - 1)//per_page

    q = "SELECT * FROM students" + where + " ORDER BY id DESC LIMIT %s OFFSET %s"
    rows = query_db_app(q, tuple(params + [per_page, offset]), fetch=True) or []

    pending_reqs = query_db_app("SELECT er.id, er.student_id, er.requested_at, s.student_name FROM edit_requests er JOIN students s ON er.student_id=s.id WHERE er.status='pending' ORDER BY er.requested_at DESC", fetch=True) or []

    return render_template('dashboard.html', students=rows, page=page, total_pages=total_pages, total=total, pending_reqs=pending_reqs)

# ----------------- Edit Requests (admin) -----------------
@app.route('/edit_requests')
def edit_requests():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    reqs = query_db_app("SELECT er.*, s.student_name, s.email FROM edit_requests er JOIN students s ON er.student_id=s.id ORDER BY er.requested_at DESC", fetch=True) or []
    return render_template('edit_requests.html', requests=reqs)

@app.route('/handle_request/<int:req_id>/<action>', methods=['POST'])
def handle_request(req_id, action):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    req = safe_one("SELECT * FROM edit_requests WHERE id=%s", (req_id,))
    if not req:
        flash("Request not found")
        return redirect(url_for('edit_requests'))
    if action == 'approve':
        query_db_app("UPDATE edit_requests SET status='approved', admin_id=%s, handled_at=%s WHERE id=%s", (session['user_id'], datetime.now(), req_id))
        query_db_app("UPDATE students SET is_locked=0, edit_requested=0 WHERE id=%s", (req['student_id'],))
        flash("Approved; student can edit now.")
    else:
        query_db_app("UPDATE edit_requests SET status='rejected', admin_id=%s, handled_at=%s WHERE id=%s", (session['user_id'], datetime.now(), req_id))
        query_db_app("UPDATE students SET edit_requested=0 WHERE id=%s", (req['student_id'],))
        flash("Rejected.")
    return redirect(url_for('edit_requests'))

# ----------------- Add Student (admin) -----------------
@app.route('/add_student', methods=['GET','POST'])
def add_student():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        batch = request.form.get('batch_no') or None
        name = request.form.get('student_name') or None
        phone = request.form.get('phone') or None
        email = request.form.get('email') or None
        admin_name = request.form.get('admin_name') or None
        trainer = request.form.get('trainer_name') or None
        suggestions = request.form.get('suggestions') or None
        join_date = request.form.get('join_date') or None
        course_combo = request.form.get('course_combo') or None

        user_id = None
        if email and phone:
            hashed = generate_password_hash(phone)
            query_db_app("INSERT IGNORE INTO users (username, password, role) VALUES (%s,%s,'student')", (email, hashed))
            u = safe_one("SELECT * FROM users WHERE username=%s", (email,))
            if u:
                user_id = u['id']

        query_db_app("""INSERT INTO students (user_id, batch_no, student_name, phone, email, admin_name, trainer_name, suggestions, join_date, course_combo, is_locked, edit_requested)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, 0, 0)""",
                     (user_id, batch, name, phone, email, admin_name, trainer, suggestions, join_date or None, course_combo))
        flash("Student added.")
        return redirect(url_for('dashboard'))
    return render_template('add_student.html')

# ----------------- Admin Edit Student -----------------
@app.route('/edit_student/<int:id>', methods=['GET','POST'])
def edit_student(id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    s = safe_one("SELECT * FROM students WHERE id=%s", (id,))
    if not s:
        flash("Not found")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        query_db_app("""UPDATE students SET batch_no=%s, student_name=%s, phone=%s, email=%s, admin_name=%s, trainer_name=%s, suggestions=%s, join_date=%s, course_combo=%s WHERE id=%s""",
                     (request.form.get('batch_no') or None,
                      request.form.get('student_name') or None,
                      request.form.get('phone') or None,
                      request.form.get('email') or None,
                      request.form.get('admin_name') or None,
                      request.form.get('trainer_name') or None,
                      request.form.get('suggestions') or None,
                      request.form.get('join_date') or None,
                      request.form.get('course_combo') or None,
                      id))
        # update users.username if email changed
        if s.get('email') and request.form.get('email') and s.get('email') != request.form.get('email'):
            query_db_app("UPDATE users SET username=%s WHERE username=%s AND role='student'", (request.form.get('email'), s.get('email')))
        flash("Updated")
        return redirect(url_for('dashboard'))
    return render_template('edit_student.html', student=s)

# ----------------- Admin Delete Student -----------------
@app.route('/delete_student/<int:id>', methods=['POST'])
def delete_student(id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    s = safe_one("SELECT * FROM students WHERE id=%s", (id,))
    if s:
        query_db_app("DELETE FROM students WHERE id=%s", (id,))
        if s.get('email'):
            query_db_app("DELETE FROM users WHERE username=%s AND role='student'", (s.get('email'),))
        flash("Deleted")
    return redirect(url_for('dashboard'))

# ----------------- Student Home / Profile -----------------
@app.route('/student_home')
def student_home():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))
    s = safe_one("SELECT * FROM students WHERE user_id=%s", (session['user_id'],))
    return render_template('student_home.html', student=s)

@app.route('/student_profile')
def student_profile():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))
    s = safe_one("SELECT * FROM students WHERE user_id=%s", (session['user_id'],))
    return render_template('student_profile.html', student=s)

# ----------------- Student Edit (fill & lock) -----------------
@app.route('/student_edit', methods=['GET','POST'])
def student_edit():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))
    s = safe_one("SELECT * FROM students WHERE user_id=%s", (session['user_id'],))
    if not s:
        flash("Profile not found")
        return redirect(url_for('student_home'))
    if s.get('is_locked'):
        flash("Profile locked. Request an edit.")
        return redirect(url_for('student_profile'))
    if request.method == 'POST':
        query_db_app("""UPDATE students SET batch_no=%s, student_name=%s, phone=%s, email=%s, admin_name=%s, trainer_name=%s, suggestions=%s, join_date=%s, course_combo=%s, is_locked=1, edit_requested=0 WHERE id=%s""",
                     (request.form.get('batch_no') or None,
                      request.form.get('student_name') or None,
                      request.form.get('phone') or None,
                      request.form.get('email') or None,
                      request.form.get('admin_name') or None,
                      request.form.get('trainer_name') or None,
                      request.form.get('suggestions') or None,
                      request.form.get('join_date') or None,
                      request.form.get('course_combo') or None,
                      s['id']))
        # keep user email sync
        if s.get('email') and request.form.get('email') and s.get('email') != request.form.get('email'):
            query_db_app("UPDATE users SET username=%s WHERE id=%s AND role='student'", (request.form.get('email'), session['user_id']))
            session['username'] = request.form.get('email')
        flash("Saved and locked. Request edit if you need changes.")
        return redirect(url_for('student_profile'))
    return render_template('student_edit.html', student=s)

# ----------------- Student Request Edit -----------------
@app.route('/request_edit', methods=['POST'])
def request_edit():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))
    s = safe_one("SELECT * FROM students WHERE user_id=%s", (session['user_id'],))
    if not s:
        flash("Profile missing")
        return redirect(url_for('student_home'))
    if s.get('edit_requested'):
        flash("Already requested. Wait for admin.")
        return redirect(url_for('student_profile'))
    query_db_app("INSERT INTO edit_requests (student_id, requested_at, status) VALUES (%s,%s,'pending')", (s['id'], datetime.now()))
    query_db_app("UPDATE students SET edit_requested=1 WHERE id=%s", (s['id'],))
    flash("Edit request sent to admin")
    return redirect(url_for('student_profile'))

# ----------------- Change Password -----------------
@app.route('/change_password', methods=['GET','POST'])
def change_password():
    if 'role' not in session:
        return redirect(url_for('student_login'))
    if request.method == 'POST':
        current = request.form.get('current_password','')
        newp = request.form.get('new_password','')
        confirm = request.form.get('confirm_password','')
        if newp != confirm:
            flash("New passwords do not match")
            return redirect(url_for('change_password'))
        user = safe_one("SELECT * FROM users WHERE id=%s", (session['user_id'],))
        if not user or not check_password_hash(user['password'], current):
            flash("Current incorrect")
            return redirect(url_for('change_password'))
        query_db_app("UPDATE users SET password=%s WHERE id=%s", (generate_password_hash(newp), session['user_id']))
        flash("Password changed. Please login again.")
        return redirect(url_for('logout'))
    return render_template('change_password.html')

# ----------------- Exports (admin) -----------------
@app.route('/export_excel')
def export_excel():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    students = query_db_app("SELECT * FROM students ORDER BY id DESC", fetch=True) or []
    wb = Workbook()
    ws = wb.active
    ws.append(["ID","Batch","Name","Phone","Email","Admin","Trainer","Join Date","Course","Locked","EditReq"])
    for s in students:
        ws.append([s.get('id'), s.get('batch_no'), s.get('student_name'), s.get('phone'), s.get('email'), s.get('admin_name'), s.get('trainer_name'), s.get('join_date'), s.get('course_combo'), s.get('is_locked'), s.get('edit_requested')])
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return send_file(bio, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name='students.xlsx', as_attachment=True)

@app.route('/export_pdf')
def export_pdf():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    students = query_db_app("SELECT * FROM students ORDER BY id DESC", fetch=True) or []
    bio = io.BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=letter)
    data = [["ID","Batch","Name","Phone","Email","Admin","Trainer","Join Date","Course"]]
    for s in students:
        data.append([s.get('id'), s.get('batch_no') or '', s.get('student_name') or '', s.get('phone') or '', s.get('email') or '', s.get('admin_name') or '', s.get('trainer_name') or '', str(s.get('join_date')) if s.get('join_date') else '', s.get('course_combo') or ''])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#3498db')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.25,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
    doc.build([table])
    bio.seek(0)
    return send_file(bio, mimetype='application/pdf', download_name='students.pdf', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timezone
import os, random, re, csv, io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'edumanage-secure-college-session-key-2026')

# Database configuration: PostgreSQL on Render, SQLite fallback locally
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
else:
    db_file = os.path.join(BASE_DIR, 'edumanage.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= DATABASE MODELS =================

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    icon = db.Column(db.String(20), default='🎓')
    duration = db.Column(db.String(50), default='3 Years')
    seats = db.Column(db.Integer, default=60)
    eligibility = db.Column(db.String(255), default='10+2 from recognized board')
    annual_fee = db.Column(db.Float, default=40000.0)
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'icon': self.icon or '🎓',
            'duration': self.duration or '3 Years',
            'seats': self.seats or 60,
            'eligibility': self.eligibility or '10+2 from recognized board',
            'annual_fee': float(self.annual_fee or 0),
            'description': self.description or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    app_number = db.Column(db.String(30), unique=True, index=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), index=True, nullable=False)
    phone = db.Column(db.String(20), index=True, nullable=False)
    dob = db.Column(db.String(20), default='')
    gender = db.Column(db.String(20), default='Not Specified')
    guardian_name = db.Column(db.String(100), default='')
    guardian_phone = db.Column(db.String(20), default='')
    address = db.Column(db.Text, default='')
    city = db.Column(db.String(50), default='')
    state = db.Column(db.String(50), default='')
    pincode = db.Column(db.String(15), default='')
    course_name = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(100), default='10+2 / HSC')
    board_university = db.Column(db.String(150), default='State Board')
    passing_year = db.Column(db.String(10), default='2026')
    percentage = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='Pending') # Pending, Under Review, Approved, Rejected
    admin_remarks = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'app_number': self.app_number,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'dob': self.dob,
            'gender': self.gender,
            'guardian_name': self.guardian_name,
            'guardian_phone': self.guardian_phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'course': self.course_name,
            'course_name': self.course_name,
            'qualification': self.qualification,
            'board_university': self.board_university,
            'passing_year': self.passing_year,
            'percentage': self.percentage,
            'status': self.status,
            'admin_remarks': self.admin_remarks or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(30), unique=True, index=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), default='')
    phone = db.Column(db.String(20), default='')
    course_name = db.Column(db.String(120), nullable=False)
    year = db.Column(db.String(30), default='1st Year')
    status = db.Column(db.String(30), default='Active')
    application_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email or '',
            'phone': self.phone or '',
            'course': self.course_name,
            'course_name': self.course_name,
            'year': self.year or '1st Year',
            'status': self.status or 'Active',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(30), unique=True, index=True, nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    fee_type = db.Column(db.String(50), default='Tuition Fee')
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.String(50), default='Online / UPI')
    reference_no = db.Column(db.String(80), default='')
    status = db.Column(db.String(30), default='Completed')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'receipt_no': self.receipt_no,
            'student': self.student_name,
            'student_name': self.student_name,
            'type': self.fee_type,
            'fee_type': self.fee_type,
            'amount': float(self.amount or 0),
            'payment_mode': self.payment_mode or 'Online',
            'reference_no': self.reference_no or '',
            'status': self.status or 'Completed',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), default='Administrator')
    role = db.Column(db.String(50), default='Super Admin')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# ================= AUTHENTICATION HELPER =================

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'error': 'Unauthorized. Please login as administrator.'}), 401
        return fn(*args, **kwargs)
    return wrapper

def generate_app_number():
    rand_digits = random.randint(10000, 99999)
    candidate = f"EDU-2026-{rand_digits}"
    while Application.query.filter_by(app_number=candidate).first():
        rand_digits = random.randint(10000, 99999)
        candidate = f"EDU-2026-{rand_digits}"
    return candidate

def generate_student_id():
    count = Student.query.count() + 1
    return f"STU-2026-{count:04d}"

def generate_receipt_no():
    rand_digits = random.randint(1000, 9999)
    count = Payment.query.count() + 1
    return f"REC-2026-{count:03d}-{rand_digits}"

# ================= SEEDING & INITIALIZATION =================

def seed_defaults():
    # 1. Seed default courses if empty
    if Course.query.count() == 0:
        default_courses = [
            Course(
                code='BSC-CS',
                name='B.Sc. Computer Science',
                icon='💻',
                duration='3 Years',
                seats=60,
                annual_fee=45000.0,
                eligibility='10+2 with Mathematics/Science, min 50% aggregate',
                description='Core programming, algorithms, AI foundations, full-stack web systems and cloud technologies.'
            ),
            Course(
                code='BSC-IT',
                name='B.Sc. Information Technology',
                icon='🌐',
                duration='3 Years',
                seats=60,
                annual_fee=42000.0,
                eligibility='10+2 with Science/Math, min 45% aggregate',
                description='Enterprise networking, cloud infrastructure, cybersecurity protocols and database architecture.'
            ),
            Course(
                code='BCOM',
                name='B.Com. (Accounting & Finance)',
                icon='📊',
                duration='3 Years',
                seats=120,
                annual_fee=32000.0,
                eligibility='10+2 Commerce or Science, min 45% aggregate',
                description='Corporate finance, audit systems, financial modeling, Indian taxation and banking regulations.'
            ),
            Course(
                code='BBA',
                name='B.B.A. (Business Administration)',
                icon='💼',
                duration='3 Years',
                seats=60,
                annual_fee=50000.0,
                eligibility='10+2 Any Stream, min 50% aggregate',
                description='Strategic management, global marketing, venture creation, business economics and analytics.'
            ),
            Course(
                code='BA-JMC',
                name='B.A. (Mass Communication & Journalism)',
                icon='📚',
                duration='3 Years',
                seats=80,
                annual_fee=28000.0,
                eligibility='10+2 Any Stream, min 45% aggregate',
                description='Digital journalism, television broadcasting, content strategy, audio-visual storytelling and PR.'
            ),
            Course(
                code='MSC-DS',
                name='M.Sc. Data Science & AI',
                icon='📈',
                duration='2 Years',
                seats=40,
                annual_fee=68000.0,
                eligibility='B.Sc. CS/IT/Maths/Stats or B.E./B.Tech. with min 55%',
                description='Advanced machine learning, deep neural networks, statistical inference, NLP and big data engineering.'
            )
        ]
        db.session.bulk_save_objects(default_courses)
        db.session.commit()

    # 2. Seed Admin User
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@college.com').strip().lower()
    admin_pw = os.environ.get('ADMIN_PASSWORD', 'Admin@123')
    
    admin_user = AdminUser.query.filter_by(email=admin_email).first()
    if not admin_user:
        admin_user = AdminUser(
            email=admin_email,
            password_hash=generate_password_hash(admin_pw),
            full_name='Chief Administrator',
            role='Super Admin'
        )
        db.session.add(admin_user)
        db.session.commit()

# ================= PUBLIC ROUTES =================

@app.route('/')
def home():
    courses = Course.query.order_by(Course.id.asc()).all()
    return render_template('index.html', courses=courses)

@app.route('/track')
def track_page():
    return redirect('/#track')

@app.route('/admin')
@app.route('/admin/login')
def admin_page():
    return render_template('admin.html')

@app.route('/health')
def health():
    try:
        # Check database connectivity
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    return jsonify({
        'status': 'ok',
        'app': 'EduManage Admission Management System',
        'version': '2.0.0',
        'database': db_status
    })

# ================= PUBLIC API ENDPOINTS =================

@app.route('/api/public/courses', methods=['GET'])
def get_public_courses():
    courses = Course.query.order_by(Course.id.asc()).all()
    return jsonify({'courses': [c.to_dict() for c in courses]})

@app.route('/api/public/apply', methods=['POST'])
def submit_application():
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({'error': 'No application data submitted.'}), 400

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    phone = (data.get('phone') or '').strip()
    dob = (data.get('dob') or '').strip()
    gender = (data.get('gender') or 'Not Specified').strip()
    guardian_name = (data.get('guardian_name') or '').strip()
    guardian_phone = (data.get('guardian_phone') or '').strip()
    address = (data.get('address') or '').strip()
    city = (data.get('city') or '').strip()
    state = (data.get('state') or '').strip()
    pincode = (data.get('pincode') or '').strip()
    course_name = (data.get('course_name') or data.get('course') or '').strip()
    qualification = (data.get('qualification') or '').strip()
    board_university = (data.get('board_university') or '').strip()
    passing_year = (data.get('passing_year') or '').strip()
    percentage_str = str(data.get('percentage') or '').strip()

    # Validations
    if len(name) < 2:
        return jsonify({'error': 'Please enter a valid student full name.'}), 400
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'error': 'Please enter a valid email address.'}), 400
    clean_phone = re.sub(r'[\s\-\+\(\)]', '', phone)
    if len(clean_phone) < 10:
        return jsonify({'error': 'Please enter a valid 10-digit mobile number.'}), 400
    if not dob:
        return jsonify({'error': 'Date of birth is required.'}), 400
    if not course_name:
        return jsonify({'error': 'Please select an academic course/programme.'}), 400
    
    # Check course exists
    course = Course.query.filter_by(name=course_name).first()
    if not course:
        # Fallback check by code or partial name
        course = Course.query.filter(Course.name.ilike(f'%{course_name}%')).first()
        if course:
            course_name = course.name

    try:
        percentage = float(percentage_str)
        if percentage < 0 or percentage > 100:
            return jsonify({'error': 'Percentage must be between 0 and 100.'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Please provide a valid percentage or score (e.g. 82.5).'}), 400

    # Prevent duplicate submission for same student & course
    existing = Application.query.filter(
        Application.course_name == course_name,
        (Application.email == email) | (Application.phone == clean_phone),
        Application.status.in_(['Pending', 'Under Review', 'Approved'])
    ).first()

    if existing:
        return jsonify({
            'error': f'An application for this course is already registered with Application Number {existing.app_number}. Please check your application status.'
        }), 409

    # Generate unique application number
    app_number = generate_app_number()

    app_record = Application(
        app_number=app_number,
        name=name,
        email=email,
        phone=clean_phone,
        dob=dob,
        gender=gender,
        guardian_name=guardian_name,
        guardian_phone=guardian_phone,
        address=address,
        city=city,
        state=state,
        pincode=pincode,
        course_name=course_name,
        qualification=qualification or '10+2 / Higher Secondary',
        board_university=board_university or 'State / National Board',
        passing_year=passing_year or '2026',
        percentage=percentage,
        status='Pending',
        admin_remarks='Application received online. Awaiting document verification.'
    )

    try:
        db.session.add(app_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save application. Please try again.'}), 500

    return jsonify({
        'ok': True,
        'message': 'Your admission application has been submitted successfully!',
        'app_number': app_number,
        'application': {
            'app_number': app_number,
            'name': name,
            'course': course_name,
            'email': email,
            'phone': clean_phone,
            'status': 'Pending',
            'submitted_at': app_record.created_at.strftime('%d %B %Y, %I:%M %p')
        }
    }), 201

@app.route('/api/public/track', methods=['POST'])
def track_application():
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({'error': 'Missing lookup parameters.'}), 400

    app_number = (data.get('app_number') or '').strip().upper()
    verification = (data.get('verification') or '').strip()

    if not app_number or not verification:
        return jsonify({'error': 'Please provide both your Application Number and registered Mobile/Email.'}), 400

    app_rec = Application.query.filter_by(app_number=app_number).first()
    if not app_rec:
        return jsonify({'error': 'No application found with this Application Number. Please check and re-try.'}), 404

    # Security check: verification must match email or phone
    clean_ver = re.sub(r'[\s\-\+\(\)]', '', verification).lower()
    app_phone_clean = re.sub(r'[\s\-\+\(\)]', '', app_rec.phone)
    if clean_ver != app_phone_clean and clean_ver != app_rec.email.lower():
        return jsonify({'error': 'The verification phone or email does not match our records for this application.'}), 403

    # Mask name for privacy (e.g. Saniya Divekar -> Saniya D***)
    name_parts = app_rec.name.split()
    if len(name_parts) > 1:
        masked_name = f"{name_parts[0]} {name_parts[-1][0]}***"
    else:
        masked_name = f"{name_parts[0][:3]}***"

    return jsonify({
        'ok': True,
        'application': {
            'app_number': app_rec.app_number,
            'masked_name': masked_name,
            'course': app_rec.course_name,
            'qualification': app_rec.qualification,
            'status': app_rec.status,
            'submitted_at': app_rec.created_at.strftime('%d %b %Y, %I:%M %p'),
            'admin_remarks': app_rec.admin_remarks or 'Application is under standard review.'
        }
    })

# ================= ADMIN AUTHENTICATION =================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    expected_email = os.environ.get('ADMIN_EMAIL', 'admin@college.com').strip().lower()
    expected_pw = os.environ.get('ADMIN_PASSWORD', 'Admin@123')

    # 1. Check in database first
    admin_user = AdminUser.query.filter_by(email=email).first()
    authenticated = False

    if admin_user and check_password_hash(admin_user.password_hash, password):
        authenticated = True
    elif email == expected_email and password == expected_pw:
        # Fallback to current environment variable credentials
        authenticated = True
        if admin_user:
            admin_user.password_hash = generate_password_hash(password)
            db.session.commit()
        else:
            admin_user = AdminUser(
                email=email,
                password_hash=generate_password_hash(password),
                full_name='Chief Administrator',
                role='Super Admin'
            )
            db.session.add(admin_user)
            db.session.commit()

    if authenticated:
        session['is_admin'] = True
        session['admin_email'] = email
        session['admin_name'] = admin_user.full_name if admin_user else 'Administrator'
        return jsonify({
            'ok': True,
            'user': {
                'name': session['admin_name'],
                'email': email,
                'role': 'Super Admin'
            }
        })

    return jsonify({'error': 'Invalid administrator email or password.'}), 401

@app.route('/api/admin/logout', methods=['POST', 'GET'])
def admin_logout():
    session.clear()
    if request.is_json:
        return jsonify({'ok': True, 'message': 'Logged out successfully.'})
    return redirect('/admin')

@app.route('/api/admin/change-password', methods=['POST'])
@admin_required
def admin_change_password():
    data = request.get_json(silent=True) or request.form.to_dict()
    current_pw = data.get('current_password') or ''
    new_pw = data.get('new_password') or ''
    confirm_pw = data.get('confirm_password') or ''

    if not current_pw or not new_pw:
        return jsonify({'error': 'Current and new password are required.'}), 400
    if len(new_pw) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long.'}), 400
    if new_pw != confirm_pw:
        return jsonify({'error': 'New password and confirmation do not match.'}), 400

    admin_email = session.get('admin_email', os.environ.get('ADMIN_EMAIL', 'admin@college.com')).strip().lower()
    admin_user = AdminUser.query.filter_by(email=admin_email).first()

    # Validate current password
    expected_env_pw = os.environ.get('ADMIN_PASSWORD', 'Admin@123')
    is_valid = False
    if admin_user and check_password_hash(admin_user.password_hash, current_pw):
        is_valid = True
    elif current_pw == expected_env_pw:
        is_valid = True

    if not is_valid:
        return jsonify({'error': 'Current password verification failed.'}), 400

    if not admin_user:
        admin_user = AdminUser(email=admin_email, full_name='Administrator', role='Super Admin')
        db.session.add(admin_user)

    admin_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()

    return jsonify({'ok': True, 'message': 'Administrator password updated successfully.'})

# ================= ADMIN DATA & CRUD =================

@app.route('/api/admin/data', methods=['GET'])
@admin_required
def get_all_admin_data():
    apps = Application.query.order_by(Application.id.desc()).all()
    students = Student.query.order_by(Student.id.desc()).all()
    courses = Course.query.order_by(Course.id.asc()).all()
    payments = Payment.query.order_by(Payment.id.desc()).all()

    total_fees = sum(p.amount for p in payments)
    approved_count = sum(1 for a in apps if a.status == 'Approved')
    pending_count = sum(1 for a in apps if a.status == 'Pending')
    rejected_count = sum(1 for a in apps if a.status == 'Rejected')

    return jsonify({
        'applications': [a.to_dict() for a in apps],
        'students': [s.to_dict() for s in students],
        'courses': [c.to_dict() for c in courses],
        'payments': [p.to_dict() for p in payments],
        'stats': {
            'students': len(students),
            'applications': len(apps),
            'admitted': approved_count,
            'approved': approved_count,
            'pending': pending_count,
            'rejected': rejected_count,
            'fees': total_fees,
            'payments_count': len(payments),
            'db_mode': 'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'
        }
    })

# Backward compatibility with original EduManage frontend
@app.route('/api/data', methods=['GET'])
@admin_required
def get_legacy_data():
    return get_all_admin_data()

# Applications Status Update
@app.route('/api/admin/applications/<int:app_id>/status', methods=['PATCH'])
@admin_required
def update_application_status(app_id):
    app_rec = db.get_or_404(Application, app_id)
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    remarks = data.get('remarks') or data.get('admin_remarks')

    if new_status:
        app_rec.status = new_status
    if remarks is not None:
        app_rec.admin_remarks = remarks.strip()

    db.session.commit()
    return jsonify({'ok': True, 'application': app_rec.to_dict()})

# Enroll approved applicant directly into Students table
@app.route('/api/admin/applications/<int:app_id>/enroll', methods=['POST'])
@admin_required
def enroll_applicant(app_id):
    app_rec = db.get_or_404(Application, app_id)
    # Check if student already enrolled from this application
    existing_student = Student.query.filter_by(application_id=app_rec.id).first()
    if existing_student:
        return jsonify({
            'ok': True,
            'message': f'Applicant is already enrolled as Student ({existing_student.student_id}).',
            'student': existing_student.to_dict()
        })

    student_id = generate_student_id()
    student = Student(
        student_id=student_id,
        name=app_rec.name,
        email=app_rec.email,
        phone=app_rec.phone,
        course_name=app_rec.course_name,
        year='1st Year',
        status='Active',
        application_id=app_rec.id
    )
    app_rec.status = 'Approved'
    if not app_rec.admin_remarks or 'enrolled' not in app_rec.admin_remarks.lower():
        app_rec.admin_remarks = f"Approved & Enrolled as Student {student_id}."

    db.session.add(student)
    db.session.commit()

    return jsonify({
        'ok': True,
        'message': f'Applicant successfully enrolled! Assigned Student ID: {student_id}',
        'student': student.to_dict()
    })

# Delete application
@app.route('/api/admin/applications/<int:app_id>', methods=['DELETE'])
@admin_required
def delete_application(app_id):
    app_rec = db.get_or_404(Application, app_id)
    db.session.delete(app_rec)
    db.session.commit()
    return jsonify({'ok': True, 'message': 'Application deleted successfully.'})

# Courses CRUD
@app.route('/api/admin/courses', methods=['POST'])
@admin_required
def create_course():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Course name is required.'}), 400

    code = (data.get('code') or '').strip().upper()
    if not code:
        code = ''.join([w[0] for w in name.split() if w.isalnum()])[:8].upper() or 'CRS'
        suffix = random.randint(10, 99)
        code = f"{code}-{suffix}"

    course = Course(
        code=code,
        name=name,
        icon=data.get('icon') or '🎓',
        duration=data.get('duration') or '3 Years',
        seats=int(data.get('seats') or 60),
        annual_fee=float(data.get('annual_fee') or data.get('fee') or 40000.0),
        eligibility=data.get('eligibility') or '10+2 from recognized board',
        description=data.get('description') or ''
    )
    db.session.add(course)
    db.session.commit()
    return jsonify(course.to_dict()), 201

@app.route('/api/admin/courses/<int:course_id>', methods=['PUT', 'PATCH'])
@admin_required
def update_course(course_id):
    course = db.get_or_404(Course, course_id)
    data = request.get_json(silent=True) or {}
    if 'name' in data: course.name = data['name'].strip()
    if 'code' in data: course.code = data['code'].strip().upper()
    if 'icon' in data: course.icon = data['icon'].strip()
    if 'duration' in data: course.duration = data['duration'].strip()
    if 'seats' in data: course.seats = int(data['seats'])
    if 'annual_fee' in data or 'fee' in data:
        course.annual_fee = float(data.get('annual_fee') or data.get('fee') or 0)
    if 'eligibility' in data: course.eligibility = data['eligibility'].strip()
    if 'description' in data: course.description = data['description'].strip()

    db.session.commit()
    return jsonify(course.to_dict())

@app.route('/api/admin/courses/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    course = db.get_or_404(Course, course_id)
    db.session.delete(course)
    db.session.commit()
    return jsonify({'ok': True})

# Students CRUD
@app.route('/api/admin/students', methods=['POST'])
@admin_required
def create_student():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    course_name = (data.get('course') or data.get('course_name') or '').strip()
    if not name or not course_name:
        return jsonify({'error': 'Student name and course are required.'}), 400

    student = Student(
        student_id=data.get('student_id') or generate_student_id(),
        name=name,
        email=(data.get('email') or '').strip(),
        phone=(data.get('phone') or '').strip(),
        course_name=course_name,
        year=data.get('year') or '1st Year',
        status=data.get('status') or 'Active'
    )
    db.session.add(student)
    db.session.commit()
    return jsonify(student.to_dict()), 201

@app.route('/api/admin/students/<int:student_id>', methods=['PUT', 'PATCH'])
@admin_required
def update_student(student_id):
    student = db.get_or_404(Student, student_id)
    data = request.get_json(silent=True) or {}
    if 'name' in data: student.name = data['name'].strip()
    if 'course' in data: student.course_name = data['course'].strip()
    if 'course_name' in data: student.course_name = data['course_name'].strip()
    if 'year' in data: student.year = data['year'].strip()
    if 'phone' in data: student.phone = data['phone'].strip()
    if 'email' in data: student.email = data['email'].strip()
    if 'status' in data: student.status = data['status'].strip()

    db.session.commit()
    return jsonify(student.to_dict())

@app.route('/api/admin/students/<int:student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({'ok': True})

# Payments CRUD
@app.route('/api/admin/payments', methods=['POST'])
@admin_required
def create_payment():
    data = request.get_json(silent=True) or {}
    student_name = (data.get('student') or data.get('student_name') or '').strip()
    amount_str = str(data.get('amount') or '').strip()

    if not student_name or not amount_str:
        return jsonify({'error': 'Student name and amount are required.'}), 400

    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than zero.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid payment amount.'}), 400

    receipt_no = generate_receipt_no()
    payment = Payment(
        receipt_no=receipt_no,
        student_name=student_name,
        fee_type=data.get('type') or data.get('fee_type') or 'Tuition Fee',
        amount=amount,
        payment_mode=data.get('payment_mode') or 'Online / UPI',
        reference_no=data.get('reference_no') or f"TXN-{random.randint(100000, 999999)}",
        status=data.get('status') or 'Completed'
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify(payment.to_dict()), 201

@app.route('/api/admin/payments/<int:payment_id>', methods=['DELETE'])
@admin_required
def delete_payment(payment_id):
    payment = db.get_or_404(Payment, payment_id)
    db.session.delete(payment)
    db.session.commit()
    return jsonify({'ok': True})

# Legacy dynamic API handlers for table actions
@app.route('/api/<table>', methods=['POST'])
@admin_required
def legacy_create_table(table):
    if table == 'applications':
        return submit_application()
    elif table == 'courses':
        return create_course()
    elif table == 'students':
        return create_student()
    elif table == 'payments':
        return create_payment()
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/<table>/<int:item_id>', methods=['PATCH', 'PUT'])
@admin_required
def legacy_patch_table(table, item_id):
    if table == 'applications':
        return update_application_status(item_id)
    elif table == 'courses':
        return update_course(item_id)
    elif table == 'students':
        return update_student(item_id)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/<table>/<int:item_id>', methods=['DELETE'])
@admin_required
def legacy_delete_table(table, item_id):
    if table == 'applications':
        return delete_application(item_id)
    elif table == 'courses':
        return delete_course(item_id)
    elif table == 'students':
        return delete_student(item_id)
    elif table == 'payments':
        return delete_payment(item_id)
    return jsonify({'error': 'Not found'}), 404

# ================= CSV EXPORT =================

@app.route('/api/admin/export/<string:table_name>', methods=['GET'])
@admin_required
def export_csv(table_name):
    output = io.StringIO()
    writer = csv.writer(output)

    if table_name == 'applications':
        writer.writerow(['Application No', 'Full Name', 'Course', 'Email', 'Phone', 'Percentage (%)', 'Status', 'Applied Date'])
        for a in Application.query.order_by(Application.id.desc()).all():
            writer.writerow([a.app_number, a.name, a.course_name, a.email, a.phone, a.percentage, a.status, a.created_at.strftime('%Y-%m-%d %H:%M')])
    elif table_name == 'students':
        writer.writerow(['Student ID', 'Full Name', 'Course', 'Year', 'Phone', 'Email', 'Status', 'Enrolled Date'])
        for s in Student.query.order_by(Student.id.desc()).all():
            writer.writerow([s.student_id, s.name, s.course_name, s.year, s.phone, s.email, s.status, s.created_at.strftime('%Y-%m-%d')])
    elif table_name == 'courses':
        writer.writerow(['Code', 'Course Name', 'Duration', 'Seats', 'Annual Fee (INR)', 'Eligibility'])
        for c in Course.query.order_by(Course.id.asc()).all():
            writer.writerow([c.code, c.name, c.duration, c.seats, c.annual_fee, c.eligibility])
    elif table_name == 'payments':
        writer.writerow(['Receipt No', 'Student Name', 'Fee Type', 'Amount (INR)', 'Mode', 'Status', 'Date'])
        for p in Payment.query.order_by(Payment.id.desc()).all():
            writer.writerow([p.receipt_no, p.student_name, p.fee_type, p.amount, p.payment_mode, p.status, p.created_at.strftime('%Y-%m-%d %H:%M')])
    else:
        return jsonify({'error': 'Invalid report type'}), 400

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=edumanage_{table_name}_{datetime.now(timezone.utc).strftime("%Y%m%d")}.csv'}
    )

# Static file direct helpers
@app.route('/style.css')
def style():
    return app.send_static_file('style.css')

@app.route('/script.js')
def script():
    return app.send_static_file('script.js')

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found.'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'An internal server error occurred. Please try again later.'}), 500
    return render_template('500.html'), 500

# Initialize database schema and default records
with app.app_context():
    db.create_all()
    seed_defaults()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

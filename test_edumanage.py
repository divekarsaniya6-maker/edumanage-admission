import os
import sys
import unittest
import json

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Ensure local test uses clean sqlite database
test_db = os.path.join(project_dir, 'test_edumanage.db')
if os.path.exists(test_db):
    try: os.remove(test_db)
    except: pass

os.environ['DATABASE_URL'] = f'sqlite:///{test_db}'
os.environ['SECRET_KEY'] = 'test-secret-key-edumanage'
os.environ['ADMIN_EMAIL'] = 'admin@college.com'
os.environ['ADMIN_PASSWORD'] = 'Admin@123'

import app
from app import db, Course, Application, Student, Payment, AdminUser

class EduManageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            app.seed_defaults()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()

    def test_01_health_endpoint(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertEqual(data.get('database'), 'connected')
        print("  [PASS] /health endpoint operational")

    def test_02_home_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('EduManage', html)
        self.assertIn('B.Sc. Computer Science', html)
        self.assertIn('Application for Student Admission', html)
        self.assertIn('Track Your Application Status', html)
        print("  [PASS] Public Home page loaded with college branding and courses")

    def test_03_public_courses_api(self):
        res = self.client.get('/api/public/courses')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('courses', data)
        self.assertGreaterEqual(len(data['courses']), 4)
        print(f"  [PASS] /api/public/courses returned {len(data['courses'])} courses")

    def test_04_public_apply_and_duplicate(self):
        payload = {
            'name': 'Saniya Divekar',
            'dob': '2005-04-12',
            'gender': 'Female',
            'guardian_name': 'Santosh Divekar',
            'guardian_phone': '9820011223',
            'email': 'saniya.applicant@example.com',
            'phone': '9820055443',
            'address': 'Plot 45, Sector 19',
            'city': 'Navi Mumbai',
            'state': 'Maharashtra',
            'pincode': '410210',
            'course_name': 'B.Sc. Computer Science',
            'qualification': '12th / HSC (Science)',
            'board_university': 'Maharashtra State Board',
            'passing_year': '2026',
            'percentage': 88.50
        }

        # 1. Successful submission
        res = self.client.post('/api/public/apply', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get('ok'))
        app_num = data.get('app_number')
        self.assertTrue(app_num.startswith('EDU-2026-'))
        print(f"  [PASS] Application submitted with App ID: {app_num}")

        # 2. Duplicate submission prevention
        res_dup = self.client.post('/api/public/apply', json=payload)
        self.assertEqual(res_dup.status_code, 409)
        self.assertIn('already registered', res_dup.get_json().get('error', ''))
        print("  [PASS] Duplicate submission correctly prevented (409 Conflict)")

        # 3. Track Application
        res_track = self.client.post('/api/public/track', json={
            'app_number': app_num,
            'verification': '9820055443'
        })
        self.assertEqual(res_track.status_code, 200)
        track_data = res_track.get_json()
        self.assertEqual(track_data['application']['app_number'], app_num)
        self.assertEqual(track_data['application']['status'], 'Pending')
        self.assertIn('***', track_data['application']['masked_name'])
        print("  [PASS] Application tracking with secure verification works")

    def test_05_admin_login_and_security(self):
        # 1. Invalid login
        res = self.client.post('/api/admin/login', json={
            'email': 'admin@college.com',
            'password': 'WrongPassword123'
        })
        self.assertEqual(res.status_code, 401)
        print("  [PASS] Invalid login rejected (401)")

        # 2. Valid login
        res = self.client.post('/api/admin/login', json={
            'email': 'admin@college.com',
            'password': 'Admin@123'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get('ok'))
        print("  [PASS] Admin login successful with Admin@123")

        # 3. Protected data endpoint
        res_data = self.client.get('/api/admin/data')
        self.assertEqual(res_data.status_code, 200)
        admin_data = res_data.get_json()
        self.assertIn('applications', admin_data)
        self.assertIn('stats', admin_data)
        print("  [PASS] Protected /api/admin/data accessible with session")

    def test_06_admin_application_lifecycle_and_enroll(self):
        # Login first
        self.client.post('/api/admin/login', json={'email': 'admin@college.com', 'password': 'Admin@123'})

        # Submit an application
        res_apply = self.client.post('/api/public/apply', json={
            'name': 'Rahul Sharma',
            'dob': '2005-08-20',
            'gender': 'Male',
            'email': 'rahul.test@example.com',
            'phone': '9833344455',
            'course_name': 'B.Com. (Accounting & Finance)',
            'percentage': 82.0
        })
        with self.app.app_context():
            app_id = Application.query.filter_by(email='rahul.test@example.com').first().id

        # Update status to Under Review
        res_st = self.client.patch(f'/api/admin/applications/{app_id}/status', json={
            'status': 'Under Review',
            'remarks': 'Marks verified from State Board portal.'
        })
        self.assertEqual(res_st.status_code, 200)
        self.assertEqual(res_st.get_json()['application']['status'], 'Under Review')
        print("  [PASS] Admin updated status to 'Under Review'")

        # 1-Click Enroll as student
        res_enroll = self.client.post(f'/api/admin/applications/{app_id}/enroll')
        self.assertEqual(res_enroll.status_code, 200)
        enroll_data = res_enroll.get_json()
        self.assertTrue(enroll_data['ok'])
        stu_id = enroll_data['student']['student_id']
        self.assertTrue(stu_id.startswith('STU-2026-'))
        print(f"  [PASS] 1-Click enrolled applicant as Student: {stu_id}")

        # Record a fee payment for this student
        res_pay = self.client.post('/api/admin/payments', json={
            'student_name': 'Rahul Sharma',
            'fee_type': 'Admission Fee',
            'amount': 15000,
            'payment_mode': 'Online / UPI'
        })
        self.assertEqual(res_pay.status_code, 201)
        pay_data = res_pay.get_json()
        self.assertTrue(pay_data['receipt_no'].startswith('REC-2026-'))
        print(f"  [PASS] Recorded fee payment with Receipt #: {pay_data['receipt_no']}")

    def test_07_admin_password_change(self):
        self.client.post('/api/admin/login', json={'email': 'admin@college.com', 'password': 'Admin@123'})

        res = self.client.post('/api/admin/change-password', json={
            'current_password': 'Admin@123',
            'new_password': 'CollegeNewPass@456',
            'confirm_password': 'CollegeNewPass@456'
        })
        self.assertEqual(res.status_code, 200)
        print("  [PASS] Admin password changed successfully")

        # Logout and test login with new password
        self.client.post('/api/admin/logout')
        res_new_login = self.client.post('/api/admin/login', json={
            'email': 'admin@college.com',
            'password': 'CollegeNewPass@456'
        })
        self.assertEqual(res_new_login.status_code, 200)
        print("  [PASS] Admin successfully logged in with new updated password")

    def test_08_csv_exports(self):
        self.client.post('/api/admin/login', json={'email': 'admin@college.com', 'password': 'CollegeNewPass@456'})

        for section in ['applications', 'students', 'courses', 'payments']:
            res = self.client.get(f'/api/admin/export/{section}')
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.mimetype, 'text/csv')
            self.assertIn('attachment', res.headers.get('Content-Disposition', ''))
            print(f"  [PASS] CSV export operational for '{section}'")

if __name__ == '__main__':
    unittest.main()

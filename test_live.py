import urllib.request
import urllib.parse
import json
import sys
import http.cookiejar

def test_live_deployment(base_url="https://edumanage-admission.onrender.com"):
    base_url = base_url.rstrip("/")
    print(f"Testing live EduManage deployment at: {base_url}\n")
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Health check
    try:
        req = urllib.request.Request(f"{base_url}/health", headers={"User-Agent": "Antigravity-Agent"})
        with opener.open(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            assert resp.status == 200
            assert data.get("status") == "ok"
            print("  [PASS] 1. /health endpoint is operational (200 OK)")
    except Exception as e:
        print(f"  [FAIL] 1. /health check failed: {e}")
        return False

    # 2. Public Homepage & Courses
    try:
        req = urllib.request.Request(f"{base_url}/", headers={"User-Agent": "Antigravity-Agent"})
        with opener.open(req, timeout=30) as resp:
            html = resp.read().decode()
            assert resp.status == 200
            assert "EduManage" in html
            assert "B.Sc. Computer Science" in html
            assert "Application for Student Admission" in html
            print("  [PASS] 2. Public Homepage loads with courses & admission portal")
    except Exception as e:
        print(f"  [FAIL] 2. Homepage failed: {e}")
        return False

    # 3. Submit Public Admission Application
    app_num = None
    try:
        payload = json.dumps({
            "name": "Live Verification Candidate",
            "dob": "2005-06-15",
            "gender": "Female",
            "guardian_name": "Guardian Name",
            "guardian_phone": "9876543210",
            "email": "live.candidate@example.com",
            "phone": "9876543210",
            "address": "College Road, Sector 15",
            "city": "Navi Mumbai",
            "state": "Maharashtra",
            "pincode": "410210",
            "course_name": "B.Sc. Computer Science",
            "qualification": "12th / HSC (Science)",
            "board_university": "State Board",
            "passing_year": "2026",
            "percentage": 89.5
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/public/apply",
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Antigravity-Agent"}
        )
        with opener.open(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            assert resp.status == 201
            assert data.get("ok") is True
            app_num = data.get("app_number")
            assert app_num.startswith("EDU-2026-")
            print(f"  [PASS] 3. Admission application submitted: App #{app_num}")
    except Exception as e:
        print(f"  [FAIL] 3. Public admission submission failed: {e}")
        return False

    # 4. Track Application Status
    try:
        payload = json.dumps({
            "app_number": app_num,
            "verification": "9876543210"
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/public/track",
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Antigravity-Agent"}
        )
        with opener.open(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            assert resp.status == 200
            assert data.get("ok") is True
            assert data["application"]["status"] == "Pending"
            print("  [PASS] 4. Application status tracking verified")
    except Exception as e:
        print(f"  [FAIL] 4. Application tracking failed: {e}")
        return False

    # 5. Administrator Login
    try:
        payload = json.dumps({
            "email": "admin@college.com",
            "password": "Admin@123"
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/admin/login",
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Antigravity-Agent"}
        )
        with opener.open(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            assert resp.status == 200
            assert data.get("ok") is True
            print("  [PASS] 5. Admin login authenticated with Admin@123")
    except Exception as e:
        print(f"  [FAIL] 5. Admin login failed: {e}")
        return False

    # 6. Admin Data Access
    try:
        req = urllib.request.Request(
            f"{base_url}/api/admin/data",
            headers={"User-Agent": "Antigravity-Agent"}
        )
        with opener.open(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            assert resp.status == 200
            assert "applications" in data
            assert "stats" in data
            print(f"  [PASS] 6. Admin data retrieved (Total Applications: {data['stats']['applications']})")
    except Exception as e:
        print(f"  [FAIL] 6. Admin data check failed: {e}")
        return False

    print("\nALL LIVE PRODUCTION CHECKS COMPLETED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://edumanage-admission.onrender.com"
    test_live_deployment(url)

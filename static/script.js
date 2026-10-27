// ================= EDUMANAGE ADMIN DASHBOARD SCRIPT =================

const $ = id => document.getElementById(id);

let data = {
    applications: [],
    students: [],
    courses: [],
    payments: [],
    stats: {}
};

let currentApp = null;
let editingStudentId = null;
let editingCourseId = null;

function toast(msg, error = false) {
    const container = $('toastContainer') || document.body;
    const el = document.createElement('div');
    el.className = 'toast' + (error ? ' error' : '');
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => {
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 300);
    }, 3200);
}

async function api(url, opts = {}) {
    const r = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...opts
    });
    let d = {};
    try { d = await r.json(); } catch {}
    if (!r.ok) {
        throw new Error(d.error || 'Server error occurred');
    }
    return d;
}

// ---------------- LOGIN / LOGOUT ----------------

async function loginSubmit(e) {
    e.preventDefault();
    const btn = $('loginSubmitBtn');
    const btnText = $('loginBtnText');
    const spinner = $('loginSpinner');

    const email = $('loginEmail').value.trim();
    const password = $('loginPassword').value;

    btn.disabled = true;
    btnText.textContent = 'Verifying...';
    spinner.classList.remove('hidden');

    try {
        const res = await api('/api/admin/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        $('loginScreen').classList.add('hidden');
        $('app').classList.remove('hidden');

        if (res.user && res.user.name) {
            if ($('sidebarAdminName')) $('sidebarAdminName').textContent = res.user.name;
            if ($('headerAdminName')) $('headerAdminName').textContent = res.user.name;
        }

        await refresh();
        toast('Welcome back, Administrator!');
    } catch (err) {
        toast(err.message, true);
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Login to Dashboard →';
        spinner.classList.add('hidden');
    }
}

async function logout() {
    try {
        await api('/api/admin/logout', { method: 'POST' });
    } catch {}
    $('app').classList.add('hidden');
    $('loginScreen').classList.remove('hidden');
    $('loginPassword').value = '';
    toast('Logged out successfully.');
}

function togglePassword() {
    const p = $('loginPassword');
    p.type = p.type === 'password' ? 'text' : 'password';
}

function toggleSidebar() {
    $('sidebar').classList.toggle('open');
}

function showForgotPassword(e) {
    e.preventDefault();
    toast('Default administrator login is admin@college.com / Admin@123', false);
}

function showNotifications() {
    const p = data.applications.filter(a => a.status === 'Pending').length;
    toast(p ? `You have ${p} pending application(s) awaiting review.` : 'All applications are up to date!');
}

// ---------------- NAVIGATION ----------------

function openPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active-page'));
    const page = $(name + 'Page');
    if (page) page.classList.add('active-page');

    document.querySelectorAll('.nav-item').forEach(n => {
        n.classList.toggle('active', n.dataset.page === name);
    });

    const titles = {
        dashboard: ['Dashboard', 'Welcome back, Administrator'],
        applications: ['Applications', 'Review and process student admission applications'],
        students: ['Enrolled Students', 'Manage officially registered college students'],
        courses: ['Academic Courses', 'Manage academic degree programmes and seat quotas'],
        payments: ['Fees & Payments', 'Track tuition and admission fee transactions'],
        reports: ['Reports & Analytics', 'College admission statistics and capacity overview'],
        settings: ['System Settings', 'College profile and administrator security']
    };

    if (titles[name]) {
        $('pageTitle').textContent = titles[name][0];
        $('pageSubtitle').textContent = titles[name][1];
    }

    $('sidebar').classList.remove('open');
    if (name === 'reports') renderReports();
}

// ---------------- DATA SYNC & RENDERING ----------------

async function refresh() {
    try {
        data = await api('/api/admin/data');
        renderAll();
    } catch (e) {
        if (e.message && e.message.toLowerCase().includes('unauthorized')) {
            logout();
        } else {
            toast(e.message, true);
        }
    }
}

function safe(v) {
    return String(v ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[c]));
}

function money(v) {
    return '₹' + Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

function statusBadge(s) {
    const st = (s || 'Pending');
    let c = st.toLowerCase().replace(/\s+/g, '-');
    return `<span class="status-pill ${c}">${safe(st)}</span>`;
}

function renderAll() {
    renderStats();
    renderApps();
    renderRecent();
    renderStudents();
    renderCourses();
    renderPayments();
    fillSelects();
    renderReports();

    if ($('applicationBadge')) {
        const pending = data.applications.filter(a => a.status === 'Pending').length;
        $('applicationBadge').textContent = pending;
    }
    if ($('dbStatusBadge')) {
        $('dbStatusBadge').textContent = data.stats.db_mode ? `${data.stats.db_mode} (Persistent)` : 'Connected';
    }
}

function renderStats() {
    const s = data.stats || {};
    setText('totalStudents', s.students || 0);
    setText('totalApplications', s.applications || 0);
    setText('totalAdmitted', s.admitted || 0);
    setText('totalFees', money(s.fees || 0));

    setText('paymentTotal', money(s.fees || 0));
    setText('paymentCount', data.payments.length);
    setText('averagePayment', money(data.payments.length ? (s.fees || 0) / data.payments.length : 0));
}

function setText(id, v) {
    const el = $(id);
    if (el) el.textContent = v;
}

// ---------------- RECENT APPLICATIONS & CHARTS ----------------

function renderRecent() {
    const body = $('recentApplicationsTable');
    if (!body) return;

    const arr = data.applications.slice(0, 5);
    if (!arr.length) {
        body.innerHTML = '<tr><td colspan="6" class="empty-state">No admission applications received yet.</td></tr>';
    } else {
        body.innerHTML = arr.map(a => `
            <tr>
                <td><strong style="color:var(--primary); font-size:12px;">${safe(a.app_number)}</strong></td>
                <td><strong>${safe(a.name)}</strong></td>
                <td>${safe(a.course)}</td>
                <td>${statusBadge(a.status)}</td>
                <td>${safe(a.created_at)}</td>
                <td>
                    <button class="secondary-btn" style="padding: 5px 10px; font-size: 12px;" onclick="viewAppDetails(${a.id})">View</button>
                </td>
            </tr>
        `).join('');
    }

    const dist = $('courseDistribution');
    if (dist) {
        const counts = data.students.reduce((acc, s) => {
            acc[s.course] = (acc[s.course] || 0) + 1;
            return acc;
        }, {});

        const keys = Object.keys(counts);
        if (!keys.length) {
            dist.innerHTML = '<div class="empty-state" style="padding:20px;">No enrolled students yet.</div>';
        } else {
            const total = data.students.length || 1;
            dist.innerHTML = keys.map(k => {
                const count = counts[k];
                const pct = Math.round((count / total) * 100);
                return `
                    <div style="margin: 12px 0;">
                        <div style="display:flex; justify-content:space-between; margin-bottom: 5px; font-size:13px;">
                            <span>${safe(k)}</span>
                            <strong>${count} (${pct}%)</strong>
                        </div>
                        <div style="height: 8px; background: #f0efff; border-radius: 8px; overflow:hidden;">
                            <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, #6558e8, #9187ff); border-radius: 8px;"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }
}

// ---------------- APPLICATIONS MANAGEMENT ----------------

function renderApps() {
    const body = $('applicationsTable');
    if (!body) return;

    const q = ($('applicationSearch')?.value || '').toLowerCase().trim();
    const stFilter = $('applicationStatusFilter')?.value || '';
    const crsFilter = $('applicationCourseFilter')?.value || '';

    const list = data.applications.filter(a => {
        const matchesQ = !q || (
            (a.name || '').toLowerCase().includes(q) ||
            (a.app_number || '').toLowerCase().includes(q) ||
            (a.email || '').toLowerCase().includes(q) ||
            (a.phone || '').includes(q) ||
            (a.course || '').toLowerCase().includes(q)
        );
        const matchesSt = !stFilter || a.status === stFilter;
        const matchesCrs = !crsFilter || a.course === crsFilter;
        return matchesQ && matchesSt && matchesCrs;
    });

    if (!list.length) {
        body.innerHTML = '<tr><td colspan="8" class="empty-state">No matching applications found.</td></tr>';
        return;
    }

    body.innerHTML = list.map(a => `
        <tr>
            <td><strong style="color:var(--primary); font-size:12px;">${safe(a.app_number)}</strong></td>
            <td><strong>${safe(a.name)}</strong></td>
            <td>${safe(a.course)}</td>
            <td>
                <div>${safe(a.email)}</div>
                <small style="color:var(--muted);">${safe(a.phone)}</small>
            </td>
            <td><strong>${safe(a.percentage)}%</strong></td>
            <td>${statusBadge(a.status)}</td>
            <td>${safe(a.created_at)}</td>
            <td style="text-align: right; white-space: nowrap;">
                <button class="secondary-btn" style="padding: 5px 10px; font-size: 12px;" onclick="viewAppDetails(${a.id})" title="View Details">👁️ View</button>
                ${a.status !== 'Approved' ? `
                    <button class="primary-btn" style="padding: 5px 10px; font-size: 12px; background: #1ba982;" onclick="setStatusDirect(${a.id}, 'Approved')" title="Approve">✓</button>
                ` : ''}
                ${a.status !== 'Rejected' ? `
                    <button class="danger-btn" style="padding: 5px 10px; font-size: 12px;" onclick="setStatusDirect(${a.id}, 'Rejected')" title="Reject">✕</button>
                ` : ''}
                <button class="danger-btn" style="padding: 5px 8px; font-size: 12px; margin-left: 4px;" onclick="deleteApplication(${a.id})" title="Delete">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function viewAppDetails(id) {
    currentApp = data.applications.find(a => a.id === id);
    if (!currentApp) return;

    $('viewAppNumber').textContent = currentApp.app_number;
    $('viewCourseTitle').textContent = `Applied for: ${currentApp.course}`;

    const badge = $('viewStatusBadge');
    badge.className = `status-pill ${(currentApp.status || 'pending').toLowerCase().replace(/\s+/g, '-')}`;
    badge.textContent = currentApp.status;

    // Show/hide enroll button based on status
    const enrollBtn = $('enrollAppBtn');
    if (enrollBtn) {
        enrollBtn.style.display = currentApp.status === 'Approved' ? 'inline-block' : 'none';
    }

    const body = $('appDetailsBody');
    body.innerHTML = `
        <div style="background: var(--bg); border-radius: 12px; padding: 18px; margin-bottom: 18px;">
            <h4 style="margin: 0 0 12px; color: var(--primary); font-size: 14px;">1. Candidate Personal Information</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                <div><span style="color:var(--muted)">Full Name:</span> <strong>${safe(currentApp.name)}</strong></div>
                <div><span style="color:var(--muted)">Gender:</span> <strong>${safe(currentApp.gender || 'Not specified')}</strong></div>
                <div><span style="color:var(--muted)">Date of Birth:</span> <strong>${safe(currentApp.dob || 'N/A')}</strong></div>
                <div><span style="color:var(--muted)">Guardian Name:</span> <strong>${safe(currentApp.guardian_name || 'N/A')}</strong></div>
                <div><span style="color:var(--muted)">Guardian Phone:</span> <strong>${safe(currentApp.guardian_phone || 'N/A')}</strong></div>
            </div>
        </div>

        <div style="background: var(--bg); border-radius: 12px; padding: 18px; margin-bottom: 18px;">
            <h4 style="margin: 0 0 12px; color: var(--primary); font-size: 14px;">2. Contact Information & Address</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                <div><span style="color:var(--muted)">Email Address:</span> <strong>${safe(currentApp.email)}</strong></div>
                <div><span style="color:var(--muted)">Mobile Number:</span> <strong>${safe(currentApp.phone)}</strong></div>
                <div style="grid-column: span 2;"><span style="color:var(--muted)">Address:</span> <strong>${safe(currentApp.address || '')}, ${safe(currentApp.city || '')}, ${safe(currentApp.state || '')} - ${safe(currentApp.pincode || '')}</strong></div>
            </div>
        </div>

        <div style="background: var(--bg); border-radius: 12px; padding: 18px; margin-bottom: 18px;">
            <h4 style="margin: 0 0 12px; color: var(--primary); font-size: 14px;">3. Academic Qualifications</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                <div><span style="color:var(--muted)">Qualifying Exam:</span> <strong>${safe(currentApp.qualification || '12th HSC')}</strong></div>
                <div><span style="color:var(--muted)">Board/University:</span> <strong>${safe(currentApp.board_university || 'State Board')}</strong></div>
                <div><span style="color:var(--muted)">Passing Year:</span> <strong>${safe(currentApp.passing_year || '2026')}</strong></div>
                <div><span style="color:var(--muted)">Aggregate Score:</span> <strong style="color:var(--primary); font-size: 15px;">${safe(currentApp.percentage)}%</strong></div>
            </div>
        </div>

        <div style="background: #fff8e6; border-left: 4px solid #ffb300; border-radius: 0 10px 10px 0; padding: 14px 18px;">
            <label style="font-weight: 700; font-size: 12px; color: #7a5400; display: block; margin-bottom: 6px;">Admissions Committee Remarks & Directives:</label>
            <textarea id="appRemarksInput" rows="2" style="width: 100%; border: 1px solid #ffd57a; border-radius: 8px; padding: 8px; background: #fff;">${safe(currentApp.admin_remarks || '')}</textarea>
            <button class="primary-btn" style="margin-top: 8px; padding: 6px 14px; font-size: 12px;" onclick="saveCurrentAppRemarks()">Save Remarks</button>
        </div>
    `;

    openModal('appDetailsModal');
}

async function saveCurrentAppRemarks() {
    if (!currentApp) return;
    const remarks = $('appRemarksInput').value.trim();
    try {
        await api(`/api/admin/applications/${currentApp.id}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ remarks })
        });
        currentApp.admin_remarks = remarks;
        await refresh();
        toast('Remarks updated successfully.');
    } catch (e) {
        toast(e.message, true);
    }
}

async function updateAppStatusPrompt(status) {
    if (!currentApp) return;
    const remarks = $('appRemarksInput')?.value.trim() || currentApp.admin_remarks;
    try {
        await api(`/api/admin/applications/${currentApp.id}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status, remarks })
        });
        closeModal('appDetailsModal');
        await refresh();
        toast(`Application marked as ${status}`);
    } catch (e) {
        toast(e.message, true);
    }
}

async function setStatusDirect(id, status) {
    try {
        await api(`/api/admin/applications/${id}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
        await refresh();
        toast(`Application marked as ${status}`);
    } catch (e) {
        toast(e.message, true);
    }
}

async function enrollCurrentApp() {
    if (!currentApp) return;
    if (!confirm(`Enroll ${currentApp.name} as an official student?`)) return;

    try {
        const res = await api(`/api/admin/applications/${currentApp.id}/enroll`, {
            method: 'POST'
        });
        closeModal('appDetailsModal');
        await refresh();
        toast(res.message || 'Applicant enrolled as student!');
        openPage('students');
    } catch (e) {
        toast(e.message, true);
    }
}

async function deleteApplication(id) {
    if (!confirm('Are you sure you want to delete this application record? This cannot be undone.')) return;
    try {
        await api(`/api/admin/applications/${id}`, { method: 'DELETE' });
        await refresh();
        toast('Application deleted');
    } catch (e) {
        toast(e.message, true);
    }
}

async function submitAdminApplication(e) {
    e.preventDefault();
    const payload = {
        name: $('adminApplicantName').value.trim(),
        course_name: $('applicantCourse').value,
        email: $('adminApplicantEmail').value.trim(),
        phone: $('adminApplicantPhone').value.trim(),
        qualification: $('adminApplicantQual').value.trim(),
        percentage: parseFloat($('adminApplicantPercentage').value || 75.0),
        status: 'Pending'
    };

    try {
        await api('/api/public/apply', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        closeModal('applicationModal');
        await refresh();
        toast('Application added successfully.');
    } catch (err) {
        toast(err.message, true);
    }
}

// ---------------- STUDENTS MANAGEMENT ----------------

function renderStudents() {
    const body = $('studentsTable');
    if (!body) return;

    const q = ($('studentSearch')?.value || '').toLowerCase().trim();
    const crs = $('studentCourseFilter')?.value || '';

    const list = data.students.filter(s => {
        const matchesQ = !q || (
            (s.name || '').toLowerCase().includes(q) ||
            (s.student_id || '').toLowerCase().includes(q) ||
            (s.phone || '').includes(q) ||
            (s.course || '').toLowerCase().includes(q)
        );
        const matchesCrs = !crs || s.course === crs;
        return matchesQ && matchesCrs;
    });

    if (!list.length) {
        body.innerHTML = '<tr><td colspan="8" class="empty-state">No students found matching your criteria.</td></tr>';
        return;
    }

    body.innerHTML = list.map(s => `
        <tr>
            <td><strong style="color:var(--primary); font-size:12px;">${safe(s.student_id)}</strong></td>
            <td><strong>${safe(s.name)}</strong></td>
            <td>${safe(s.course)}</td>
            <td>${safe(s.year)}</td>
            <td>${safe(s.phone)}</td>
            <td><span class="status-pill ${s.status === 'Active' ? 'approved' : 'pending'}">${safe(s.status)}</span></td>
            <td>${safe(s.created_at)}</td>
            <td style="text-align: right; white-space: nowrap;">
                <button class="secondary-btn" style="padding: 5px 10px; font-size: 12px;" onclick="editStudent(${s.id})">✏️ Edit</button>
                <button class="danger-btn" style="padding: 5px 8px; font-size: 12px; margin-left: 4px;" onclick="deleteStudent(${s.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function openStudentModal(id = null) {
    editingStudentId = id;
    const m = $('studentModal');
    $('studentForm').reset();
    fillSelects();

    if (id) {
        const s = data.students.find(x => x.id === id);
        if (s) {
            $('studentModalTitle').textContent = 'Edit Student Record';
            $('studentName').value = s.name;
            $('studentCourse').value = s.course;
            $('studentYear').value = s.year;
            $('studentPhone').value = s.phone || '';
            $('studentEmail').value = s.email || '';
            $('studentStatus').value = s.status || 'Active';
        }
    } else {
        $('studentModalTitle').textContent = 'Add Enrolled Student';
    }

    openModal('studentModal');
}

function editStudent(id) {
    openStudentModal(id);
}

async function submitStudentForm(e) {
    e.preventDefault();
    const payload = {
        name: $('studentName').value.trim(),
        course: $('studentCourse').value,
        year: $('studentYear').value,
        phone: $('studentPhone').value.trim(),
        email: $('studentEmail').value.trim(),
        status: $('studentStatus').value
    };

    try {
        if (editingStudentId) {
            await api(`/api/admin/students/${editingStudentId}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
            toast('Student record updated');
        } else {
            await api('/api/admin/students', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            toast('Student added successfully');
        }
        closeModal('studentModal');
        await refresh();
    } catch (err) {
        toast(err.message, true);
    }
}

async function deleteStudent(id) {
    if (!confirm('Are you sure you want to remove this student?')) return;
    try {
        await api(`/api/admin/students/${id}`, { method: 'DELETE' });
        await refresh();
        toast('Student record deleted');
    } catch (e) {
        toast(e.message, true);
    }
}

// ---------------- COURSES MANAGEMENT ----------------

function renderCourses() {
    const grid = $('courseCardsGrid');
    if (!grid) return;

    if (!data.courses.length) {
        grid.innerHTML = '<div class="empty-state">No academic courses found. Add your first programme.</div>';
        return;
    }

    grid.innerHTML = data.courses.map(c => `
        <article class="panel course-card" style="display:flex; flex-direction:column;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                <span style="font-size:32px; background:#f0efff; border-radius:12px; width:48px; height:48px; display:grid; place-items:center;">${safe(c.icon || '🎓')}</span>
                <span class="course-code-badge" style="background:#f0efff; color:var(--primary); font-weight:800; font-size:11px; padding:4px 8px; border-radius:6px;">${safe(c.code)}</span>
            </div>
            <h3 style="margin: 0 0 6px; font-size: 17px; font-weight: 700;">${safe(c.name)}</h3>
            <p style="color:var(--muted); font-size:12px; margin:0 0 16px; flex-grow:1; line-height:1.5;">${safe(c.description || 'Degree programme')}</p>
            
            <div style="border-top:1px solid #edf0f8; border-bottom:1px solid #edf0f8; padding:10px 0; margin-bottom:16px; font-size:12px;">
                <div style="display:flex; justify-content:space-between; margin:4px 0;">
                    <span style="color:var(--muted)">Duration:</span>
                    <strong>${safe(c.duration)}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin:4px 0;">
                    <span style="color:var(--muted)">Seats:</span>
                    <strong>${safe(c.seats)} Seats</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin:4px 0;">
                    <span style="color:var(--muted)">Annual Fee:</span>
                    <strong style="color:var(--primary);">${money(c.annual_fee)}</strong>
                </div>
            </div>

            <div style="display:flex; justify-content:space-between; gap:8px;">
                <button class="secondary-btn" style="flex:1; padding:8px; font-size:12px;" onclick="editCourse(${c.id})">✏️ Edit</button>
                <button class="danger-btn" style="padding:8px 12px; font-size:12px;" onclick="deleteCourse(${c.id})">🗑️</button>
            </div>
        </article>
    `).join('');
}

function openCourseModal(id = null) {
    editingCourseId = id;
    $('courseForm').reset();

    if (id) {
        const c = data.courses.find(x => x.id === id);
        if (c) {
            $('courseModalTitle').textContent = 'Edit Academic Course';
            $('courseName').value = c.name;
            $('courseCode').value = c.code || '';
            $('courseIcon').value = c.icon || '🎓';
            $('courseDuration').value = c.duration || '3 Years';
            $('courseSeats').value = c.seats || 60;
            $('courseFee').value = c.annual_fee || 40000;
            $('courseEligibility').value = c.eligibility || '';
            $('courseDescription').value = c.description || '';
        }
    } else {
        $('courseModalTitle').textContent = 'Add Academic Course';
    }

    openModal('courseModal');
}

function editCourse(id) {
    openCourseModal(id);
}

async function submitCourseForm(e) {
    e.preventDefault();
    const payload = {
        name: $('courseName').value.trim(),
        code: $('courseCode').value.trim(),
        icon: $('courseIcon').value.trim() || '🎓',
        duration: $('courseDuration').value.trim(),
        seats: parseInt($('courseSeats').value || 60),
        annual_fee: parseFloat($('courseFee').value || 40000),
        eligibility: $('courseEligibility').value.trim(),
        description: $('courseDescription').value.trim()
    };

    try {
        if (editingCourseId) {
            await api(`/api/admin/courses/${editingCourseId}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
            toast('Course updated');
        } else {
            await api('/api/admin/courses', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            toast('Course created successfully');
        }
        closeModal('courseModal');
        await refresh();
    } catch (err) {
        toast(err.message, true);
    }
}

async function deleteCourse(id) {
    if (!confirm('Are you sure you want to delete this course?')) return;
    try {
        await api(`/api/admin/courses/${id}`, { method: 'DELETE' });
        await refresh();
        toast('Course deleted');
    } catch (e) {
        toast(e.message, true);
    }
}

// ---------------- PAYMENTS MANAGEMENT ----------------

function renderPayments() {
    const body = $('paymentsTable');
    if (!body) return;

    const q = ($('paymentSearch')?.value || '').toLowerCase().trim();
    const list = data.payments.filter(p => {
        return !q || (
            (p.student_name || '').toLowerCase().includes(q) ||
            (p.receipt_no || '').toLowerCase().includes(q) ||
            (p.fee_type || '').toLowerCase().includes(q)
        );
    });

    if (!list.length) {
        body.innerHTML = '<tr><td colspan="8" class="empty-state">No payment records found.</td></tr>';
        return;
    }

    body.innerHTML = list.map(p => `
        <tr>
            <td><strong style="color:var(--primary); font-size:12px;">${safe(p.receipt_no)}</strong></td>
            <td><strong>${safe(p.student_name)}</strong></td>
            <td>${safe(p.fee_type)}</td>
            <td><strong style="color: #1ba982;">${money(p.amount)}</strong></td>
            <td>${safe(p.payment_mode)}</td>
            <td><span class="status-pill approved">${safe(p.status)}</span></td>
            <td>${safe(p.created_at)}</td>
            <td style="text-align: right;">
                <button class="danger-btn" style="padding: 5px 8px; font-size: 12px;" onclick="deletePayment(${p.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function openPaymentModal() {
    fillSelects();
    $('paymentForm').reset();
    openModal('paymentModal');
}

async function submitPaymentForm(e) {
    e.preventDefault();
    const payload = {
        student_name: $('paymentStudent').value.trim(),
        fee_type: $('paymentType').value,
        amount: parseFloat($('paymentAmount').value),
        payment_mode: $('paymentMode').value,
        reference_no: $('paymentRef').value.trim()
    };

    try {
        await api('/api/admin/payments', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        closeModal('paymentModal');
        await refresh();
        toast('Fee payment recorded successfully');
    } catch (err) {
        toast(err.message, true);
    }
}

async function deletePayment(id) {
    if (!confirm('Are you sure you want to delete this payment record?')) return;
    try {
        await api(`/api/admin/payments/${id}`, { method: 'DELETE' });
        await refresh();
        toast('Payment record removed');
    } catch (e) {
        toast(e.message, true);
    }
}

// ---------------- REPORTS & ANALYTICS ----------------

function renderReports() {
    const total = data.applications.length;
    const approved = data.applications.filter(a => a.status === 'Approved').length;
    const pending = data.applications.filter(a => a.status === 'Pending').length;
    const rejected = data.applications.filter(a => a.status === 'Rejected').length;

    setText('reportApplications', total);
    setText('reportApproved', approved);
    setText('reportPending', pending);
    setText('reportRejected', rejected);

    const body = $('courseReportTable');
    if (!body) return;

    if (!data.courses.length) {
        body.innerHTML = '<tr><td colspan="6">No course capacity data.</td></tr>';
        return;
    }

    body.innerHTML = data.courses.map(c => {
        const enrolled = data.students.filter(s => s.course === c.name).length;
        const available = Math.max(0, c.seats - enrolled);
        const utilization = Math.round((enrolled / (c.seats || 1)) * 100);
        return `
            <tr>
                <td><strong>${safe(c.name)}</strong></td>
                <td>${safe(c.duration)}</td>
                <td>${safe(c.seats)} Seats</td>
                <td><strong>${enrolled}</strong></td>
                <td><span style="color:${available < 10 ? '#c62828' : '#1ba982'}; font-weight:700;">${available}</span></td>
                <td>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div style="flex:1; height:6px; background:#f0efff; border-radius:4px; overflow:hidden;">
                            <div style="width:${Math.min(100, utilization)}%; height:100%; background:var(--primary);"></div>
                        </div>
                        <span style="font-size:11px; font-weight:600;">${utilization}%</span>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function printReport() {
    window.print();
}

// ---------------- SETTINGS & PASSWORD CHANGE ----------------

async function changeAdminPassword(e) {
    e.preventDefault();
    const cur = $('currentAdminPassword').value;
    const nw = $('newAdminPassword').value;
    const cnf = $('confirmAdminPassword').value;

    if (nw !== cnf) {
        toast('New passwords do not match!', true);
        return;
    }

    try {
        const res = await api('/api/admin/change-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: cur,
                new_password: nw,
                confirm_password: cnf
            })
        });
        $('changePasswordForm').reset();
        toast(res.message || 'Password changed successfully!');
    } catch (err) {
        toast(err.message, true);
    }
}

// ---------------- SELECT FILLING ----------------

function fillSelects() {
    // Fill course selects
    const crsSelects = ['applicantCourse', 'studentCourse', 'applicationCourseFilter', 'studentCourseFilter'];
    crsSelects.forEach(id => {
        const el = $(id);
        if (!el) return;
        const oldVal = el.value;
        const isFilter = id.includes('Filter');
        el.innerHTML = (isFilter ? '<option value="">All Programmes</option>' : '<option value="">-- Select Programme --</option>') +
            data.courses.map(c => `<option value="${safe(c.name)}">${safe(c.name)}</option>`).join('');
        if (oldVal) el.value = oldVal;
    });

    // Fill student autocomplete for payments
    const studentInput = $('paymentStudent');
    if (studentInput && data.students.length) {
        // Datalist for autocomplete
        let dl = $('studentDataList');
        if (!dl) {
            dl = document.createElement('datalist');
            dl.id = 'studentDataList';
            document.body.appendChild(dl);
            studentInput.setAttribute('list', 'studentDataList');
        }
        dl.innerHTML = data.students.map(s => `<option value="${safe(s.name)}">${safe(s.student_id)}</option>`).join('');
    }
}

// ---------------- CSV EXPORT ----------------

function exportCSV(table) {
    window.location.href = `/api/admin/export/${table}`;
    toast(`Downloading ${table} CSV report...`);
}

// ---------------- MODAL HELPERS ----------------

function openModal(id) {
    const m = $(id);
    if (m) m.classList.add('open');
}

function closeModal(id) {
    const m = $(id);
    if (m) m.classList.remove('open');
}

function openApplicationModal() {
    fillSelects();
    $('applicationForm').reset();
    openModal('applicationModal');
}

// ---------------- INITIALIZATION ----------------

document.addEventListener('DOMContentLoaded', async () => {
    // Search & Filter event listeners
    ['applicationSearch', 'studentSearch', 'paymentSearch', 'applicationStatusFilter', 'applicationCourseFilter', 'studentCourseFilter'].forEach(id => {
        $(id)?.addEventListener('input', () => {
            renderApps();
            renderStudents();
            renderPayments();
        });
    });

    // Close modals on background click
    document.querySelectorAll('.modal-overlay').forEach(m => {
        m.addEventListener('click', e => {
            if (e.target === m) m.classList.remove('open');
        });
    });

    // College profile settings form
    $('settingsForm')?.addEventListener('submit', e => {
        e.preventDefault();
        toast('College settings saved.');
    });

    // Check if admin is already logged in
    try {
        const res = await api('/api/admin/data');
        data = res;
        $('loginScreen').classList.add('hidden');
        $('app').classList.remove('hidden');
        renderAll();
    } catch {
        // Not logged in; remain on login screen
    }
});

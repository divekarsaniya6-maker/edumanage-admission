// ================= EDUMANAGE PUBLIC PORTAL SCRIPT =================

function $(id) {
    return document.getElementById(id);
}

function showToast(msg, isError = false) {
    const container = $('toastContainer') || document.body;
    const el = document.createElement('div');
    el.className = 'toast' + (isError ? ' error' : '');
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => {
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 300);
    }, 3500);
}

function togglePubNav() {
    const links = $('pubNavLinks');
    if (links) links.classList.toggle('open');
}

function closePubNav() {
    const links = $('pubNavLinks');
    if (links) links.classList.remove('open');
}

// Pre-select course from course card and scroll to application form
function selectCourseToApply(courseName) {
    const select = $('appCourseSelect');
    if (select) {
        let found = false;
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value === courseName || select.options[i].text.includes(courseName)) {
                select.selectedIndex = i;
                found = true;
                break;
            }
        }
        if (!found) {
            const opt = new Option(courseName, courseName);
            select.add(opt);
            select.value = courseName;
        }
    }
    const applySec = $('apply');
    if (applySec) {
        applySec.scrollIntoView({ behavior: 'smooth' });
    }
    showToast(`Selected "${courseName}". Complete your details below.`);
}

// Handle Online Admission Form Submission
async function submitAdmissionForm(e) {
    e.preventDefault();

    const alertBox = $('formAlertBox');
    alertBox.className = 'alert-box hidden';
    alertBox.textContent = '';

    const btn = $('submitAppBtn');
    const btnText = $('submitBtnText');
    const spinner = $('submitSpinner');

    // Validation
    const name = $('appName').value.trim();
    const dob = $('appDob').value;
    const gender = $('appGender').value;
    const guardianName = $('appGuardian').value.trim();
    const guardianPhone = $('appGuardianPhone').value.trim();
    const email = $('appEmail').value.trim();
    const phone = $('appPhone').value.trim();
    const address = $('appAddress').value.trim();
    const city = $('appCity').value.trim();
    const state = $('appState').value.trim();
    const pincode = $('appPincode').value.trim();
    const qualification = $('appQual').value;
    const board = $('appBoard').value.trim();
    const year = $('appYear').value;
    const marks = $('appMarks').value;
    const course = $('appCourseSelect').value;
    const declared = $('appDeclare').checked;

    if (!declared) {
        alertBox.className = 'alert-box error';
        alertBox.textContent = 'Please check the declaration box before submitting.';
        return;
    }

    const payload = {
        name, dob, gender,
        guardian_name: guardianName,
        guardian_phone: guardianPhone,
        email, phone, address, city, state, pincode,
        qualification,
        board_university: board,
        passing_year: year,
        percentage: parseFloat(marks),
        course_name: course
    };

    btn.disabled = true;
    btnText.textContent = 'Submitting Application...';
    spinner.classList.remove('hidden');

    try {
        const response = await fetch('/api/public/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Submission failed. Please verify your details.');
        }

        // Show Success Modal
        showSuccessModal(data);
        $('publicAdmissionForm').reset();
    } catch (err) {
        alertBox.className = 'alert-box error';
        alertBox.textContent = err.message;
        alertBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Submit Admission Application';
        spinner.classList.add('hidden');
    }
}

let lastSubmittedData = null;

function showSuccessModal(data) {
    lastSubmittedData = data;
    const app = data.application || {};
    $('modalAppNumber').textContent = data.app_number;
    
    const box = $('modalDetailsBox');
    box.innerHTML = `
        <div class="detail-row"><span>Student Name:</span><strong>${escapeHtml(app.name || '')}</strong></div>
        <div class="detail-row"><span>Course Applied:</span><strong>${escapeHtml(app.course || '')}</strong></div>
        <div class="detail-row"><span>Registered Email:</span><strong>${escapeHtml(app.email || '')}</strong></div>
        <div class="detail-row"><span>Registered Phone:</span><strong>${escapeHtml(app.phone || '')}</strong></div>
        <div class="detail-row"><span>Submission Date:</span><strong>${escapeHtml(app.submitted_at || new Date().toLocaleString())}</strong></div>
        <div class="detail-row"><span>Current Status:</span><strong style="color:#b78103">Pending Review</strong></div>
    `;

    $('successModal').classList.add('open');
}

function closeSuccessModal() {
    $('successModal').classList.remove('open');
}

function goToTrackFromSuccess() {
    closeSuccessModal();
    if (lastSubmittedData) {
        $('trackAppNo').value = lastSubmittedData.app_number || '';
        $('trackVerification').value = (lastSubmittedData.application && lastSubmittedData.application.phone) || '';
        $('track').scrollIntoView({ behavior: 'smooth' });
        setTimeout(() => {
            $('trackBtn').click();
        }, 500);
    } else {
        $('track').scrollIntoView({ behavior: 'smooth' });
    }
}

function printApplicationReceipt() {
    if (!lastSubmittedData) return;
    const app = lastSubmittedData.application || {};
    const win = window.open('', '_blank');
    win.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admission Acknowledgement Slip - ${lastSubmittedData.app_number}</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; color: #1d2440; max-width: 700px; margin: 0 auto; }
                .slip-header { border-bottom: 2px solid #6558e8; padding-bottom: 18px; margin-bottom: 24px; text-align: center; }
                .slip-logo { font-size: 24px; font-weight: 800; color: #6558e8; }
                .slip-title { font-size: 18px; font-weight: 700; margin: 8px 0 4px; }
                .slip-subtitle { font-size: 13px; color: #666; }
                .app-box { background: #f6f7fc; border: 1px dashed #6558e8; padding: 18px; border-radius: 8px; text-align: center; margin-bottom: 24px; }
                .app-box strong { font-size: 24px; color: #6558e8; display: block; margin-top: 5px; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
                th, td { padding: 10px 12px; border: 1px solid #ddd; font-size: 14px; text-align: left; }
                th { background: #f0efff; color: #333; width: 35%; }
                .notice { font-size: 12px; color: #555; line-height: 1.6; border-top: 1px solid #eee; padding-top: 15px; }
                @media print { .no-print { display: none; } }
            </style>
        </head>
        <body>
            <div class="slip-header">
                <div class="slip-logo">EduManage College of Higher Education</div>
                <div class="slip-title">ONLINE ADMISSION APPLICATION ACKNOWLEDGEMENT (2026–27)</div>
                <div class="slip-subtitle">Kharghar, Navi Mumbai - 410210, Maharashtra, India</div>
            </div>

            <div class="app-box">
                <div>OFFICIAL APPLICATION NUMBER</div>
                <strong>${lastSubmittedData.app_number}</strong>
            </div>

            <table>
                <tr><th>Applicant Name</th><td>${escapeHtml(app.name || '')}</td></tr>
                <tr><th>Course / Programme</th><td>${escapeHtml(app.course || '')}</td></tr>
                <tr><th>Registered Email</th><td>${escapeHtml(app.email || '')}</td></tr>
                <tr><th>Registered Mobile</th><td>${escapeHtml(app.phone || '')}</td></tr>
                <tr><th>Application Date</th><td>${escapeHtml(app.submitted_at || new Date().toLocaleString())}</td></tr>
                <tr><th>Initial Status</th><td>Pending Review</td></tr>
            </table>

            <div class="notice">
                <strong>Important Instructions:</strong>
                <ol>
                    <li>Please retain this acknowledgement slip for future reference during document verification and counseling.</li>
                    <li>Merit lists and verification schedules will be published online. Track your application status anytime at the EduManage portal.</li>
                    <li>For inquiries, contact the admissions desk at admissions@edumanage.edu.in or call +91 (022) 2774-8800.</li>
                </ol>
            </div>

            <div class="no-print" style="text-align: center; margin-top: 30px;">
                <button onclick="window.print()" style="padding: 10px 24px; font-size: 14px; font-weight: bold; background: #6558e8; color: white; border: none; border-radius: 6px; cursor: pointer;">Print Acknowledgement</button>
            </div>
        </body>
        </html>
    `);
    win.document.close();
}

// Track Application Status Functionality
async function trackApplication(e) {
    e.preventDefault();

    const appNo = $('trackAppNo').value.trim();
    const verification = $('trackVerification').value.trim();
    const container = $('trackResultContainer');
    const btn = $('trackBtn');
    const btnText = $('trackBtnText');
    const spinner = $('trackSpinner');

    btn.disabled = true;
    btnText.textContent = 'Verifying...';
    spinner.classList.remove('hidden');

    try {
        const response = await fetch('/api/public/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ app_number: appNo, verification })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Verification failed. Application not found.');
        }

        renderTrackResult(data.application);
    } catch (err) {
        container.className = 'track-result-box';
        container.innerHTML = `
            <div class="alert-box error" style="margin: 0">
                <strong>Lookup Failed:</strong> ${escapeHtml(err.message)}
            </div>
        `;
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Verify & Check';
        spinner.classList.add('hidden');
    }
}

function renderTrackResult(app) {
    const container = $('trackResultContainer');
    container.classList.remove('hidden');

    const statusMap = {
        'Pending': { class: 'pending', label: '🟡 Pending Review' },
        'Under Review': { class: 'under-review', label: '🔵 Under Review' },
        'Approved': { class: 'approved', label: '🟢 Approved / Admitted' },
        'Rejected': { class: 'rejected', label: '🔴 Application Rejected' }
    };

    const statusInfo = statusMap[app.status] || { class: 'pending', label: app.status };

    container.innerHTML = `
        <div class="track-status-header">
            <div>
                <span style="font-size: 11px; color: var(--muted); font-weight: 700; letter-spacing: 1px;">APPLICATION NUMBER</span>
                <div class="track-app-id">${escapeHtml(app.app_number)}</div>
            </div>
            <div>
                <span class="status-pill ${statusInfo.class}">${statusInfo.label}</span>
            </div>
        </div>

        <div class="track-info-grid">
            <div class="track-info-item">
                <span>Applicant Name</span>
                <strong>${escapeHtml(app.masked_name)}</strong>
            </div>
            <div class="track-info-item">
                <span>Programme</span>
                <strong>${escapeHtml(app.course)}</strong>
            </div>
            <div class="track-info-item">
                <span>Submitted On</span>
                <strong>${escapeHtml(app.submitted_at)}</strong>
            </div>
        </div>

        <div class="track-remarks-box">
            <strong>Admissions Office Update & Remarks:</strong>
            ${escapeHtml(app.admin_remarks || 'Your application is currently under normal review by the committee.')}
        </div>

        ${app.status === 'Approved' ? `
            <div style="margin-top: 18px; background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 10px; padding: 14px; text-align: center; color: #1b5e20;">
                <strong>🎉 Congratulations!</strong> Your admission has been approved. Please report to the administration office with original documents or contact the admissions helpline to complete enrollment.
            </div>
        ` : ''}
    `;

    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, c => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[c]));
}

// Check URL hash on load (e.g. #track)
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.hash === '#track') {
        const trackSec = $('track');
        if (trackSec) trackSec.scrollIntoView({ behavior: 'smooth' });
    }
});

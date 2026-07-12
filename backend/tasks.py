import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

# Celery background tasks for reminders, reports and exports

celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

celery_app.conf.beat_schedule = {
    'daily-deadline-reminders': {
        'task': 'tasks.send_daily_reminders',
        'schedule': crontab(hour=0, minute=0),
    },
    'monthly-admin-report': {
        'task': 'tasks.generate_monthly_report',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },
}
celery_app.conf.timezone = 'UTC'

# ---------------- Notification config (set as environment variables) ----------------
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@institute.edu')
GCHAT_WEBHOOK_URL = os.environ.get('GCHAT_WEBHOOK_URL', '')

def _send_email(to_email, subject, html_body):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD):
        print(f"[Mailer] SMTP not configured. Would have sent to {to_email}: {subject}")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[Mailer] Failed to send email to {to_email}: {e}")
        return False

def _send_gchat(text):
    if not GCHAT_WEBHOOK_URL:
        print(f"[GChat] Webhook not configured. Would have posted: {text}")
        return False
    try:
        import requests
        requests.post(GCHAT_WEBHOOK_URL, json={"text": text}, timeout=5)
        return True
    except Exception as e:
        print(f"[GChat] Failed to post message: {e}")
        return False

@celery_app.task
def export_applications_to_csv(company_id):
    """Asynchronous background task compiling application lists to disk CSV formats."""
    from app import create_app
    from models import db, Application, StudentProfile, PlacementDrive
    flask_app = create_app()

    with flask_app.app_context():
        drives = PlacementDrive.query.filter_by(company_id=company_id).all()
        drive_ids = [d.id for d in drives]
        apps = Application.query.filter(Application.drive_id.in_(drive_ids)).all() if drive_ids else []

        static_dir = os.path.join(flask_app.root_path, '..', 'frontend', 'exports')
        os.makedirs(static_dir, exist_ok=True)

        filename = f"company_{company_id}_applicants.csv"
        filepath = os.path.join(static_dir, filename)

        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Application ID', 'Candidate Name', 'Branch', 'CGPA', 'Job Title', 'Current Status', 'Scheduled Interview'])
            for a in apps:
                student = StudentProfile.query.filter_by(user_id=a.student_id).first()
                drive = db.session.get(PlacementDrive, a.drive_id)
                writer.writerow([
                    a.id,
                    student.name if student else 'Unknown',
                    student.branch if student else 'N/A',
                    student.cgpa if student else 0.0,
                    drive.job_title if drive else 'Unknown',
                    a.status,
                    a.interview_date if a.interview_date else 'Not Scheduled'
                ])
        return f"/exports/{filename}"

@celery_app.task
def export_student_history_to_csv(student_user_id):
    """Asynchronous student task compiling history lists to disk CSV."""
    from app import create_app
    from models import db, Application, PlacementDrive, CompanyProfile
    flask_app = create_app()

    with flask_app.app_context():
        apps = Application.query.filter_by(student_id=student_user_id).all()

        static_dir = os.path.join(flask_app.root_path, '..', 'frontend', 'exports')
        os.makedirs(static_dir, exist_ok=True)

        filename = f"student_{student_user_id}_history.csv"
        filepath = os.path.join(static_dir, filename)

        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Student ID', 'Company Name', 'Drive Title', 'Application Status', 'Scheduled Interview'])

            for a in apps:
                drive = db.session.get(PlacementDrive, a.drive_id)
                company_name = "Unknown Company"

                if drive:
                    company = db.session.get(CompanyProfile, drive.company_id)
                    if company:
                        company_name = company.name

                i_date = 'Not Scheduled'
                if hasattr(a, 'interview_date') and a.interview_date:
                    i_date = a.interview_date

                writer.writerow([
                    student_user_id,
                    company_name,
                    drive.job_title if drive else 'Unknown Role',
                    getattr(a, 'status', 'Applied'),
                    i_date
                ])
        return f"/exports/{filename}"

@celery_app.task
def send_daily_reminders():
    """Reminds students, via email/GChat, about drives closing within 3 days that they're eligible for and haven't applied to."""
    from app import create_app
    from models import db, PlacementDrive, Application, User, StudentProfile
    flask_app = create_app()

    with flask_app.app_context():
        upcoming_cutoff = datetime.utcnow() + timedelta(days=3)
        drives = PlacementDrive.query.filter(
            PlacementDrive.status == 'Approved',
            PlacementDrive.deadline >= datetime.utcnow(),
            PlacementDrive.deadline <= upcoming_cutoff
        ).all()

        if not drives:
            print("[Celery Beat] No drives closing within the next 3 days.")
            return "No reminders to send."

        students = User.query.filter_by(role='student', is_active=True).all()
        applied_pairs = {(a.student_id, a.drive_id) for a in Application.query.all()}

        reminders_sent = 0
        for student in students:
            profile = StudentProfile.query.filter_by(user_id=student.id).first()
            eligible_drives = []
            for d in drives:
                if (student.id, d.id) in applied_pairs:
                    continue
                if profile and profile.cgpa and profile.cgpa < d.cgpa_eligibility:
                    continue
                eligible_drives.append(d)

            if not eligible_drives:
                continue

            drive_lines = "".join(
                f"<li><b>{d.job_title}</b> — closes {d.deadline.strftime('%Y-%m-%d')}</li>"
                for d in eligible_drives
            )
            html = f"""<p>Hi {profile.name if profile else student.email},</p>
<p>The following placement drives you're eligible for are closing soon:</p>
<ul>{drive_lines}</ul>
<p>Log in to the portal to apply before the deadline.</p>"""

            if _send_email(student.email, "Placement Drive Deadlines Closing Soon", html):
                reminders_sent += 1
            _send_gchat(f"Reminder sent to {student.email} for {len(eligible_drives)} closing drive(s).")

        print(f"[Celery Beat] Daily reminder job complete. {reminders_sent} reminder(s) sent.")
        return f"Daily reminders run completed. {reminders_sent} sent."

@celery_app.task
def generate_monthly_report():
    """Builds an HTML placement activity report and emails it to admin, saving a copy to disk."""
    from app import create_app
    from models import db, PlacementDrive, Application, CompanyProfile, User, Placement
    flask_app = create_app()

    with flask_app.app_context():
        total_drives = PlacementDrive.query.filter_by(status='Approved').count()
        total_applications = Application.query.count()
        total_selected = Application.query.filter_by(status='Selected').count()
        total_placements = Placement.query.count()
        total_students = User.query.filter_by(role='student').count()
        total_companies = CompanyProfile.query.filter_by(is_approved=True).count()

        html = f"""<html><body style="font-family: Arial, sans-serif;">
<h2>Monthly Placement Activity Report</h2>
<p>Generated on {datetime.utcnow().strftime('%Y-%m-%d')}</p>
<table border="1" cellpadding="8" cellspacing="0">
<tr><td>Active Students</td><td>{total_students}</td></tr>
<tr><td>Approved Companies</td><td>{total_companies}</td></tr>
<tr><td>Approved Placement Drives</td><td>{total_drives}</td></tr>
<tr><td>Total Applications</td><td>{total_applications}</td></tr>
<tr><td>Students Selected</td><td>{total_selected}</td></tr>
<tr><td>Confirmed Placements</td><td>{total_placements}</td></tr>
</table>
</body></html>"""

        static_dir = os.path.join(flask_app.root_path, '..', 'frontend', 'exports')
        os.makedirs(static_dir, exist_ok=True)
        filename = f"monthly_report_{datetime.utcnow().strftime('%Y_%m')}.html"
        filepath = os.path.join(static_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        sent = _send_email(ADMIN_EMAIL, "Monthly Placement Activity Report", html)
        print(f"[Celery Beat] Monthly report generated at /exports/{filename}. Emailed: {sent}")
        return f"/exports/{filename}"
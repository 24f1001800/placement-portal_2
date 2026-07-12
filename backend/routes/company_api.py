import os
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, PlacementDrive, CompanyProfile, Application, StudentProfile, Placement
from datetime import datetime
from tasks import export_applications_to_csv, celery_app

# Company APIs for drives, applicants, interviews and placements

company_bp = Blueprint('company_bp', __name__)

def get_company():
    identity = get_jwt_identity()
    try:
        user = db.session.get(User, int(str(identity)))
    except (ValueError, TypeError):
        return None
    if not user or user.role != 'company' or not user.is_active:
        return None
    return CompanyProfile.query.filter_by(user_id=user.id).first()

def _ensure_placement_record(company, application):
    """Creates a Placement + a generated offer letter the first time a candidate is marked Selected."""
    existing = Placement.query.filter_by(application_id=application.id).first()
    if existing:
        return existing

    drive = db.session.get(PlacementDrive, application.drive_id)
    student_profile = StudentProfile.query.filter_by(user_id=application.student_id).first()

    placement = Placement(
        student_id=application.student_id,
        company_id=company.id,
        application_id=application.id,
        position=drive.job_title if drive else 'Not Specified',
        salary='To be confirmed by HR',
        joining_date=''
    )
    db.session.add(placement)
    db.session.flush()

    static_dir = os.path.join(os.getcwd(), '..', 'frontend', 'exports')
    os.makedirs(static_dir, exist_ok=True)
    filename = f"offer_letter_{placement.id}.html"
    filepath = os.path.join(static_dir, filename)

    candidate_name = student_profile.name if student_profile else 'Candidate'
    html = f"""<html><body style="font-family: Georgia, serif; padding: 40px;">
<h2>{company.name}</h2>
<p>Date: {datetime.utcnow().strftime('%Y-%m-%d')}</p>
<p>Dear {candidate_name},</p>
<p>We are pleased to offer you the position of <b>{placement.position}</b> at {company.name}
through the Campus Recruitment Portal. Congratulations on your selection!</p>
<p>Further details regarding compensation and joining date will be communicated by HR separately.</p>
<p>Warm regards,<br>{company.name} Talent Acquisition Team</p>
</body></html>"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    placement.offer_letter_url = f"/exports/{filename}"
    db.session.commit()
    return placement

@company_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    comp = get_company()
    if not comp: return jsonify({"message": "Unauthorized"}), 403
    return jsonify({"id": comp.id, "name": comp.name, "is_approved": comp.is_approved}), 200

@company_bp.route('/drives', methods=['GET', 'POST'])
@jwt_required()
def manage_drives():
    comp = get_company()
    if not comp or not comp.is_approved:
        return jsonify({"message": "Access restricted to verified companies only."}), 403

    if request.method == 'POST':
        data = request.get_json()
        job_title = data.get('job_title', '').strip()
        description = data.get('description', '').strip()
        branch_eligibility = data.get('branch_eligibility', '').strip()

        if not job_title or not description or not branch_eligibility:
            return jsonify({"message": "Validation Error: All campaign attributes are mandatory."}), 400

        try:
            cgpa_req = float(data.get('cgpa_eligibility'))
            if cgpa_req < 0.0 or cgpa_req > 10.0:
                return jsonify({"message": "Validation Error: CGPA criteria must match standard bounds (0-10)."}), 400
        except:
            return jsonify({"message": "Validation Error: Invalid criteria format."}), 400

        try:
            d_date = datetime.strptime(data.get('deadline'), '%Y-%m-%d')
            if d_date < datetime.utcnow():
                return jsonify({"message": "Validation Error: Campaign deadline must be a future date."}), 400
        except:
            return jsonify({"message": "Validation Error: Incorrect deadline date configuration."}), 400

        db.session.add(PlacementDrive(
            company_id=comp.id, job_title=job_title, description=description,
            branch_eligibility=branch_eligibility, cgpa_eligibility=cgpa_req,
            deadline=d_date, status='Pending'
        ))
        db.session.commit()
        return jsonify({"message": "Drive strategy locked and submitted for administrative approval!"}), 201

    drives = PlacementDrive.query.filter_by(company_id=comp.id).all()
    return jsonify([{"id": d.id, "job_title": d.job_title, "status": d.status, "deadline": d.deadline.strftime('%Y-%m-%d')} for d in drives]), 200

@company_bp.route('/applicants', methods=['GET'])
@jwt_required()
def get_applicants():
    comp = get_company()
    if not comp: return jsonify({"message": "Unauthorized"}), 403

    drives = PlacementDrive.query.filter_by(company_id=comp.id).all()
    drive_ids = [d.id for d in drives]

    apps = Application.query.filter(Application.drive_id.in_(drive_ids)).all()
    result = []
    for a in apps:
        s_prof = StudentProfile.query.filter_by(user_id=a.student_id).first()
        drive = db.session.get(PlacementDrive, a.drive_id)
        result.append({
            "application_id": a.id, "job_title": drive.job_title if drive else "Unknown",
            "student_name": s_prof.name if s_prof else "Unknown", "branch": s_prof.branch if s_prof else "N/A",
            "cgpa": s_prof.cgpa if s_prof else 0.0, "resume_url": s_prof.resume_url if s_prof else "",
            "status": a.status, "interview_date": a.interview_date
        })
    return jsonify(result), 200

@company_bp.route('/applicants/review', methods=['POST'])
@jwt_required()
def review_applicant():
    comp = get_company()
    if not comp: return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    app_record = db.session.get(Application, data.get('application_id'))
    if not app_record: return jsonify({"message": "Application entry not found."}), 404

    app_record.status = data.get('status', app_record.status)
    if 'interview_date' in data:
        app_record.interview_date = data.get('interview_date') or ''
    db.session.commit()

    if app_record.status == 'Selected':
        _ensure_placement_record(comp, app_record)

    return jsonify({"message": f"Candidate status updated to {app_record.status}!"}), 200

@company_bp.route('/export-applicants', methods=['POST'])
@jwt_required()
def trigger_company_export():
    comp = get_company()
    if not comp: return jsonify({"message": "Unauthorized"}), 403
    task = export_applications_to_csv.delay(comp.id)
    return jsonify({"task_id": task.id, "message": "Asynchronous data compilation initialized."}), 202

@company_bp.route('/export-status/<task_id>', methods=['GET'])
@jwt_required()
def company_export_status(task_id):
    task = celery_app.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        return jsonify({"status": "COMPLETED", "download_url": task.result}), 200
    elif task.state == 'FAILURE':
        return jsonify({"status": "FAILED"}), 500
    return jsonify({"status": "PENDING"}), 200
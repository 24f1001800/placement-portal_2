import os
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, PlacementDrive, Application, StudentProfile, CompanyProfile, Placement
from tasks import export_student_history_to_csv, celery_app
from flask_caching import Cache

# Student APIs for profiles, applications and placement tracking

student_bp = Blueprint('student_bp', __name__)

cache = Cache(config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})

def get_current_student():
    identity = get_jwt_identity()
    try:
        user = db.session.get(User, int(str(identity)))
    except (ValueError, TypeError):
        return None
    if not user or user.role != 'student' or not user.is_active:
        return None
    return user

@student_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_student_profile():
    user = get_current_student()
    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        return jsonify({"name": "", "branch": "", "cgpa": 0.0, "year": 4, "contact": "", "resume_url": ""}), 200

    return jsonify({
        "name": profile.name,
        "branch": profile.branch,
        "cgpa": profile.cgpa,
        "year": profile.year,
        "contact": profile.contact,
        "resume_url": profile.resume_url
    }), 200

@student_bp.route('/profile', methods=['POST'])
@jwt_required()
def save_student_profile():
    user = get_current_student()
    if not user:
        return jsonify({"message": "No valid student profile context found."}), 404

    data = request.json or {}
    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.session.add(profile)

    profile.name = data.get('name', '').strip() or user.email.split('@')[0]
    profile.branch = data.get('branch', '').strip() or 'Computer Science'
    profile.contact = data.get('contact', '').strip()

    try:
        profile.cgpa = float(data.get('cgpa') or 0.0)
    except (ValueError, TypeError):
        profile.cgpa = 0.0

    try:
        profile.year = int(data.get('year') or 4)
    except (ValueError, TypeError):
        profile.year = 4

    db.session.commit()
    return jsonify({"message": "Profile cached safely!"}), 200

@student_bp.route('/upload-resume', methods=['POST'])
@jwt_required()
def upload_student_resume():
    user = get_current_student()
    if not user:
        return jsonify({"message": "Access restricted to valid student tokens."}), 403

    if 'resume' not in request.files:
        return jsonify({"message": "No file stream detected."}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({"message": "Empty file name chosen."}), 400

    static_dir = os.path.join(os.getcwd(), '..', 'frontend', 'uploads')
    os.makedirs(static_dir, exist_ok=True)

    filename = f"student_{user.id}_resume.pdf"
    filepath = os.path.join(static_dir, filename)
    file.save(filepath)

    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = StudentProfile(user_id=user.id, name=user.email.split('@')[0])
        db.session.add(profile)

    profile.resume_url = f"/uploads/{filename}"
    db.session.commit()

    return jsonify({"message": "Official resume uploaded and saved successfully!", "resume_url": profile.resume_url}), 200

@student_bp.route('/drives/approved', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60)
def get_approved_drives():
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    result = []
    for d in drives:
        company = CompanyProfile.query.get(d.company_id)
        comp_name = company.name if company else "Unknown Company"
        result.append({
            "id": d.id,
            "job_title": d.job_title,
            "company_name": comp_name,
            "description": d.description,
            "cgpa_eligibility": d.cgpa_eligibility,
            "branch_eligibility": d.branch_eligibility,
            "deadline": d.deadline
        })
    return jsonify(result), 200

@student_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_student_applications():
    user = get_current_student()
    if not user:
        return jsonify([]), 200

    apps = Application.query.filter_by(student_id=user.id).all()
    result = []
    for a in apps:
        drive = db.session.get(PlacementDrive, a.drive_id)
        comp_name = "Unknown Company"
        job_title = "Unknown Role"
        if drive:
            job_title = drive.job_title
            company = CompanyProfile.query.get(drive.company_id)
            if company:
                comp_name = company.name

        result.append({
            "company_name": comp_name,
            "job_title": job_title,
            "status": a.status,
            "interview_date": a.interview_date
        })
    return jsonify(result), 200

@student_bp.route('/placements', methods=['GET'])
@jwt_required()
def get_student_placements():
    user = get_current_student()
    if not user:
        return jsonify([]), 200

    placements = Placement.query.filter_by(student_id=user.id).all()
    result = []
    for p in placements:
        company = CompanyProfile.query.get(p.company_id)
        result.append({
            "id": p.id,
            "company_name": company.name if company else "Unknown",
            "position": p.position,
            "salary": p.salary,
            "joining_date": p.joining_date,
            "offer_letter_url": p.offer_letter_url
        })
    return jsonify(result), 200

@student_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_to_drive():
    user = get_current_student()
    if not user:
        return jsonify({"message": "Access restricted to valid student tokens."}), 403

    data = request.json
    drive_id = data.get('drive_id')

    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    if not profile or not profile.cgpa:
        return jsonify({"message": "Please configure your academic profile metrics first."}), 400

    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({"message": "Drive not found"}), 404

    if profile.cgpa < drive.cgpa_eligibility:
        return jsonify({"message": f"Application rejected. Minimum required CGPA is {drive.cgpa_eligibility}."}), 400

    existing = Application.query.filter_by(student_id=user.id, drive_id=drive_id).first()
    if existing:
        return jsonify({"message": "You have already applied to this recruitment campaign."}), 400

    new_app = Application(student_id=user.id, drive_id=drive_id, status='Applied')
    db.session.add(new_app)
    db.session.commit()
    return jsonify({"message": "Application submitted successfully!"}), 200

@student_bp.route('/export-history', methods=['POST'])
@jwt_required()
def trigger_student_history_export():
    user = get_current_student()
    if not user:
        return jsonify({"message": "Access restricted to valid student tokens."}), 403

    task = export_student_history_to_csv.delay(user.id)
    return jsonify({"task_id": task.id, "message": "Asynchronous data compilation initialized."}), 202

@student_bp.route('/export-status/<task_id>', methods=['GET'])
@jwt_required()
def get_student_export_status(task_id):
    task = celery_app.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        return jsonify({"status": "COMPLETED", "download_url": task.result}), 200
    elif task.state == 'FAILURE':
        return jsonify({"status": "FAILED"}), 500
    return jsonify({"status": "PENDING"}), 200
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, CompanyProfile, PlacementDrive, StudentProfile, Application

# Admin management APIs for approvals, searches, and moderation

admin_bp = Blueprint('admin_bp', __name__)

def is_admin():
    identity = get_jwt_identity()
    try:
        user = db.session.get(User, int(str(identity)))
    except (ValueError, TypeError):
        return False
    return bool(user and user.role == 'admin')

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_stats():
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    return jsonify({
        "total_students": User.query.filter_by(role='student').count(),
        "total_companies": CompanyProfile.query.count(),
        "total_drives": PlacementDrive.query.filter_by(status='Approved').count()
    }), 200

# ---------------- Companies: pending approval ----------------

@admin_bp.route('/companies/pending', methods=['GET'])
@jwt_required()
def pending_companies():
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    companies = CompanyProfile.query.filter_by(is_approved=False).all()
    result = []
    for c in companies:
        user = db.session.get(User, c.user_id)
        result.append({
            "id": c.id,
            "company_name": c.name,
            "email": user.email if user else "Unknown"
        })
    return jsonify(result), 200

@admin_bp.route('/companies/approve/<int:company_id>', methods=['POST'])
@jwt_required()
def approve_company(company_id):
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    company = db.session.get(CompanyProfile, company_id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    company.is_approved = True
    db.session.commit()
    return jsonify({"message": f"{company.name} approved successfully!"}), 200

@admin_bp.route('/companies/reject/<int:company_id>', methods=['POST'])
@jwt_required()
def reject_company(company_id):
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    company = db.session.get(CompanyProfile, company_id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    # Auto-reject any drives this company had pending before removing them
    PlacementDrive.query.filter_by(company_id=company.id, status='Pending').update({"status": "Rejected"})
    user = db.session.get(User, company.user_id)
    db.session.delete(company)
    if user:
        db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Company registration rejected and removed."}), 200

# ---------------- Companies: search + blacklist ----------------

@admin_bp.route('/companies', methods=['GET'])
@jwt_required()
def search_companies():
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    query = request.args.get('q', '').strip()
    companies_query = CompanyProfile.query
    if query:
        like_expr = f"%{query}%"
        companies_query = companies_query.filter(
            db.or_(CompanyProfile.name.ilike(like_expr), CompanyProfile.industry.ilike(like_expr))
        )

    result = []
    for c in companies_query.all():
        user = db.session.get(User, c.user_id)
        result.append({
            "id": c.id,
            "user_id": c.user_id,
            "company_name": c.name,
            "email": user.email if user else "Unknown",
            "industry": c.industry,
            "location": c.location,
            "is_approved": c.is_approved,
            "is_active": user.is_active if user else False
        })
    return jsonify(result), 200

@admin_bp.route('/companies/toggle-active/<int:user_id>', methods=['POST'])
@jwt_required()
def toggle_company_active(user_id):
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    user = db.session.get(User, user_id)
    if not user or user.role != 'company':
        return jsonify({"message": "Company account not found."}), 404

    user.is_active = not user.is_active
    db.session.commit()
    state = "reactivated" if user.is_active else "blacklisted"
    return jsonify({"message": f"Company account {state}.", "is_active": user.is_active}), 200

# ---------------- Students: search + blacklist ----------------

@admin_bp.route('/students', methods=['GET'])
@jwt_required()
def search_students():
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    query = request.args.get('q', '').strip().lower()
    students = User.query.filter_by(role='student').all()

    result = []
    for s in students:
        profile = StudentProfile.query.filter_by(user_id=s.id).first()
        if query:
            haystack = " ".join([
                s.email.lower(),
                str(s.id),
                (profile.name.lower() if profile and profile.name else ''),
                (profile.contact.lower() if profile and profile.contact else '')
            ])
            if query not in haystack:
                continue
        result.append({
            "id": s.id,
            "email": s.email,
            "name": profile.name if profile else "Not Set",
            "branch": profile.branch if profile else "N/A",
            "cgpa": profile.cgpa if profile else 0.0,
            "contact": profile.contact if profile else "",
            "is_active": s.is_active
        })
    return jsonify(result), 200

@admin_bp.route('/students/toggle-active/<int:user_id>', methods=['POST'])
@jwt_required()
def toggle_student_active(user_id):
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    user = db.session.get(User, user_id)
    if not user or user.role != 'student':
        return jsonify({"message": "Student account not found."}), 404

    user.is_active = not user.is_active
    db.session.commit()
    state = "reactivated" if user.is_active else "blacklisted"
    return jsonify({"message": f"Student account {state}.", "is_active": user.is_active}), 200

# ---------------- Drives ----------------

@admin_bp.route('/drives/pending', methods=['GET'])
@jwt_required()
def pending_drives():
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    drives = PlacementDrive.query.filter_by(status='Pending').all()
    result = []
    for d in drives:
        company = db.session.get(CompanyProfile, d.company_id)
        result.append({
            "id": d.id,
            "company_name": company.name if company else "Unknown",
            "job_title": d.job_title,
            "branch_eligibility": d.branch_eligibility,
            "cgpa_eligibility": d.cgpa_eligibility,
            "deadline": d.deadline.strftime('%Y-%m-%d')
        })
    return jsonify(result), 200

@admin_bp.route('/drives/approve/<int:drive_id>', methods=['POST'])
@jwt_required()
def approve_drive(drive_id):
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({"message": "Drive campaign not found"}), 404

    drive.status = 'Approved'
    db.session.commit()
    return jsonify({"message": f"Drive for {drive.job_title} approved successfully!"}), 200

@admin_bp.route('/drives/reject/<int:drive_id>', methods=['POST'])
@jwt_required()
def reject_drive(drive_id):
    if not is_admin():
        return jsonify({"message": "Unauthorized access."}), 403

    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({"message": "Drive campaign not found"}), 404

    drive.status = 'Rejected'
    db.session.commit()
    return jsonify({"message": f"Drive for {drive.job_title} rejected."}), 200
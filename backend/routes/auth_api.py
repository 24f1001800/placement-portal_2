from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, CompanyProfile

# JWT authentication and role-based access control routes

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"message": "Your account is deactivated. Contact admin."}), 403

    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "message": "Login successful",
        "token": access_token,
        "role": user.role
    }), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role') # 'student' or 'company'

    if role == 'admin':
        return jsonify({"message": "Admin registration is not allowed"}), 403

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400

    hashed_password = generate_password_hash(password)
    
    new_user = User(email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.flush()

    if role == 'company':
        company_name = data.get('company_name', 'Unnamed Company')
        new_company = CompanyProfile(
            user_id=new_user.id,
            name=company_name,
            industry=data.get('industry', '').strip() or 'Not Specified',
            location=data.get('location', '').strip() or 'Not Specified',
            is_approved=False
        )
        db.session.add(new_company)

    db.session.commit()
    return jsonify({"message": f"{role.capitalize()} registered successfully!"}), 201

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    identity = get_jwt_identity()
    try:
        user = db.session.get(User, int(str(identity)))
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid token identity."}), 400

    if not user:
        return jsonify({"message": "User not found."}), 404

    data = request.get_json() or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if not check_password_hash(user.password, current_password):
        return jsonify({"message": "Current password is incorrect."}), 401

    if not new_password or len(new_password) < 6:
        return jsonify({"message": "New password must be at least 6 characters."}), 400

    user.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated successfully!"}), 200
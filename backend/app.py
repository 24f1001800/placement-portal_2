import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db, User
from werkzeug.security import generate_password_hash
from flask_caching import Cache

def create_app():
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    app.config['SECRET_KEY'] = 'super-secret-key-matrix-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-token-key-789'

    CORS(app)
    JWTManager(app)
    db.init_app(app)

    # MILESTONE REQUIREMENT: Bind Redis Cache
    from routes.student_api import cache
    cache.init_app(app)

    # Register modular routes
    from routes.auth_api import auth_bp
    from routes.admin_api import admin_bp
    from routes.company_api import company_bp
    from routes.student_api import student_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(company_bp, url_prefix='/api/company')
    app.register_blueprint(student_bp, url_prefix='/api/student')

    @app.route('/')
    def serve_frontend():
        return send_from_directory(app.static_folder, 'index.html')

    with app.app_context():
        db.create_all()
        # Admin Seeding
        if not User.query.filter_by(email='admin@institute.edu').first():
            db.session.add(User(
                email='admin@institute.edu',
                password=generate_password_hash('admin123'),
                role='admin'
            ))
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
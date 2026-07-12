# Placement Portal V2 Database Schema

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False) # admin, company, student
    is_active = db.Column(db.Boolean, default=True)

class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(100), default='Not Specified')
    website = db.Column(db.String(200), default='Not Specified')
    industry = db.Column(db.String(100), default='Not Specified')
    location = db.Column(db.String(150), default='Not Specified')
    is_approved = db.Column(db.Boolean, default=False)

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), default='Name Not Set')
    branch = db.Column(db.String(100), default='CSE')
    cgpa = db.Column(db.Float, default=0.0)
    year = db.Column(db.Integer, default=4)
    contact = db.Column(db.String(50), default='')
    resume_url = db.Column(db.String(300), default='')

class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    branch_eligibility = db.Column(db.String(200), nullable=False)
    cgpa_eligibility = db.Column(db.Float, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending, Approved, Rejected

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    status = db.Column(db.String(50), default='Applied') # Applied, Shortlisted, Selected, Rejected
    interview_date = db.Column(db.String(100), default='')
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)

class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False, unique=True)
    position = db.Column(db.String(150), nullable=False)
    salary = db.Column(db.String(100), default='Not Disclosed')
    joining_date = db.Column(db.String(100), default='')
    offer_letter_url = db.Column(db.String(300), default='')
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
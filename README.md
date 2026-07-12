Campus Recruitment Portal Project Overview

A modern, decoupled, role-based application designed to streamline campus placement cycles for Students, Corporate Recruiters, and Institute Administrators.

Architecture and Technical Stack

* Backend Framework: Flask REST API
* Database Engine: SQLite handled via SQLAlchemy Object-Relational Mapping (ORM)
* Authentication Protocol: Stateless authorization using JSON Web Tokens (JWT) via Flask-JWT-Extended
* Frontend Framework: Client-side Single Page Application (SPA) built with Vue.js 3 and Vue Router 4
* UI Design System: Responsive dashboard layout engineered with Bootstrap 5 and Bootstrap Icons

Implemented Core Features

1. Robust Input Validations

* Student Profile Constraints: Enforces strict boundary checks on academic metrics. CGPA submissions are strictly restricted on both client and server-side runtimes to stay between 0.00 and 10.00.
* Campaign Timeline Assertions: Prevents corporate entities from submitting past deadline dates. The backend verifies all job posts against the current date and time.
* Mandatory Attributes Verification: Forms check for missing fields, incomplete records, or missing resume links before executing state changes.

2. Live Client-Side Search and Filter

* Real-Time Keyword Search: Students can search approved campaigns dynamically by role name or corporate employer title without triggering page reloads.
* Criteria Sliders: A responsive matching engine limits displayed job positions instantly using a maximum target CGPA cutoff threshold.

3. Comprehensive Profile and Account Actions

* Security Control Engine: Users can seamlessly update or reset account credentials directly inside their secure console views via hashed password mutations.
* Role-Based Workspaces: Context-aware data parsing blocks students from seeing unverified job pipelines and ensures recruiters only process applicants matching specific parameters.

Setup Instructions

1. Backend Configuration
Navigate to your project root or backend directory to spin up the REST infrastructure server:

Command Line Instructions:
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python app.py

2. Frontend Access

Because the Flask application factory is configured with unified static folder routing directives, you do not need a secondary live-server instance for the frontend. Simply open your web browser and navigate directly to:
[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

3. Default Administrative Credentials

An initial system administrator entity is programmatically provisioned into the database upon initial app initialization:

* Admin Email: admin@institute.edu
* Admin Password: admin123

System File Hierarchy Structure

placement_portal2/
├── backend/
│   ├── app.py                  (Core Application Factory and Frontend Static Server)
│   ├── config.py               (Runtime Environment Variable Profiles)
│   ├── models.py               (SQLAlchemy Database Declarative Schemas)
│   └── routes/                 (Decoupled Blueprint API Endpoint Layer)
│       ├── admin_api.py        (Institutional Administrative Approvals)
│       ├── auth_api.py         (Registration and JWT Token Generators)
│       ├── company_api.py      (Corporate Placements and Selection Tracking)
│       └── student_api.py      (Profile Portfolios, Form Checks and Security)
├── frontend/
│   ├── index.html              (Vue Mounting Matrix Layout Container)
│   └── app.js                  (Client Components and Vue Router Single Page Logic)
├── .gitignore                  (Wipes local caches and databases out of version histories)
└── requirements.txt            (Explicit definitions of environment packages)

REST API Endpoint Inventory Blueprint

* POST: /api/auth/register
Authorization Role Required: Open Public
Scope: Validates and generates a new secure database credential state.
* POST: /api/auth/login
Authorization Role Required: Open Public
Scope: Generates short-lived cryptographic JWT keys if records match.
* GET: /api/admin/dashboard
Authorization Role Required: Admin Only
Scope: Evaluates aggregate statistics across the entire database registry.
* GET: /api/admin/companies/pending
Authorization Role Required: Admin Only
Scope: Collects active requests from unverified corporate partners.
* POST: /api/admin/drives/approve/id
Authorization Role Required: Admin Only
Scope: Shifts campaign validation variables to toggle visibility states.
* POST: /api/company/drives
Authorization Role Required: Company Only
Scope: Creates recruitment strategies bound to future deadline limits.
* GET: /api/company/applicants
Authorization Role Required: Company Only
Scope: Extracts academic profile metrics for evaluating open jobs.
* POST: /api/student/profile
Authorization Role Required: Student Only
Scope: Saves branch credentials and validates scaling data parameters.
* POST: /api/student/apply
Authorization Role Required: Student Only
Scope: Passes applications through eligibility and deadline checks.
* POST: /api/student/change-password
Authorization Role Required: Universally Bound
Scope: Mutates database credentials cleanly via token-subject matching.

import os
import uuid
import datetime
from flask import Flask, render_template, redirect, url_for, request, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'complaint-app-secret-key-12345')

# Read DATABASE_URL from Render, mapping postgres:// to postgresql://
db_url = os.environ.get('DATABASE_URL', 'sqlite:///complaints.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'student' or 'admin'
    full_name = db.Column(db.String(100), nullable=False)
    school_college = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    complaints = db.relationship('Complaint', backref='student', lazy=True)

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for anonymous
    category = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    supporting_doc = db.Column(db.String(255), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='Submitted')  # 'Submitted', 'Under Review', 'In Progress', 'Resolved'
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Decorators
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper for secure file uploading
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def home():
    # Calculate stats for homepage
    stats = {
        'total': Complaint.query.count(),
        'resolved': Complaint.query.filter_by(status='Resolved').count(),
        'in_progress': Complaint.query.filter(Complaint.status.in_(['Under Review', 'In Progress'])).count(),
        'anonymous': Complaint.query.filter_by(is_anonymous=True).count()
    }
    return render_template('home.html', stats=stats)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Thank you for reaching out. Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        mobile = request.form.get('mobile').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name').strip()
        school_college = request.form.get('school_college').strip()
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
            
        # Check if email or mobile already registered
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return render_template('register.html')
        if User.query.filter_by(mobile=mobile).first():
            flash('Mobile number already registered!', 'danger')
            return render_template('register.html')
            
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            mobile=mobile,
            password_hash=hashed_password,
            full_name=full_name,
            school_college=school_college,
            role='student'
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        identifier = request.form.get('identifier').strip().lower()  # email or mobile
        password = request.form.get('password')
        
        # Check both email and mobile
        user = User.query.filter((User.email == identifier) | (User.mobile == identifier)).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['full_name'] = user.full_name
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            # Simulated reset password logic
            flash('A password reset link has been sent to your email (simulation).', 'success')
        else:
            flash('Email address not found.', 'danger')
    return render_template('forgot_password.html')

@app.route('/submit-complaint', methods=['GET', 'POST'])
def submit_complaint():
    # If not logged in, we check if they want to submit anonymously
    is_logged_in = 'user_id' in session
    
    if request.method == 'POST':
        category = request.form.get('category')
        title = request.form.get('title').strip()
        description = request.form.get('description').strip()
        anonymous_form = request.form.get('anonymous') == 'true'
        
        # Anonymous is enforced if not logged in
        is_anonymous = True if not is_logged_in else anonymous_form
        
        # Unique ID generation e.g. CMP-83D2A5
        unique_id = f"CMP-{uuid.uuid4().hex[:6].upper()}"
        
        # Handle file upload
        filename = None
        file = request.files.get('file')
        if file and file.filename != '':
            if allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                # Secure filename with unique string to prevent collision
                filename = f"{unique_id}_{secure_filename(file.filename)}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                flash('Invalid file format. Allowed formats: PNG, JPG, JPEG, GIF, PDF, DOC, DOCX, TXT', 'danger')
                return render_template('submit_complaint.html')

        user_id = None if is_anonymous else session.get('user_id')
        
        new_complaint = Complaint(
            complaint_id=unique_id,
            user_id=user_id,
            category=category,
            title=title,
            description=description,
            supporting_doc=filename,
            is_anonymous=is_anonymous,
            status='Submitted'
        )
        db.session.add(new_complaint)
        db.session.commit()
        
        flash(f'Complaint submitted successfully! Your tracking ID is: {unique_id}', 'success')
        return redirect(url_for('track', complaint_id=unique_id))
        
    return render_template('submit_complaint.html')

@app.route('/track', methods=['GET', 'POST'])
def track():
    complaint = None
    complaint_id = request.args.get('complaint_id', '').strip()
    
    if request.method == 'POST':
        complaint_id = request.form.get('complaint_id', '').strip()
        
    if complaint_id:
        complaint = Complaint.query.filter_by(complaint_id=complaint_id).first()
        if not complaint:
            flash('No complaint found with that tracking ID.', 'danger')
            
    return render_template('track.html', complaint=complaint, query_id=complaint_id)

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    user = User.query.get(session['user_id'])
    # Get complaints belonging to user (not anonymous, or submitted while logged in as non-anonymous)
    complaints = Complaint.query.filter_by(user_id=user.id).order_by(Complaint.created_at.desc()).all()
    
    return render_template('dashboard_user.html', user=user, complaints=complaints)

@app.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    user = User.query.get(session['user_id'])
    user.full_name = request.form.get('full_name').strip()
    user.mobile = request.form.get('mobile').strip()
    user.school_college = request.form.get('school_college').strip()
    
    db.session.commit()
    session['full_name'] = user.full_name
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Fetch all complaints
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    
    # Calculate stats for chart
    categories_data = db.session.query(Complaint.category, db.func.count(Complaint.id)).group_by(Complaint.category).all()
    status_data = db.session.query(Complaint.status, db.func.count(Complaint.id)).group_by(Complaint.status).all()
    
    stats = {
        'total': len(complaints),
        'submitted': Complaint.query.filter_by(status='Submitted').count(),
        'under_review': Complaint.query.filter_by(status='Under Review').count(),
        'in_progress': Complaint.query.filter_by(status='In Progress').count(),
        'resolved': Complaint.query.filter_by(status='Resolved').count()
    }
    
    return render_template('dashboard_admin.html', complaints=complaints, stats=stats, 
                           categories_data=dict(categories_data), status_data=dict(status_data))

@app.route('/admin/update-complaint/<int:id>', methods=['POST'])
@admin_required
def admin_update_complaint(id):
    complaint = Complaint.query.get_or_450(id) if hasattr(Complaint, 'query') else None
    # Let's get by ID
    complaint = Complaint.query.get(id)
    if not complaint:
        flash('Complaint not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes').strip()
    
    if status in ['Submitted', 'Under Review', 'In Progress', 'Resolved']:
        complaint.status = status
    complaint.admin_notes = admin_notes
    db.session.commit()
    
    flash(f'Complaint {complaint.complaint_id} updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Command line interface to create database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed an admin account
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            hashed_password = generate_password_hash('Admin@123')
            admin = User(
                email='admin@report.org',
                mobile='1234567890',
                password_hash=hashed_password,
                role='admin',
                full_name='System Admin',
                school_college='System HQ'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin account created (admin@report.org / Admin@123)")
    app.run(debug=True, port=5000)

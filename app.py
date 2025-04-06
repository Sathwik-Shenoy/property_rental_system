from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/property_rental_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'landlord', or 'tenant'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    properties = db.relationship('Property', backref='landlord', lazy=True)
    tenant_profile = db.relationship('Tenant', backref='user', uselist=False, lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Property(db.Model):
    property_id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    square_feet = db.Column(db.Float)
    monthly_rent = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leases = db.relationship('Lease', backref='property', lazy=True)

class Tenant(db.Model):
    tenant_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    employment_status = db.Column(db.String(50))
    annual_income = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leases = db.relationship('Lease', backref='tenant', lazy=True)

class Lease(db.Model):
    lease_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.tenant_id'))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    monthly_rent = db.Column(db.Float, nullable=False)
    security_deposit = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='lease', lazy=True)

class Payment(db.Model):
    payment_id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.lease_id'))
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(50), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        # Validate required fields
        if not all([username, email, password, role]):
            flash('All fields are required', 'error')
            return redirect(url_for('register'))

        # Validate tenant-specific fields
        if role == 'tenant' and not all([first_name, last_name]):
            flash('First name and last name are required for tenants', 'error')
            return redirect(url_for('register'))

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))

        try:
            # Create user
            user = User(
                username=username,
                email=email,
                role=role
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get the user ID without committing
            
            # If registering as a tenant, create tenant profile
            if role == 'tenant':
                tenant = Tenant(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
                db.session.add(tenant)

            # Create welcome notification
            notification = Notification(
                user_id=user.id,
                message=f'Welcome to Property Rental System! Your account has been created successfully.',
                type='success'
            )
            db.session.add(notification)
            
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        properties = Property.query.all()
        tenants = Tenant.query.all()
        leases = Lease.query.all()
    elif current_user.role == 'landlord':
        properties = Property.query.filter_by(landlord_id=current_user.id).all()
        # Get all tenants who have leases for this landlord's properties
        property_ids = [p.property_id for p in properties]
        tenant_ids = db.session.query(Lease.tenant_id).filter(Lease.property_id.in_(property_ids)).distinct().all()
        tenant_ids = [t[0] for t in tenant_ids]
        tenants = Tenant.query.filter(Tenant.tenant_id.in_(tenant_ids)).all()
        leases = Lease.query.filter(Lease.property_id.in_(property_ids)).all()
    else:  # tenant
        tenant = current_user.tenant_profile
        if tenant:
            leases = Lease.query.filter_by(tenant_id=tenant.tenant_id).all()
            properties = Property.query.join(Lease).filter(Lease.tenant_id == tenant.tenant_id).all()
            tenants = [tenant]
        else:
            leases = []
            properties = []
            tenants = []
    
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    return render_template('dashboard.html', 
                         properties=properties, 
                         tenants=tenants, 
                         leases=leases,
                         notifications=notifications)

@app.route('/properties')
@login_required
def properties():
    if current_user.role == 'admin':
        properties = Property.query.all()
    elif current_user.role == 'landlord':
        properties = Property.query.filter_by(landlord_id=current_user.id).all()
    else:  # tenant
        tenant = current_user.tenant_profile
        if tenant:
            properties = Property.query.join(Lease).filter(Lease.tenant_id == tenant.tenant_id).all()
        else:
            properties = []
    return render_template('properties.html', properties=properties)

@app.route('/tenants')
@login_required
def tenants():
    if current_user.role == 'admin':
        # Admin can see all tenants
        tenants = Tenant.query.all()
    elif current_user.role == 'landlord':
        # Get properties owned by this landlord
        properties = Property.query.filter_by(landlord_id=current_user.id).all()
        property_ids = [p.property_id for p in properties]
        
        # Get leases for these properties
        leases = Lease.query.filter(Lease.property_id.in_(property_ids)).all()
        tenant_ids = [lease.tenant_id for lease in leases]
        
        # Get tenants who have leases with this landlord's properties
        tenants = Tenant.query.filter(Tenant.tenant_id.in_(tenant_ids)).all()
        
        # Get all available tenants (those without active leases)
        leased_tenants = Lease.query.with_entities(Lease.tenant_id).filter(Lease.status == 'Active').all()
        leased_tenant_ids = [t[0] for t in leased_tenants]
        available_tenants = Tenant.query.filter(~Tenant.tenant_id.in_(leased_tenant_ids)).all()
        
        # Combine both lists while removing duplicates
        tenant_set = set(tenants)
        tenant_set.update(available_tenants)
        tenants = list(tenant_set)
    else:
        # Tenants can only see their own profile
        tenants = [current_user.tenant_profile] if current_user.tenant_profile else []
    
    return render_template('tenants.html', tenants=tenants)

@app.route('/leases')
@login_required
def leases():
    if current_user.role == 'admin':
        leases = Lease.query.all()
        properties = Property.query.filter_by(status='Available').all()
        # Get all tenants who don't have an active lease
        tenants = Tenant.query.outerjoin(Lease, (Tenant.tenant_id == Lease.tenant_id) & (Lease.status == 'Active'))\
            .filter(Lease.lease_id == None).all()
    elif current_user.role == 'landlord':
        # Get landlord's properties
        properties = Property.query.filter_by(landlord_id=current_user.id, status='Available').all()
        # Get leases for landlord's properties
        property_ids = [p.property_id for p in properties]
        leases = Lease.query.filter(Lease.property_id.in_(property_ids)).all()
        # Get all tenants who don't have an active lease
        tenants = Tenant.query.outerjoin(Lease, (Tenant.tenant_id == Lease.tenant_id) & (Lease.status == 'Active'))\
            .filter(Lease.lease_id == None).all()
    else:  # tenant
        tenant = current_user.tenant_profile
        if tenant:
            leases = Lease.query.filter_by(tenant_id=tenant.tenant_id).all()
            properties = []
            tenants = []
        else:
            leases = []
            properties = []
            tenants = []
    
    return render_template('leases.html', 
        leases=leases, 
        properties=properties, 
        tenants=tenants,
        today=date.today().strftime('%Y-%m-%d')
    )

@app.route('/payments')
@login_required
def payments():
    if current_user.role == 'admin':
        payments = Payment.query.all()
    elif current_user.role == 'landlord':
        # Get all properties owned by the landlord
        properties = Property.query.filter_by(landlord_id=current_user.id).all()
        property_ids = [p.property_id for p in properties]
        # Get all leases for these properties
        lease_ids = [lease.lease_id for lease in Lease.query.filter(Lease.property_id.in_(property_ids)).all()]
        # Get all payments for these leases
        payments = Payment.query.filter(Payment.lease_id.in_(lease_ids)).all() if lease_ids else []
    else:  # tenant
        tenant = current_user.tenant_profile
        if tenant:
            lease_ids = [lease.lease_id for lease in Lease.query.filter_by(tenant_id=tenant.tenant_id).all()]
            payments = Payment.query.filter(Payment.lease_id.in_(lease_ids)).all() if lease_ids else []
        else:
            payments = []
    return render_template('payments.html', payments=payments)

@app.route('/property/add', methods=['POST'])
@login_required
def add_property():
    if current_user.role not in ['admin', 'landlord']:
        flash('Permission denied')
        return redirect(url_for('properties'))
    
    address = request.form.get('address')
    property_type = request.form.get('property_type')
    bedrooms = request.form.get('bedrooms')
    bathrooms = request.form.get('bathrooms')
    square_feet = request.form.get('square_feet')
    monthly_rent = request.form.get('monthly_rent')
    
    property = Property(
        landlord_id=current_user.id,
        address=address,
        property_type=property_type,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        square_feet=square_feet,
        monthly_rent=monthly_rent
    )
    
    db.session.add(property)
    db.session.commit()
    
    flash('Property added successfully')
    return redirect(url_for('properties'))

@app.route('/lease/add', methods=['POST'])
@login_required
def add_lease():
    if current_user.role not in ['admin', 'landlord']:
        flash('Permission denied', 'error')
        return redirect(url_for('leases'))
    
    try:
        # Get form data
        property_id = request.form.get('property_id')
        tenant_id = request.form.get('tenant_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        monthly_rent = request.form.get('monthly_rent')
        security_deposit = request.form.get('security_deposit')

        # Validate required fields
        if not all([property_id, tenant_id, start_date, end_date, monthly_rent, security_deposit]):
            flash('All fields are required', 'error')
            return redirect(url_for('leases'))

        # Convert dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Validate date range
            if start_date >= end_date:
                flash('End date must be after start date', 'error')
                return redirect(url_for('leases'))
            
            if start_date < datetime.now().date():
                flash('Start date cannot be in the past', 'error')
                return redirect(url_for('leases'))
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('leases'))

        # Validate property exists and belongs to landlord
        property = Property.query.get(property_id)
        if not property:
            flash('Invalid property selected', 'error')
            return redirect(url_for('leases'))
        
        if current_user.role == 'landlord' and property.landlord_id != current_user.id:
            flash('You can only create leases for your own properties', 'error')
            return redirect(url_for('leases'))
        
        if property.status != 'Available':
            flash('This property is not available for lease', 'error')
            return redirect(url_for('leases'))

        # Validate tenant exists
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            flash('Invalid tenant selected', 'error')
            return redirect(url_for('leases'))

        # Check if tenant already has an active lease
        existing_lease = Lease.query.filter_by(
            tenant_id=tenant_id,
            status='Active'
        ).first()
        if existing_lease:
            flash('This tenant already has an active lease', 'error')
            return redirect(url_for('leases'))

        # Create lease
        lease = Lease(
            property_id=property_id,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            monthly_rent=float(monthly_rent),
            security_deposit=float(security_deposit),
            status='Active'
        )
        
        # Update property status
        property.status = 'Rented'
        
        db.session.add(lease)
        
        # Create notifications
        tenant_notification = Notification(
            user_id=tenant.user_id,
            message=f'New lease created for property at {property.address}. Monthly rent: ${monthly_rent}, Security deposit: ${security_deposit}',
            type='info'
        )
        
        landlord_notification = Notification(
            user_id=property.landlord_id,
            message=f'New lease created for your property at {property.address} with tenant {tenant.first_name} {tenant.last_name}',
            type='success'
        )
        
        db.session.add(tenant_notification)
        db.session.add(landlord_notification)
        
        db.session.commit()
        flash('Lease created successfully', 'success')
        
    except ValueError as e:
        flash(f'Invalid data format: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating lease: {str(e)}', 'error')
    
    return redirect(url_for('leases'))

@app.route('/tenant/add', methods=['POST'])
@login_required
def add_tenant():
    if current_user.role not in ['admin', 'landlord']:
        flash('Permission denied', 'error')
        return redirect(url_for('tenants'))
    
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone = request.form.get('phone')
    date_of_birth = request.form.get('date_of_birth')
    employment_status = request.form.get('employment_status')
    annual_income = request.form.get('annual_income')
    
    if not all([email, first_name, last_name]):
        flash('Email, first name, and last name are required', 'error')
        return redirect(url_for('tenants'))
    
    # Check if tenant with this email already exists
    if Tenant.query.filter_by(email=email).first():
        flash('A tenant with this email already exists', 'error')
        return redirect(url_for('tenants'))
    
    try:
        # Create user account for tenant
        username = email.split('@')[0]  # Use email prefix as username
        password = 'tenant123'  # Default password
        
        user = User(
            username=username,
            email=email,
            role='tenant'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Create tenant profile
        tenant = Tenant(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None,
            employment_status=employment_status,
            annual_income=float(annual_income) if annual_income else None
        )
        db.session.add(tenant)
        
        # Create welcome notification
        notification = Notification(
            user_id=user.id,
            message=f'Welcome to Property Rental System! Your account has been created with username: {username} and password: {password}',
            type='success'
        )
        db.session.add(notification)
        
        db.session.commit()
        flash(f'Tenant added successfully. Account created with username: {username} and password: {password}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding tenant: {str(e)}', 'error')
    
    return redirect(url_for('tenants'))

@app.route('/lease/<int:lease_id>/payments')
@login_required
def get_lease_payments(lease_id):
    lease = Lease.query.get_or_404(lease_id)
    
    # Verify user has permission to view these payments
    if current_user.role == 'tenant':
        if lease.tenant.user_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
    elif current_user.role == 'landlord':
        if lease.property.landlord_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
    
    payments = Payment.query.filter_by(lease_id=lease_id).all()
    payments_data = [{
        'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
        'amount': "%.2f" % payment.amount,
        'payment_type': payment.payment_type,
        'payment_status': payment.payment_status
    } for payment in payments]
    
    return jsonify({'payments': payments_data})

@app.route('/payment/add', methods=['POST'])
@login_required
def add_payment():
    try:
        lease_id = request.form.get('lease_id')
        amount = request.form.get('amount')
        payment_type = request.form.get('payment_type')
        payment_date = request.form.get('payment_date')
        
        if not all([lease_id, amount, payment_type, payment_date]):
            flash('All fields are required', 'error')
            return redirect(url_for('leases'))
        
        # Convert payment date
        payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        
        # Verify lease exists and user has permission
        lease = Lease.query.get_or_404(lease_id)
        if current_user.role == 'tenant' and lease.tenant.user_id != current_user.id:
            flash('Permission denied', 'error')
            return redirect(url_for('leases'))
        
        # Create payment
        payment = Payment(
            lease_id=lease_id,
            amount=float(amount),
            payment_type=payment_type,
            payment_date=payment_date,
            payment_status='Pending'
        )
        db.session.add(payment)
        
        # Create notifications
        tenant_notification = Notification(
            user_id=lease.tenant.user_id,
            message=f'Payment of ${amount} submitted for {payment_type}. Status: Pending',
            type='info'
        )
        
        landlord_notification = Notification(
            user_id=lease.property.landlord_id,
            message=f'New payment of ${amount} received from {lease.tenant.first_name} {lease.tenant.last_name} for property at {lease.property.address}',
            type='info'
        )
        
        db.session.add(tenant_notification)
        db.session.add(landlord_notification)
        
        db.session.commit()
        flash('Payment submitted successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting payment: {str(e)}', 'error')
    
    return redirect(url_for('leases'))

@app.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    notification_ids = request.json.get('notification_ids', [])
    if notification_ids:
        Notification.query.filter(
            Notification.notification_id.in_(notification_ids),
            Notification.user_id == current_user.id
        ).update({Notification.is_read: True}, synchronize_session=False)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/payment/<int:payment_id>/status', methods=['POST'])
@login_required
def update_payment_status(payment_id):
    if current_user.role not in ['admin', 'landlord']:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['Completed', 'Failed', 'Pending']:
        return jsonify({'error': 'Invalid status'}), 400
        
    payment = Payment.query.get_or_404(payment_id)
    
    # Verify the payment belongs to one of the landlord's properties
    if current_user.role == 'landlord':
        lease = Lease.query.get(payment.lease_id)
        property = Property.query.get(lease.property_id)
        if property.landlord_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
    
    payment.payment_status = new_status
    db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001) 
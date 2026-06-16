from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import stripe
import os
from dotenv import load_dotenv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///freelancer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Stripe 配置
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_your_key')

# ==================== 数据库模型 ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_status = db.Column(db.String(20), default='free')  # free, pro
    subscription_end = db.Column(db.DateTime)
    
    projects = db.relationship('Project', backref='user', lazy=True, cascade='all, delete-orphan')
    clients = db.relationship('Client', backref='user', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='user', lazy=True, cascade='all, delete-orphan')
    time_logs = db.relationship('TimeLog', backref='user', lazy=True, cascade='all, delete-orphan')

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    company = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    projects = db.relationship('Project', backref='client', lazy=True)
    invoices = db.relationship('Invoice', backref='client', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, completed, on-hold
    rate = db.Column(db.Float)  # 时薪
    budget = db.Column(db.Float)  # 总预算
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    time_logs = db.relationship('TimeLog', backref='project', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='project', lazy=True)

class TimeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    logged_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, sent, paid
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_date = db.Column(db.DateTime)
    
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== 认证路由 ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            company_name=company_name
        )
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ==================== 主页面 ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # 统计数据
    total_projects = Project.query.filter_by(user_id=current_user.id).count()
    active_projects = Project.query.filter_by(user_id=current_user.id, status='active').count()
    
    # 总时间（小时）
    time_logs = TimeLog.query.filter_by(user_id=current_user.id).all()
    total_hours = sum(log.hours for log in time_logs)
    
    # 总收入
    invoices = Invoice.query.filter_by(user_id=current_user.id, status='paid').all()
    total_income = sum(inv.amount for inv in invoices)
    
    # 最近项目
    recent_projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).limit(5).all()
    
    # 本月收入
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_income = sum(inv.amount for inv in invoices if inv.paid_date and inv.paid_date >= current_month_start)
    
    return render_template('dashboard.html',
                         total_projects=total_projects,
                         active_projects=active_projects,
                         total_hours=total_hours,
                         total_income=total_income,
                         monthly_income=monthly_income,
                         recent_projects=recent_projects)

# ==================== 项目管理 ====================

@app.route('/projects')
@login_required
def projects():
    page = request.args.get('page', 1, type=int)
    projects_list = Project.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=10)
    return render_template('projects.html', projects=projects_list.items, pagination=projects_list)

@app.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        project = Project(
            user_id=current_user.id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            rate=float(request.form.get('rate', 0)),
            budget=float(request.form.get('budget', 0)),
            deadline=datetime.fromisoformat(request.form.get('deadline')) if request.form.get('deadline') else None
        )
        db.session.add(project)
        db.session.commit()
        flash('项目创建成功！', 'success')
        return redirect(url_for('projects'))
    
    return render_template('create_project.html')

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        project.rate = float(request.form.get('rate', 0))
        project.budget = float(request.form.get('budget', 0))
        project.status = request.form.get('status')
        db.session.commit()
        flash('项目更新成功！', 'success')
        return redirect(url_for('projects'))
    
    return render_template('edit_project.html', project=project)

@app.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return redirect(url_for('projects'))
    
    db.session.delete(project)
    db.session.commit()
    flash('项目已删除', 'success')
    return redirect(url_for('projects'))

# ==================== 时间追踪 ====================

@app.route('/time-logs')
@login_required
def time_logs():
    page = request.args.get('page', 1, type=int)
    logs = TimeLog.query.filter_by(user_id=current_user.id).order_by(TimeLog.logged_date.desc()).paginate(page=page, per_page=20)
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('time_logs.html', logs=logs.items, projects=projects, pagination=logs)

@app.route('/time-logs/add', methods=['GET', 'POST'])
@login_required
def add_time_log():
    if request.method == 'POST':
        time_log = TimeLog(
            user_id=current_user.id,
            project_id=request.form.get('project_id'),
            hours=float(request.form.get('hours')),
            description=request.form.get('description'),
            logged_date=datetime.fromisoformat(request.form.get('logged_date')) if request.form.get('logged_date') else datetime.utcnow()
        )
        db.session.add(time_log)
        db.session.commit()
        flash('时间记录已添加！', 'success')
        return redirect(url_for('time_logs'))
    
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    return render_template('add_time_log.html', projects=projects)

# ==================== 发票管理 ====================

@app.route('/invoices')
@login_required
def invoices():
    page = request.args.get('page', 1, type=int)
    invoices_list = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('invoices.html', invoices=invoices_list.items, pagination=invoices_list)

@app.route('/invoices/create', methods=['GET', 'POST'])
@login_required
def create_invoice():
    if request.method == 'POST':
        # 生成发票号
        invoice_count = Invoice.query.filter_by(user_id=current_user.id).count()
        invoice_number = f"INV-{current_user.id}-{invoice_count + 1:04d}"
        
        invoice = Invoice(
            user_id=current_user.id,
            client_id=request.form.get('client_id'),
            project_id=request.form.get('project_id'),
            invoice_number=invoice_number,
            amount=float(request.form.get('amount')),
            due_date=datetime.fromisoformat(request.form.get('due_date')) if request.form.get('due_date') else None
        )
        db.session.add(invoice)
        db.session.commit()
        
        # 添加发票项目
        items = request.form.getlist('item_description')
        quantities = request.form.getlist('item_quantity')
        prices = request.form.getlist('item_price')
        
        for desc, qty, price in zip(items, quantities, prices):
            if desc:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=desc,
                    quantity=float(qty),
                    unit_price=float(price)
                )
                db.session.add(item)
        
        db.session.commit()
        flash('发票创建成功！', 'success')
        return redirect(url_for('invoices'))
    
    clients = Client.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('create_invoice.html', clients=clients, projects=projects)

@app.route('/invoices/<int:invoice_id>/download')
@login_required
def download_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    if invoice.user_id != current_user.id:
        return redirect(url_for('invoices'))
    
    # 生成 PDF
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # 标题
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1f2937'))
    elements.append(Paragraph(f"发票 {invoice.invoice_number}", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # 发票信息
    info_data = [
        ['发票日期:', datetime.utcnow().strftime('%Y-%m-%d')],
        ['应付期限:', invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'N/A'],
        ['状态:', invoice.status]
    ]
    info_table = Table(info_data, colWidths=[2*inch, 2*inch])
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # 项目表
    items_data = [['描述', '数量', '单价', '合计']]
    for item in invoice.items:
        items_data.append([
            item.description,
            str(item.quantity),
            f"${item.unit_price:.2f}",
            f"${item.quantity * item.unit_price:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # 总额
    total_style = ParagraphStyle('Total', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#1f2937'), alignment=2)
    elements.append(Paragraph(f"<b>总计: ${invoice.amount:.2f}</b>", total_style))
    
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return pdf_buffer.getvalue(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'attachment; filename="{invoice.invoice_number}.pdf"'
    }

# ==================== 客户管理 ====================

@app.route('/clients')
@login_required
def clients():
    page = request.args.get('page', 1, type=int)
    clients_list = Client.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=20)
    return render_template('clients.html', clients=clients_list.items, pagination=clients_list)

@app.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        client = Client(
            user_id=current_user.id,
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            company=request.form.get('company')
        )
        db.session.add(client)
        db.session.commit()
        flash('客户已添加！', 'success')
        return redirect(url_for('clients'))
    
    return render_template('add_client.html')

# ==================== 支付/订阅 ====================

@app.route('/upgrade')
@login_required
def upgrade():
    return render_template('upgrade.html')

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'FreelanceFlow Pro - Monthly'},
                        'unit_amount': 1999,  # $19.99
                        'recurring': {'interval': 'month', 'interval_count': 1}
                    },
                    'quantity': 1
                }
            ],
            mode='subscription',
            success_url=url_for('checkout_success', _external=True),
            cancel_url=url_for('upgrade', _external=True),
            customer_email=current_user.email,
            client_reference_id=str(current_user.id)
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return jsonify(error=str(e)), 400

@app.route('/checkout-success')
@login_required
def checkout_success():
    current_user.subscription_status = 'pro'
    current_user.subscription_end = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    flash('升级成功！欢迎使用 Pro 版本', 'success')
    return redirect(url_for('dashboard'))

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ==================== 初始化数据库 ====================

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask import Flask
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, DebtType, PaymentTask, ExpenseCategory, Expense, IncomeExpense
from datetime import datetime
import io
import matplotlib.pyplot as plt
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import CSRFProtect
import os
from forms import RegistrationForm

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(32)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

csrf = CSRFProtect()
csrf.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Flask-Migrateの初期化

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/',methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = request.form.get('username')  # フォームからのデータ取得
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        print(username,password,confirm_password)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('そのユーザー名は既に使用されています。')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('パスワードが一致しません。')
            return redirect(url_for('register'))
            
        if not username or not password:
            flash('全てのフィールドを入力してください')
            return redirect(url_for('register'))
            
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('登録が成功しました！ログインしてください。')
        return redirect(url_for('dashboard'))
        
    else:
        if request.method == 'POST':
            flash('フォームの送信に失敗しました。もう一度お試しください。')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()  # ここにクエリを記述
        
        if user is None or not user.check_password(password):
            flash('ユーザー名かパスワードが間違っています。')
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    debt_types = DebtType.query.filter_by(user_id=current_user.id).all()
    tasks = PaymentTask.query.filter_by(user_id=current_user.id).all()
    income_expense = IncomeExpense.query.filter_by(user_id=current_user.id).first()
    fixed_categories = ExpenseCategory.query.filter_by(parent_category='固定費', user_id=current_user.id).all()
    variable_categories = ExpenseCategory.query.filter_by(parent_category='変動費', user_id=current_user.id).all()

    return render_template('dashboard.html', debt_types=debt_types, tasks=tasks, income_expense=income_expense)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = request.form['amount']
        description = request.form['description']
        category_id = request.form['category_id']

        new_expense = Expense(user_id=current_user.id, amount=amount, category_id=category_id, description=description)
        db.session.add(new_expense)
        db.session.commit()

        flash('支出が登録されました。')
        return redirect(url_for('dashboard'))

    fixed_categories = ExpenseCategory.query.filter_by(parent_category='固定費', user_id=current_user.id).all()
    variable_categories = ExpenseCategory.query.filter_by(parent_category='変動費', user_id=current_user.id).all()

    return render_template('add_expense.html', fixed_categories=fixed_categories, variable_categories=variable_categories)

@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        category_name = request.form['category_name']
        parent_category = request.form['parent_category']

        new_category = ExpenseCategory(name=category_name, parent_category=parent_category, user_id=current_user.id)
        db.session.add(new_category)
        db.session.commit()

        flash('カテゴリが追加されました。')
        return redirect(url_for('dashboard'))

    return render_template('add_category.html')

@app.route('/expense_category_chart')
@login_required
def expense_category_chart():
    expenses = db.session.query(
        ExpenseCategory.name, db.func.sum(Expense.amount)
    ).join(Expense).filter(Expense.user_id == current_user.id).group_by(ExpenseCategory.name).all()

    labels = [expense[0] for expense in expenses]
    values = [expense[1] for expense in expenses]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return Response(img.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port,debug=True)

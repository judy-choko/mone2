import sqlite3
from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import os
from forms import RegistrationForm
import io
import matplotlib.pyplot as plt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField  # 必要なフィールドをインポート
from wtforms.validators import DataRequired

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "defaultsecret")
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# データベース初期化関数
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expense_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_category TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (category_id) REFERENCES expense_category(id)
        )
    ''')
    conn.commit()
    conn.close()
    
# SQLiteデータベース接続関数
def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row  # クエリ結果を辞書形式で取得
    return conn

# ログインフォームの定義
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

# カテゴリ追加用フォーム
class AddCategoryForm(FlaskForm):
    category_name = StringField('カテゴリ名', validators=[DataRequired()])
    parent_category = SelectField('大カテゴリ', choices=[('固定費', '固定費'), ('変動費', '変動費')], validators=[DataRequired()])
    submit = SubmitField('カテゴリを追加')

# 支出追加用フォーム
class AddExpenseForm(FlaskForm):
    amount = IntegerField('支出額', validators=[DataRequired()])
    description = StringField('説明', validators=[DataRequired()])
    category_id = SelectField('カテゴリ', coerce=int)
    submit = SubmitField('支出を追加')
    
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['password_hash'])
    return None

class User:
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        if password != confirm_password:
            flash('パスワードが一致しません。')
            return redirect(url_for('register'))

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('そのユーザー名は既に使用されています。')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO user (username, password_hash) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()

        flash('登録が成功しました！ログインしてください。')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # SQLiteでユーザー情報を取得
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'], user['password_hash'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        #if user and check_password_hash(user.password_hash, form.password.data):
        #    login_user(user)
        else:
            flash('ユーザー名かパスワードが正しくありません')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expense WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()

    return render_template('dashboard.html', expenses=expenses)

@app.route('/expense_category_chart')
@login_required
def expense_category_chart():
    conn = get_db_connection()
    expenses = conn.execute('SELECT category_id, SUM(amount) as total_amount FROM expense WHERE user_id = ? GROUP BY category_id', 
                            (current_user.id,)).fetchall()
    conn.close()

    labels = [expense['category_id'] for expense in expenses]
    values = [expense['total_amount'] for expense in expenses]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return Response(img.getvalue(), mimetype='image/png')

# カテゴリ追加ルート
@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    form = AddCategoryForm()
    if form.validate_on_submit():
        category_name = form.category_name.data
        parent_category = form.parent_category.data

        # カテゴリをデータベースに追加
        conn = get_db_connection()
        conn.execute('INSERT INTO expense_category (name, parent_category, user_id) VALUES (?, ?, ?)', 
                     (category_name, parent_category, current_user.id))
        conn.commit()
        conn.close()

        flash('カテゴリが追加されました。')
        return redirect(url_for('dashboard'))

    return render_template('add_category.html', form=form)

# 支出追加ルート
@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = AddExpenseForm()

    # カテゴリのリストをデータベースから取得
    conn = get_db_connection()
    fixed_categories = conn.execute('SELECT * FROM expense_category WHERE parent_category = ? AND user_id = ?', ('固定費', current_user.id)).fetchall()
    variable_categories = conn.execute('SELECT * FROM expense_category WHERE parent_category = ? AND user_id = ?', ('変動費', current_user.id)).fetchall()

    # カテゴリ選択フィールドにデータを追加
    form.category_id.choices = [(category['id'], category['name']) for category in fixed_categories + variable_categories]

    if form.validate_on_submit():
        # フォームからデータを取得
        amount = form.amount.data
        description = form.description.data
        category_id = form.category_id.data

        # データベースに支出を追加
        conn.execute('INSERT INTO expense (user_id, amount, category_id, description) VALUES (?, ?, ?, ?)', 
                     (current_user.id, amount, category_id, description))
        conn.commit()
        conn.close()

        flash('支出が追加されました。')
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html', form=form, fixed_categories=fixed_categories, variable_categories=variable_categories)


if __name__ == '__main__':
    with app.app_context():
        init_db()  # アプリ起動時にデータベースを初期化
    app.run(host="0.0.0.0", port=8080, debug=True)

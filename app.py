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
from wtforms import StringField, IntegerField, SelectField,FileField, SubmitField, PasswordField, DateField 
from wtforms.validators import DataRequired
from dotenv import load_dotenv
from datetime import datetime
import matplotlib.font_manager as fm
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
import calendar
from  matplotlib import rcParams
from flask_cors import CORS
import mysql.connector
import MySQLdb
import psycopg2
import psycopg2.extras 
from flask import Flask, render_template_string
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract 
import json

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
PASSWORD = os.getenv('PASSWORD')
LOCALHOST = os.getenv('LOCALHOST')
USERNAME = os.getenv('USERNAME')
DBNAME = os.getenv('DBNAME')
DATABASE_URL = os.getenv('DATABASE_URL')
DBURL = os.getenv('DBURL')
# プッシュ
# アップロードフォルダの設定
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = SECRET_KEY
csrf = CSRFProtect(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Japanese font
font_path = '/usr/share/fonts/NotoSansCJKjp-DemiLight.otf'
fm.fontManager.ttflist
jp_font = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = jp_font.get_name()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_fonts():
    font_paths = []
    for font in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
        font_paths.append(font)
    return font_paths

# アップロードされたファイルが許可された形式かどうか確認
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import re

# 画像からテキストを抽出する関数
def extract_text_from_image(image_path):
    try:
        # 画像からテキストをOCRで抽出
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='jpn')  # 日本語のOCR
        # 改行や連続する空白を1つの空白に変換
        texts = re.sub(r'\s+', ' ', text.strip())

        # 明細と金額を区切るための正規表現
        # 明細部分は空白、金額部分は最後に「円」または数字で終わる
        pattern = r'(.*?)\s+(\d+,\d+|\d+円|\d+)'
        matches = re.findall(pattern, texts)

        # 各明細と金額を抽出
        items = []
        for match in matches:
            item_name = match[0].strip()  # 明細部分
            amount = match[1].replace(',', '').replace('円', '')  # 金額部分
            items.append({'item': item_name, 'amount': int(amount)})
            return items

    except Exception as e:
        print(f"画像処理エラー: {e}")
        return "テキスト抽出に失敗しました"
    
def get_user_categories(user_id):
    conn = create_server_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT expense_category ,id 
        FROM expense_category
        ANDuser_id = %s 
    ''', (user_id,))
    categories = cur.fetchall()
    conn.close()
    return categories

file_path='category_keywords.json'

def load_category_keywords():
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def categorize_item(item_name, user_id):
    # ユーザーのカテゴリリストを取得
    user_categories = get_user_categories(user_id)
    
    # カテゴリ名とIDをキーとした辞書を作成
    user_category_dict = {category['expense_category']: category['id'] for category in user_categories}
    category_keywords = load_category_keywords()
    # キーワードに基づくカテゴリを判定
    for category_name, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in item_name:
                # キーワードが一致したカテゴリがユーザーのカテゴリに存在するか確認
                if category_name in user_category_dict:
                    return user_category_dict[id]  # 一致するカテゴリIDを返す
                else:
                    return 1  # 一致するカテゴリがなければ「その他」を返す

    # キーワードに一致しない場合も「その他」に分類
    return 1
    
def create_server_connection():
    # conn = psycopg2.connect(DATABASE_URL)
    # conn = psycopg2.connect(dbname=DBNAME,host=LOCALHOST,port=5432,user=USERNAME,password=PASSWORD,sslmode="require")
    # conn = psycopg2.connect(dbname=DBNAME, user=USERNAME, password=PASSWORD)
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    # conn = psycopg2.connect(f'host={LOCALHOST} port=5432 dbname={DBNAME}  user={USERNAME} password={PASSWORD}')
    # connection = MySQLdb.connect(
    #     user=USERNAME, passwd=PASSWORD, host=LOCALHOST, db=DBNAME, charset="utf8"
    # )
    print("MySQL Database connection successful")
    return conn
# Datetime adapter for SQLite
def adapt_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def convert_datetime(s):
    try:
        return datetime.strptime(s.decode(), '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return datetime.strptime(s.decode(), '%Y-%m-%d')

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

# データベース初期化関数
def init_db():
    print("データベースを構築します")
    conn = create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS app_user (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expense_category (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            parent_category TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES app_user(id)
        )
    ''')
    conn.commit()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS debt_type (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        debt_name TEXT NOT NULL,
        total_debt INTEGER NOT NULL,
        monthly_payment INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES app_user(id)
        )
    ''')
    conn.commit()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expense (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES app_user(id),
            FOREIGN KEY (category_id) REFERENCES expense_category(id)
        )
    ''')
    conn.commit()
    cur.execute('''
CREATE TABLE IF NOT EXISTS payment_task (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    debt_type_id INTEGER NOT NULL,
    debt_name TEXT NOT NULL,
    monthly_payment INTEGER NOT NULL,                
    due_date TIMESTAMP NOT NULL,  -- TIMESTAMP to store both date and time
    is_completed BOOLEAN NOT NULL DEFAULT False,  -- ここを整数からbooleanに変更
    FOREIGN KEY(user_id) REFERENCES app_user(id),
    FOREIGN KEY(debt_type_id) REFERENCES debt_type(id)
    );
    ''')
    conn.commit()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS income_expense (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        income INTEGER DEFAULT 0,
        expense INTEGER DEFAULT 0,
        remaining_balance INTEGER DEFAULT 0,
        reset_day INTEGER DEFAULT 1 NOT NULL,  -- NULL不可でデフォルトを1日に
        FOREIGN KEY(user_id) REFERENCES app_user(id)
        )
    ''')
    conn.commit()
    
    # デフォルトカテゴリが存在しない場合のみ挿入
    cur.execute('SELECT COUNT(*) FROM expense_category')
    count = cur.fetchone()[0]
    conn.commit()
    
    if count == 0:
        # デフォルトの支出カテゴリを挿入
        default_categories = [
            ('家賃', '固定費'),
            ('光熱費', '固定費'),
            ('食費', '変動費'),
            ('交通費', '変動費')
        ]
        for name, parent_category in default_categories:
            cur.execute('INSERT INTO expense_category (name, parent_category, user_id) VALUES (%s, %s, 0)', (name, parent_category))
            conn.commit()
    
    conn.close()
    
# SQLiteデータベース接続関数
def get_db_connection():
    conn = sqlite3.connect('app.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row  # クエリ結果を辞書形式で取得
    return conn


# ログインフォームの定義
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

class addreciptForm(FlaskForm):
    image = FileField('画像を選択', validators=[DataRequired()])
    submit = SubmitField('アップロード')
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

class TaskForm(FlaskForm):
    debt_type_id = SelectField('借金の種類', coerce=int, validators=[DataRequired()])
    debt_name = StringField('借金の名前', validators=[DataRequired()])
    monthly_payment = IntegerField('毎月の返済額', validators=[DataRequired()])
    due_date = DateField('期日', validators=[DataRequired()])
    submit = SubmitField('タスクを追加')

class IncomeForm(FlaskForm):
    income = IntegerField('収入額', validators=[DataRequired()])
    submit = SubmitField('追加')

class ResetDayForm(FlaskForm):
    reset_day = IntegerField('収入リセット日', validators=[DataRequired()])
    submit = SubmitField('リセット日を設定')

class DebtTypeForm(FlaskForm):
    debt_name = StringField('借金の名前', validators=[DataRequired()])
    total_debt = IntegerField('借金総額', validators=[DataRequired()])
    monthly_payment = IntegerField('月々の返済額', validators=[DataRequired()])
    submit = SubmitField('追加')

class app_user:
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


# 固定費カテゴリ合計計算
def calculate_fixed_expenses(cur, user_id):
    cur.execute('''
        SELECT SUM(expense.amount) AS total_fixed_expenses
        FROM expense
        JOIN expense_category ON expense.category_id = expense_category.id
        WHERE expense_category.parent_category = '固定費'
        AND expense.user_id = %s 
    ''', (user_id,))
    fixed_expenses = cur.fetchone()
    return fixed_expenses['total_fixed_expenses'] if fixed_expenses['total_fixed_expenses'] is not None else 0

# 月々の返済合計計算
def calculate_total_payment(cur, user_id):
    cur.execute('''
        SELECT SUM(debt_type.monthly_payment) AS total_payment
        FROM payment_task
        JOIN debt_type ON payment_task.debt_type_id = debt_type.id
        WHERE payment_task.user_id = %s
        AND TO_CHAR(payment_task.due_date, 'YYYY-MM') = TO_CHAR(NOW(), 'YYYY-MM')
    ''', (user_id,))
    total_payment = cur.fetchone()
    return total_payment['total_payment'] if total_payment['total_payment'] is not None else 0


# その他の支出合計計算
def calculate_total_expenses(cur, user_id):
    cur.execute('''
        SELECT SUM(amount) AS total_expenses
        FROM expense
        WHERE user_id = %s 
    ''', (user_id,))
    other_expenses = cur.fetchone()
    print(other_expenses)
    return other_expenses['total_expenses'] if other_expenses['total_expenses'] is not None else 0

# 日割りで使える金額計算
def calculate_daily_allowance(income, total_payment, fixed_expenses, total_expenses):
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    remaining_days = days_in_month - today.day + 1

    usable_income = income - total_payment - fixed_expenses - total_expenses
    daily_allowance = usable_income / remaining_days if remaining_days > 0 else 0
    formatted_daily_allowance = f"{int(daily_allowance):,}"
    return formatted_daily_allowance


# 毎月1日に借金返済タスクを生成する関数
# Generate monthly payment tasks automatically
def create_monthly_tasks():
    conn =  create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT id FROM app_user')
    users = cur.fetchall()
    conn.commit()
    for user in users:
        cur.execute('SELECT * FROM debt_type WHERE user_id = %s ', (user['id'],))
        debt_types = cur.fetchall()
        conn.commit()
        for debt in debt_types:
            cur.execute('INSERT INTO payment_task (user_id, debt_name, debt_type_id, monthly_payment, due_date, is_completed) VALUES (%s, %s, %s, %s, %s, %s)', 
             (user['id'], debt['debt_name'], debt['id'], debt['monthly_payment'], datetime.today().replace(day=1), False))

    conn.commit()
    conn.close()

# Flaskアプリにスケジューラをセットアップ
scheduler = BackgroundScheduler()
scheduler.add_job(func=create_monthly_tasks, trigger='cron', day=1, hour=0, minute=0)  # 毎月1日に実行
scheduler.start()


def reset_monthly_income(user_id):
    conn =  create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    today = datetime.today()
    # ユーザーのリセット日を取得
    cur.execute('SELECT income, expense, remaining_balance, reset_day FROM income_expense WHERE user_id = %s ', (user_id,))
    income_expense = cur.fetchone()
    conn.commit()

    if income_expense:
        reset_day = income_expense['reset_day']
        if today.day == reset_day:
            remaining_balance = income_expense['income'] - income_expense['expense']
            cur.execute('UPDATE income_expense SET remaining_balance = %s , income = 0, expense = 0 WHERE user_id = %s ',
                         (remaining_balance, user_id))
            conn.commit()
    
    conn.close()

def check_and_reset_incomes():
    conn =  create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT user_id FROM income_expense')
    users = cur.fetchall()
    for user in users:
        reset_monthly_income(user['user_id'])
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_reset_incomes, trigger='cron', hour=0)  # 毎日チェック
scheduler.start()

@app.route('/fonts')
def show_fonts():
    fonts = get_fonts()
    return render_template_string('''
    <h1>インストールされているフォントのリスト</h1>
    <ul>
        {% for font in fonts %}
            <li>{{ font }}</li>
        {% endfor %}
    </ul>
    ''', fonts=fonts)
    
@login_manager.user_loader
def load_user(user_id):
    conn =  create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM app_user WHERE id = %s ', (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        return app_user(user['id'], user['username'], user['password_hash'])
    return None

    
@app.route('/', methods=['GET', 'POST'])
def index():
    conn =  create_server_connection()
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

        conn =  create_server_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SELECT * FROM app_user WHERE username = %s ', (username,))
        existing_user = cur.fetchone()
        if existing_user:
            flash('そのユーザー名は既に使用されています。')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        cur.execute('INSERT INTO app_user (username, password_hash) VALUES (%s, %s)', (username, hashed_password))
        conn.commit()
        cur.execute('SELECT use_id FROM app_user WHERE username = %s ', (username,))
        newuserid = cur.fetchone()
        conn.commit()
        cur.execute('INSERT INTO expense_category (name, parent_category, user_id) VALUES (%s, %s, %s)', 
                     ("その他", "変動費", newuserid))
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
        conn =  create_server_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SELECT * FROM app_user WHERE username = %s ', (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            user_obj = app_user(user['id'], user['username'], user['password_hash'])
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

# レシート画像アップロードルート
@app.route('/upload_receipt', methods=['POST'])
@login_required
def upload_receipt():
    # ファイルが正しく送信されているか確認
    form = addreciptForm()
    if form.validate_on_submit():
        file = form.image.data
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # アップロードされた画像からテキストを抽出
            extracted_text = extract_text_from_image(file_path)

            if extracted_text=="テキスト抽出に失敗しました":
                flash('画像の登録に失敗しました')
                return redirect(url_for('dashboard'))
        
            for item in extracted_text:
                print(f"商品: {item['item']}, 金額: {item['amount']}円")
                conn =  create_server_connection()
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                category_id  = categorize_item(item['item'], current_user.id)
                # データベースに支出を追加
                cur.execute('INSERT INTO expense (user_id, amount, category_id, description) VALUES (%s, %s, %s, %s)', 
                     (current_user.id, item['amount'], category_id, "レシートからの登録"))
                conn.commit()
                conn.close()
            flash('画像のアップロードが成功しました: {}'.format(extracted_text))

            # 画像処理後、不要なら削除
            os.remove(file_path)

            return redirect(url_for('dashboard'))
    
        if file.filename == '':
            flash('ファイルが選択されていません')
            return redirect(url_for('dashboard'))
        
    flash('許可されていないファイル形式です')
    return redirect(url_for('dashboard'))

# タスク追加ルート
@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()

    # 借金の種類を取得して選択肢に設定
    conn =  create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT id, debt_name FROM debt_type WHERE user_id = %s ', (current_user.id,))
    debt_types = cur.fetchall()
    form.debt_type_id.choices = [(debt['id'], debt['debt_name']) for debt in debt_types]
    
    if form.validate_on_submit():
        # フォームからデータを取得し、タスクを登録
        debt_type_id = form.debt_type_id.data
        due_date = form.due_date.data
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('INSERT INTO payment_task (user_id, debt_type_id,debt_name,monthly_payment, due_date, is_completed) VALUES (%s, %s, %s, %s)', 
                     (current_user.id, debt_type_id, due_date, False))
        conn.commit()
        conn.close()

        flash('タスクが追加されました。')
        return redirect(url_for('dashboard'))

    return render_template('add_task.html', form=form)

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    conn =  create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('UPDATE payment_task SET is_completed = True WHERE id = %s AND user_id = %s ', (task_id, current_user.id))
    conn.commit()
    conn.close()

    flash('タスクが完了しました。')
    return redirect(url_for('dashboard'))

@app.route('/set_reset_day', methods=['GET', 'POST'])
@login_required
def set_reset_day():
    form = ResetDayForm()
    if form.validate_on_submit():
        reset_day = form.reset_day.data
        conn =  create_server_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('UPDATE income_expense SET reset_day = %s WHERE user_id = %s ', (reset_day, current_user.id))
        conn.commit()
        conn.close()
        flash('リセット日が更新されました。')
        return redirect(url_for('dashboard'))
    return render_template('set_reset_day.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    conn = create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # 支出の合計を取得
    cur.execute('SELECT SUM(amount) FROM expense WHERE user_id = %s ', (current_user.id,))
    total_expense = cur.fetchone()
    conn.commit()
    total_expenses = total_expense[0] if total_expense[0] is not None else 0
    cur.execute('SELECT id, debt_type_id,debt_name,monthly_payment, is_completed FROM payment_task WHERE user_id = %s ', (current_user.id,))
    tasks = cur.fetchall()
    conn.commit()
    # 各taskを辞書に変換してから処理
    
    task_list = []
    for task in tasks:
        task_dict = dict(task)  # Rowオブジェクトを辞書に変換
        task_list.append(task_dict)
    print(task_list)
    cur.execute('SELECT * FROM debt_type WHERE user_id = %s ', (current_user.id,))
    debt_types = cur.fetchall()
    conn.commit()
    cur.execute('SELECT * FROM income_expense WHERE user_id = %s ', (current_user.id,))
    income_expense = cur.fetchone()
    conn.commit()
    income_form = IncomeForm()    
    # ユーザーの収入を取得
    cur.execute('SELECT income FROM income_expense WHERE user_id = %s ', (current_user.id,))
    income_row = cur.fetchone()
    conn.commit()
    income = income_row['income'] if income_row else 0

    # 固定費合計
    fixed_expenses = calculate_fixed_expenses(cur, current_user.id)
    # 月々の返済額合計
    total_payment = calculate_total_payment(cur, current_user.id)
    # その他支出の合計
    total_expenses = calculate_total_expenses(cur, current_user.id)
    # 日割りで使える金額を計算
    daily_allowance = calculate_daily_allowance(income, total_payment, fixed_expenses, total_expenses)

    conn.close()

    # フォームオブジェクトの作成
    task_form = TaskForm()
    income_form = IncomeForm()
    expense_form = AddExpenseForm()
    category_form = AddCategoryForm()
    debt_form = DebtTypeForm()
    reset_form = ResetDayForm()
    recipt_form = addreciptForm()

    # フォームをテンプレートに渡す
    return render_template('dashboard.html', 
                           tasks=task_list, 
                           debt_types=debt_types, 
                           income_expense=income_expense,
                           task_form=task_form,
                           income_form=income_form,
                           expense_form=expense_form,
                           debt_form=debt_form,
                           category_form=category_form,
                           total_expense=total_expenses,
                           month_total_payment=total_payment,
                           daily_allowance=daily_allowance,
                           reset_form = reset_form,
                           recipt_form = recipt_form)



@app.route('/expense_category_chart')
@login_required
def expense_category_chart():
    conn = create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
    SELECT expense_category.name, SUM(expense.amount) as total_amount 
    FROM expense
    JOIN expense_category ON expense.category_id = expense_category.id
    WHERE expense.user_id = %s
    GROUP BY expense_category.name, expense_category.id
    ''', (current_user.id,))
    expenses = cur.fetchall()
    conn.close()

    labels = [expense['name'] for expense in expenses]
    values = [expense['total_amount'] for expense in expenses]
    print(labels,values)
    try:
        fig, ax = plt.subplots(figsize=(2, 2))  # 幅5インチ、高さ3インチの画像
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=150)  # dpi=300 で解像度を設定
        img.seek(0)
        return Response(img.getvalue(), mimetype='image/png')
    except Exception as e:
        print(f"Error generating chart: {e}")
        flash('グラフ生成中にエラーが発生しました')
        return redirect(url_for('dashboard'))

# カテゴリ追加ルート
@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    form = AddCategoryForm()
    if form.validate_on_submit():
        category_name = form.category_name.data
        parent_category = form.parent_category.data

        # カテゴリをデータベースに追加
        conn = create_server_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('INSERT INTO expense_category (name, parent_category, user_id) VALUES (%s, %s, %s)', 
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
    conn = create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM expense_category WHERE parent_category = %s AND user_id = %s ', ('固定費', current_user.id))
    fixed_categories = cur.fetchall()
    conn.commit()
    cur.execute('SELECT * FROM expense_category WHERE parent_category = %s AND user_id = %s ', ('変動費', current_user.id))
    variable_categories = cur.fetchall()
    conn.commit()

    # カテゴリ選択フィールドにデータを追加
    form.category_id.choices = [(category['id'], category['name']) for category in fixed_categories + variable_categories]

    if form.validate_on_submit():
        # フォームからデータを取得
        amount = form.amount.data
        description = form.description.data
        category_id = form.category_id.data

        # データベースに支出を追加
        cur.execute('INSERT INTO expense (user_id, amount, category_id, description) VALUES (%s, %s, %s, %s)', 
                     (current_user.id, amount, category_id, description))
        conn.commit()
        conn.close()

        flash('支出が追加されました。')
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html', form=form, fixed_categories=fixed_categories, variable_categories=variable_categories)

@app.route('/add_income', methods=['POST'])
@login_required
def add_income():
    income_form = IncomeForm()

    if income_form.validate_on_submit():
        income = income_form.income.data
        
        # データベースに収入を追加
        conn = create_server_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # 既存の収入/支出データがあるか確認
        cur.execute('SELECT * FROM income_expense WHERE user_id = %s ', (current_user.id,))
        income_expense = cur.fetchone()
        conn.commit()

        if income_expense:
            # 既存データがあれば更新
            cur.execute('UPDATE income_expense SET income = income + %s WHERE user_id = %s ', (income, current_user.id))
        else:
            # 新規にデータを作成
            cur.execute('INSERT INTO income_expense (user_id, income, expense) VALUES (%s, %s, 0)', (current_user.id, income))
        
        conn.commit()
        conn.close()

        flash('収入が追加されました。')
        return redirect(url_for('dashboard'))

    flash('収入の追加に失敗しました。')
    return redirect(url_for('dashboard'))

@app.route('/add_debt_type', methods=['POST'])
@login_required
def add_debt_type():
    debt_form = DebtTypeForm()

    if debt_form.validate_on_submit():
        debt_name = debt_form.debt_name.data
        total_debt = debt_form.total_debt.data
        monthly_payment = debt_form.monthly_payment.data

        # データベースに借金の種類を追加
        conn = create_server_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('INSERT INTO debt_type (debt_name, total_debt, monthly_payment, user_id) VALUES (%s, %s, %s, %s)',
                     (debt_name, total_debt, monthly_payment, current_user.id))
        conn.commit()

        # 追加された借金のIDを取得
        cur.execute('SELECT id FROM debt_type WHERE user_id = %s ORDER BY id DESC LIMIT 1',
                                (current_user.id,))
        new_debt = cur.fetchone()
        conn.commit()

        # 初回のタスクを自動生成 (例えば、当月の1日に設定)
        due_date = datetime.today().replace(day=1)  # 今月の1日
        cur.execute('INSERT INTO payment_task (user_id, debt_type_id, debt_name, due_date, monthly_payment,is_completed) VALUES (%s, %s, %s, %s,%s, %s)',
                     (current_user.id, new_debt['id'], debt_name, due_date,monthly_payment, False))
        conn.commit()
        conn.close()

        flash('借金の種類と初回返済タスクが追加されました。')
        return redirect(url_for('dashboard'))

    flash('借金の種類の追加に失敗しました。')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    with app.app_context():
        init_db()  # アプリ起動時にデータベースを初期化
    app.run(host="0.0.0.0", port=8080, debug=True)

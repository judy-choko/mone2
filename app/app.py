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
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired
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
import json
import re
import requests
from openai import OpenAI
from io import BytesIO
from PIL import Image
import io
from google.cloud import vision
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_CREDS = os.environ["GOOGLE_API_CREDS"]
DBURL = os.environ["DBURL"]
DATABASE_URL = os.environ["DATABASE_URL"]
DBNAME = os.environ["DBNAME"]
LOCALHOST = os.environ["LOCALHOST"]
ROOTPASS = os.environ["ROOTPASS"]
USERNAME = os.environ["USERNAME"]
OPEN_AI_KEYS = os.environ["OPEN_AI_KEYS"]
SEC_NUMBERS= os.environ["SEC_NUMBERS"]

# プッシュ
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

file = json.loads(GOOGLE_API_CREDS)
path = 'data/test.json'
with open(path, 'w') as f:
    json.dump(file, f, indent=2)
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=path

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = SEC_NUMBERS
csrf = CSRFProtect(app)

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


def gettext(data):
    client = vision.ImageAnnotatorClient()
    content = data.read()
    image = vision.Image(content=content)
    response =  client.document_text_detection(
            image=image,
            image_context={'language_hints': ['ja']}
        )

    try:
        meisai = response.text_annotations[0].description
        # Print the extracted text
        client = OpenAI(
            # This is the default and can be omitted
            api_key=OPEN_AI_KEYS,
        )
        prompt = '購入した商品と金額のデータを作成して。JSON形式のデータのみ返してください。コードブロックとしてではなく、直接JSONデータだけをお願いします。カテゴリは固定費：住宅費、水道光熱費、通信料、保険料、車両費、保育料・学費、税金、習い事、交通費、小遣い、その他。変動費：食費、日用品費、医療費、子ども費、被服費、美容費、交際費、娯楽費、雑費、特別費。の中から選び、データのフォーマットは次の通りです。{data:[{"name":項目名,"price":金額,"parent_category":固定費or変動費,"category":カテゴリ名},]}以下データ：'+meisai
        messages = [{"role": "system", "content": prompt}]
        response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
        res = response.choices[0].message.content
        updated_json = json.loads(res)
        return updated_json
    except KeyError:
        print("Key 'text' not found in the JSON response")
        return "読み取りエラー"
    
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

        
def create_server_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
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

def create_categories(newuserid):
    print("カテゴリ登録")
    conn = create_server_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # 複数のデータを一度に挿入
    data = [
    ('住宅費', '固定費', newuserid),
    ('水道光熱費', '固定費', newuserid),
    ('通信料', '固定費', newuserid),
    ('保険料', '固定費', newuserid),
    ('車両費', '固定費', newuserid),
    ('保育料・学費', '固定費', newuserid),
    ('税金', '固定費', newuserid),
    ('習い事', '固定費', newuserid),
    ('交通費', '固定費', newuserid),
    ('小遣い', '固定費', newuserid),
    ('その他', '固定費', newuserid),
    ('食費', '変動費', newuserid),
    ('日用品費', '変動費', newuserid),
    ('医療費', '変動費', newuserid),
    ('子ども費', '変動費', newuserid),
    ('被服費', '変動費', newuserid),
    ('美容費', '変動費', newuserid),
    ('交際費', '変動費', newuserid),
    ('娯楽費', '変動費', newuserid),
    ('雑費', '変動費', newuserid),
    ('特別費', '変動費', newuserid)
    ]
    # SQLクエリ文を修正し、executemanyで一度に挿入
    for category in data:
        # カテゴリがすでに存在するかをチェックする
        cur.execute('''
            SELECT * FROM expense_category 
            WHERE name = %s AND parent_category = %s AND user_id = %s
        ''', category)
    
        # 結果がない場合にのみ挿入
        if cur.fetchone() is None:
            cur.execute('''
                INSERT INTO expense_category (name, parent_category, user_id) 
                VALUES (%s, %s, %s)
            ''', category)
            conn.commit()
    
    conn.close()

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
    
    # category_id 列を payment_task テーブルに追加
    cur.execute('''
            ALTER TABLE payment_task
            ADD COLUMN IF NOT EXISTS category_id INTEGER;
        ''')

        # 外部キー制約を追加して、category_id が expense_category テーブルの id に紐づくようにする
    cur.execute('''
            ALTER TABLE payment_task
            ADD CONSTRAINT fk_category
            FOREIGN KEY (category_id) 
            REFERENCES expense_category(id);
     ''')

    conn.commit()

    # category_id 列を payment_task テーブルに追加
    cur.execute('''
            ALTER TABLE debt_type
            ADD COLUMN IF NOT EXISTS category_id INTEGER;
        ''')

        # 外部キー制約を追加して、category_id が expense_category テーブルの id に紐づくようにする
    cur.execute('''
            ALTER TABLE debt_type
            ADD CONSTRAINT fk_category
            FOREIGN KEY (category_id) 
            REFERENCES expense_category(id);
     ''')

    conn.commit()
    cur.execute('''
        ALTER TABLE debt_type
        ALTER COLUMN total_debt SET DEFAULT 0;
    ''')

    cur.execute('''
        ALTER TABLE debt_type
        ADD CONSTRAINT check_total_debt CHECK (total_debt >= 0);
    ''')

    conn.commit()
    conn.close()
    

# ログインフォームの定義
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

class AssignCategoryForm(FlaskForm):
    tasks =  SelectField('タスク', validators=[DataRequired()])
    category = SelectField('カテゴリ', validators=[DataRequired()], coerce=int)
    submit = SubmitField('カテゴリを設定')
class addreciptForm(FlaskForm):
    image = FileField('画像を選択', validators=[DataRequired(), FileAllowed(['jpg', 'png','jpeg','JPEG','PNG','JPG'], '画像形式のみ許可されています')])
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
        conn.close()
        conn =  create_server_connection()
        cur.execute('SELECT use_id FROM app_user WHERE username = %s ', (username,))
        newuserid = cur.fetchone()
        conn.commit()
        cur.execute('INSERT INTO expense_category (name, parent_category, user_id) VALUES (%s, %s, %s)', 
                     ("その他", "変動費", newuserid))
        conn.commit()
        conn.close()
        create_categories(newuserid)
        flash('登録が成功しました！ログインしてください。')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def logsecretcommand():
    create_categories(current_user.id)
    flash('カテゴリを追加したよ。')
    return redirect(url_for('dashboard'))

@app.route('/assign_category', methods=['GET', 'POST'])
@login_required
def assign_category():
    conn = create_server_connection()
    cur = conn.cursor()

    # タスク情報を取得
    cur.execute('''
        SELECT debt_name FROM payment_task
        WHERE category_id IS NULL
        AND user_id = %s
    ''', (current_user.id,))
    tasks = cur.fetchone()

    if not tasks:
        flash('タスクが見つかりません。')
        return redirect(url_for('dashboard'))

    # ユーザーのカテゴリを取得して選択肢に設定
    cur.execute('SELECT id, name FROM expense_category WHERE user_id = %s', (current_user.id,))
    categories = cur.fetchall()

    form = AssignCategoryForm()
    form.category.choices = [(category[0], category[1]) for category in categories]
    form.tasks.choices = [(task) for task in tasks]
    if form.validate_on_submit():
        # 選択されたカテゴリIDをタスクに割り当てる
        cur.execute('UPDATE payment_task SET category_id = %s WHERE debt_name = %s AND user_id = %s', 
                    (form.category.data, form.tasks.data, current_user.id))
        
        conn.commit()
        cur.execute('UPDATE debt_type SET category_id = %s WHERE debt_name = %s AND user_id = %s', 
                    (form.category.data, form.tasks.data, current_user.id))
        conn.commit()
        flash('カテゴリが設定されました。')
        return redirect(url_for('assign_category'))

    conn.close()
    return render_template('assign_category.html', form=form)

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
@app.route('/upload_receipt', methods=['GET', 'POST'])
@login_required
def upload_receipt():
    form = addreciptForm()
    if form.validate_on_submit():
        file = form.image.data  # 画像ファイルを取得
        data_lest = gettext(file)

        if data_lest=="読み取りエラー":
            flash('読み取りできませんでした')
            return redirect(url_for('dashboard'))
        if data_lest:
            for i in range(len(data_lest["data"])):
                name = data_lest["data"][i]["name"]
                price = data_lest["data"][i]["price"]
                parent_category = data_lest["data"][i]["parent_category"]
                category = data_lest["data"][i]["category"]
                conn =  create_server_connection()
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute("""
                            SELECT id 
                            FROM expense_category 
                            WHERE user_id = %s AND name = %s;
                            """, (current_user.id, category))
                # データベースに支出を追加
                category_id = cur.fetchone()
                conn.commit()
                if not category_id:
                    cur.execute('INSERT INTO expense (user_id, amount, category_id, description) VALUES (%s, %s, %s, %s)', 
                     (current_user.id, price, 1, name))
                    conn.commit()

                else :
                    cur.execute('INSERT INTO expense (user_id, amount, category_id, description) VALUES (%s, %s, %s, %s)', 
                     (current_user.id, price, category_id, name))
                    conn.commit()
                conn.close()
            flash('画像のアップロードが成功しました')
            return redirect(url_for('dashboard'))
    
        if data_lest == '':
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

        flash('定期的支払いの種類と初回返済タスクが追加されました。')
        return redirect(url_for('dashboard'))

    flash('定期的支払いの種類の追加に失敗しました。')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    with app.app_context():
        init_db()  # アプリ起動時にデータベースを初期化
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

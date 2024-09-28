import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# データベース接続用の関数
def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row  # クエリ結果を辞書形式で取得できるようにする
    return conn

# テーブルを初期化するための関数
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debt_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            total_debt INTEGER NOT NULL,
            monthly_payment INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            debt_type_id INTEGER NOT NULL,
            due_date TEXT DEFAULT CURRENT_TIMESTAMP,
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(debt_type_id) REFERENCES debt_type(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_category TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(category_id) REFERENCES expense_category(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income_expense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            income INTEGER NOT NULL,
            expense INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
    ''')

    conn.commit()
    conn.close()

# ユーザークラスの定義
class User:
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create_user(username, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO user (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_by_username(username):
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['password_hash'])
        return None

# 他のテーブルに対する操作も同様に、SQLを直接使って行います。

class DebtType:
    @staticmethod
    def create_debt_type(user_id, name, total_debt, monthly_payment):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO debt_type (user_id, name, total_debt, monthly_payment)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, total_debt, monthly_payment))
        conn.commit()
        conn.close()

class PaymentTask:
    @staticmethod
    def create_task(user_id, debt_type_id, due_date, is_completed=False):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payment_task (user_id, debt_type_id, due_date, is_completed)
            VALUES (?, ?, ?, ?)
        ''', (user_id, debt_type_id, due_date, is_completed))
        conn.commit()
        conn.close()

class ExpenseCategory:
    @staticmethod
    def create_category(user_id, name, parent_category):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expense_category (user_id, name, parent_category)
            VALUES (?, ?, ?)
        ''', (user_id, name, parent_category))
        conn.commit()
        conn.close()

class Expense:
    @staticmethod
    def add_expense(user_id, amount, category_id, description):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expense (user_id, amount, category_id, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, category_id, description))
        conn.commit()
        conn.close()

class IncomeExpense:
    @staticmethod
    def add_income_expense(user_id, income, expense):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO income_expense (user_id, income, expense)
            VALUES (?, ?, ?)
        ''', (user_id, income, expense))
        conn.commit()
        conn.close()

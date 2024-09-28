# Pythonの公式イメージを使用
FROM python:3.9-slim

# 作業ディレクトリを作成
WORKDIR /app

# 必要なパッケージをインストール
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Flaskアプリを起動するための環境変数を設定
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# ポート5000をコンテナ外部に公開
EXPOSE 5000

# Flaskアプリケーションを起動
CMD ["flask", "run", "--host=0.0.0.0"]

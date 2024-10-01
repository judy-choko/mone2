# Pythonの公式イメージを使用
FROM python:3.9-slim

RUN echo "Database URL: "{$GOOGLE_API_CREDS}
# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    apt-utils \
    pkg-config \
    libpq-dev \
    libmariadb-dev \
    gcc \
    g++ \
    fontconfig \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set the working directory
WORKDIR /app

# Copy the application files to the container
COPY ./app/ /app/

RUN fc-cache -f -v
# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# 環境変数の設定
ENV FLASK_ENV=development
ENV FLASK_APP=app.py
# 環境変数の設定
ENV LANG=ja_JP.UTF-8
ENV PYTHONIOENCODING=utf_8
# ENV FLASK_ENV=production

# 環境変数を設定（必要に応じて適宜変更）
ENV GOOGLE_API_CREDS=${GOOGLE_API_CREDS}
ENV DBURL=${DBURL}
ENV DATABASE_URL=${DATABASE_URL}
ENV DBNAME=${DBNAME}
ENV LOCALHOST=${LOCALHOST}
ENV USERS_PASSWORDS=${PASSWORD}
ENV ROOTPASS=${ROOTPASS}
ENV USERNAME=${USERNAME}
ENV OPEN_AI_KEYS=${OPEN_AI_KEY}

ENV PATH="/home/chokokaruros/.local/bin:$PATH"

# SQLiteデータベースの初期化（テーブル作成などを行うスクリプトを実行）
RUN python -c 'from app import init_db; init_db()'

# ポート5000をコンテナ外部に公開
EXPOSE 8080

# Flaskアプリケーションを起動
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080","--log-level", "debug", "app:app"]

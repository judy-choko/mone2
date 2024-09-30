# Pythonの公式イメージを使用
FROM python:3.9-slim


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
COPY ./app.py /app/
COPY ./.env /app/
COPY ./forms.py /app/
COPY ./models.py /app/
COPY ./requirements.txt /app/
COPY ./heroku.yml /app/
COPY ./static /app/static/
COPY ./templates /app/templates/

# アプリケーションコードとフォントをコピー
COPY ./fonts /usr/share/fonts

# Copy and unzip the fonts to the appropriate directory
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

ENV PATH="/home/chokokaruros/.local/bin:$PATH"

# SQLiteデータベースの初期化（テーブル作成などを行うスクリプトを実行）
RUN python -c 'from app import init_db; init_db()'

# ポート5000をコンテナ外部に公開
EXPOSE 8080

# Flaskアプリケーションを起動
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080","--log-level", "debug", "app:app"]

# Pythonの公式イメージを使用
FROM python:3.9-slim


# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    fontconfig \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# アプリケーションコードとフォントをコピー
COPY ./fonts /usr/share/fonts

# フォントキャッシュを更新
RUN fc-cache -f -v


# 環境変数からパスワードを設定する
ARG ROOTPASS
RUN useradd -ms /bin/bash chokokaruros && echo "chokokaruros:$ROOTPASS" | chpasswd

# sudo 権限を追加
RUN usermod -aG sudo chokokaruros

# アプリケーションコードをコピー
COPY --chown=chokokaruros:chokokaruros . .

# chokokarurosユーザーに切り替える
USER chokokaruros

# 必要なパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

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

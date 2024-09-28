# Pythonの公式イメージを使用
FROM python:3.9-slim

# 作業ディレクトリを作成
WORKDIR /app

# 必要なパッケージをインストールし、pipをアップグレード
RUN apt-get update && apt-get install -y --no-install-recommends gcc sudo \
    && pip install --upgrade pip

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

# ENV FLASK_ENV=production

ENV PATH="/home/chokokaruros/.local/bin:$PATH"

# データベースのマイグレーションとアップグレードを実行
RUN flask db init  # 初回のみ
RUN flask db upgrade
RUN flask db migrate || true  # 既存のマイグレーションがない場合でもエラーを無視


# ポート5000をコンテナ外部に公開
EXPOSE 8080

# Flaskアプリケーションを起動
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]

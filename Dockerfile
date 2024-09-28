# Pythonの公式イメージを使用
FROM python:3.9-slim

# 作業ディレクトリを作成
WORKDIR /app


# パッケージリストの更新と必要なパッケージのインストール
RUN apt-get update && \
    apt-get install -y wget fontconfig zip unzip fonts-migmix
# パッケージのインストールや他の設定
RUN wget https://noto-website-2.storage.googleapis.com/pkgs/NotoSansCJKjp-hinted.zip
RUN unzip NotoSansCJKjp-hinted.zip -d /usr/share/fonts/NotoSansCJKjp
RUN chmod 644 /usr/share/fonts/NotoSansCJKjp/*.otf
RUN fc-cache -fv
RUN fc-list

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

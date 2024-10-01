# Pythonの公式イメージを使用
FROM python:3.9-slim

# Create and set the working directory
WORKDIR /app

# Copy the application files to the container
COPY ./app/ /app/

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

EXPOSE 5000

# Flaskアプリケーションを起動
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:$PORT", "app:app"]
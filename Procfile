release: apt-get install -y fonts-noto-cjk && fc-cache -fv && python -c 'from app import init_db; init_db()'
web: gunicorn app:app

web: gunicorn  app:app port:8080
release: python -c 'from app import init_db; init_db()'

import os
import json
from flask import Flask
from dotenv import load_dotenv
load_dotenv()


TORIAEZU = os.environ.get("TORIAEZU")
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return "hello"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)


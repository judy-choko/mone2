import os
import json
from flask import Flask
from dotenv import load_dotenv
load_dotenv()
TORIAEZU=os.environ["TORIAEZU"]
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return "hello"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


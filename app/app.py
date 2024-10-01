import os
import json
from flask import Flask
from dotenv import load_dotenv
load_dotenv()


GOOGLE_API_CREDS = os.environ["GOOGLE_API_CREDS"]
DBURL = os.environ["DBURL"]
TORIAEZU = os.environ["TORIAEZU"]
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    print(GOOGLE_API_CREDS)
    return str(TORIAEZU)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)


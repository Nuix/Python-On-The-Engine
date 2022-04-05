from flask import Flask
import json

app = Flask(__name__)


@app.route('/')
def hello():
    return json.dumps({'greet': 'hello'})

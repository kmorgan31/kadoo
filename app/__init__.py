from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__) #app - main app/website, __name__ - root path, help to find files in directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/kadoo' #allow connection to database

UPLOAD_FOLDER = 'static/profile/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

app.secret_key="SECRET_KEY"

db = SQLAlchemy(app)

db.create_all()

from app import controller, models
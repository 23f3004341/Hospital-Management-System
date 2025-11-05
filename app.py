from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app= Flask(__name__)

#Database Configuration (using SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://hospital_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

#Initialize SQLAlchemy instance
db = SQLAlchemy(app)
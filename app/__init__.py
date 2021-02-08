# app/__init__.py

from flask import Flask
from redis import Redis
from rq_scheduler import Scheduler
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

"""
This file shall contain configurations for the web app
"""


# create app
app = Flask(__name__)

db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()
# Handles login functionality eg creating and removing login sessions
login = LoginManager()


def create_app():
    global app, db, migrate, login, bootstrap
    app.config['SECRET_KEY'] = 'secretkey'

    # database set up
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Info.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Redis and RQ
    app.config['REDIS_URL'] = 'redis://'
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    # The queue where periodic tasks are submitted
    queue_name = 'ann_tasks'
    app.scheduler = Scheduler(queue_name, connection=app.redis)

    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)

    from app import models, views

    return app

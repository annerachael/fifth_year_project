# app/models.py

from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_login import UserMixin
from datetime import datetime
from app import db, login
import rq
import sys


"""
This module shall contain the tables of the database
"""


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    telephone = db.Column(db.Integer, unique=True, nullable=False)
    paid = db.Column(db.Boolean, nullable=False, default=False)
    date_paid = db.Column(db.DateTime, nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.now())
    # Relation between users and payments
    payer = db.relationship(
        'Payment',
        primaryjoin='Payment.source == User.telephone',
        backref='payer', lazy='dynamic',
    )

    @property
    def password(self):
        """
        Prevent password from being accessed
        """
        raise AttributeError('password is not a readable attribute.')

    @password.setter
    def password(self, password):
        """
        Set password to a hashed password
        """
        self.password_hash = generate_password_hash(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        Check if hashed password matches actual password
        """
        return check_password_hash(self.password_hash, password)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return 0
        except Exception as err:
            print(err)
            db.session.rollback()
            return 1

    def __repr__(self):
        return f"User('{self.username}', '{self.telephone}')"


@login.user_loader
def load_user(user_id):
    """
     Flask-Login knows nothing about databases, it needs the application's help in loading a user.
     For that reason, the extension expects that the application will configure a user loader function,
     that can be called to load a user given the ID
    """
    return User.query.get(int(user_id))


class Payment(db.Model):
    __tablename__ = 'payments'

    code = db.Column(db.Text, primary_key=True)
    sender = db.Column(db.Text, default='')
    creation_date = db.Column(db.DateTime, default=datetime.now())
    amount = db.Column(db.Text, default='Ksh0.00')
    source = db.Column('User', db.String(60),
                       db.ForeignKey('users.telephone', ondelete='CASCADE', onupdate='CASCADE'), )
    scheduled_task_id = db.Column(db.String(36), default='')

    def __repr__(self):
        return f"Payment('{self.code}', 'Sender: {self.sender}', 'Phone: {self.source}')"


class ScheduledTask(db.Model):
    """
    Create a Scheduled Task table
    All processes that are planned to be executed at a specified or periodically shall be stored here
    Interval shall be saved in seconds
    """
    __tablename__ = 'scheduled_tasks'

    id = db.Column(db.String(36), primary_key=True, nullable=False)
    name = db.Column(db.String(128), index=True)
    start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    interval = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    cancelled = db.Column(db.Boolean, default=False)

    @staticmethod
    def get_scheduled_task(task_id):
        try:
            # Loads the Job instance from the data that exists in Redis about it
            rq_job = rq.job.Job.fetch(task_id, connection=current_app.redis)
        except BaseException as err:
            print(err)
            current_app.logger.exception(err, exc_info=sys.exc_info())
            return None
        return rq_job

    def cancel_scheduled_task(self, job):
        """
        Given a job, check if it is in scheduler and cancel it if true
        :param job: RQ Job or Job ID
        :return: None
        """
        try:
            status = 0
            scheduler = current_app.scheduler
            if job and (type(job) == rq.job or type(job) == str) and job in scheduler:
                scheduler.cancel(job)
                self.cancelled = True
                status = self.save()
            return status
        except BaseException as err:
            print(err)
            current_app.logger.exception(err, exc_info=sys.exc_info())
            return 'Unable to cancel scheduled task'

    @staticmethod
    def retrieve_scheduled_tasks(tasks: list):
        _tasks = []
        for task in tasks:
            _tasks.append(
                {
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'cancelled': task.cancelled,
                    'beginning': task.start.strftime("%A %b %d, %Y %I:%M %p"),
                    'interval': task.interval,
                }
            )
        return _tasks

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return 0
        except Exception as err:
            print(err)
            db.session.rollback()
            return 1

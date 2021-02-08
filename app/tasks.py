# app/tasks.py

from app.models import User, Payment, ScheduledTask
from app import create_app
from datetime import datetime, timedelta
import sys
import pytz

"""
This module shall contain the background tasks run in the app
"""


# Get a Flask application instance and application context
app = create_app()
app.app_context().push()


def check_payment_status(telephone, payment_code):
    try:
        _user = User.query.filter_by(telephone=telephone).first()
        if not _user:
            app.logger.exception('User not registered', exc_info=sys.exc_info())
            return
        payment = Payment.query.filter(Payment.code == payment_code).first()
        if not payment:
            app.logger.exception("This is an invalid code", exc_info=sys.exc_info())
            return
        date_paid = _user.date_paid.astimezone(tz=pytz.timezone('Africa/Nairobi'))
        now = datetime.now(tz=pytz.timezone('Africa/Nairobi'))
        print("Running")
        passed_time = now - date_paid
        deadline = timedelta(minutes=1) if app.debug else timedelta(days=30)
        if passed_time >= deadline:
            _user.paid = False
            status = _user.save()
            if status:
                return
            # Cancel booking's current hourly scheduled task
            scheduled_task = ScheduledTask.query.filter(ScheduledTask.id == payment.scheduled_task_id).first()
            if not scheduled_task:
                app.logger.exception('No such scheduled task', exc_info=sys.exc_info())
                return
            res = scheduled_task.cancel_scheduled_task(payment.scheduled_task_id)
            if res:
                app.logger.exception(f"Unable to cancel scheduled task for payment: {payment.code}",
                                     exc_info=sys.exc_info())
                return
            print("Cancelled")
    except Exception as err:
        print(err)
        app.logger.exception("Unhandled exception", exc_info=sys.exc_info())
        return

# app/views.py

from flask import render_template, redirect, url_for, make_response, request, flash, jsonify
from flask_login import login_user, logout_user, login_required
from app.forms import SignUpForm, LoginForm
from app.models import User, Payment, ScheduledTask
from datetime import datetime
from app import app, db
import phonenumbers
import pytz

"""
This module shall contain the endpoints(routes) of the web app
"""


@app.route('/')
def home():
    return redirect(url_for('login'))


def process_telephone(telephone):
    phone = phonenumbers.parse(telephone, "KE")
    phone_number = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    return phone_number


# cookies on login and sign up capture user_id details for verification if code is sent.

# post get data, get post data
@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    try:
        if form.validate_on_submit():
            password = form.password.data
            username = form.username.data
            telephone = form.telephone.data
            phone_number = process_telephone(telephone)
            # Map object `user` of class `User` to a record of table User
            _user = User(
                username=username,
                password=password,
                telephone=phone_number,
            )
            # Add record to database
            db.session.add(_user)
            # Save changes to db
            db.session.commit()

            # Log user in and create session
            login_user(_user, remember=form.remember_me.data)

            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie("userID", f"{_user.id}")
            return resp
    except Exception as err:
        print(err)
        db.session.rollback()
        form.submit.errors.append(f"Error saving user:{err}")
    return render_template('signup.html', form=form)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    try:
        if form.validate_on_submit():
            # Log user in and create session
            _user = User.query.filter_by(telephone=process_telephone(form.telephone.data)).first()
            login_user(_user, remember=form.remember_me.data)
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie("userID", f"{_user.id}")
            return resp
    except Exception as err:
        print(err)
        db.session.rollback()
        form.submit.errors.append(f"Error saving user:{err}")
    return render_template('login.html', form=form)


@app.route('/logout/')
def logout():
    try:
        logout_user()
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie("userID", None)
        return resp
    except Exception as err:
        print(err)
        return redirect(url_for('login'))


@app.route('/dashboard/')
@login_required
def dashboard():
    user_id = request.cookies.get('userID')
    _user = User.query.filter_by(id=user_id).first()
    if not _user:
        flash("This user doesn't exist")
        return redirect(url_for("logout"))
    return render_template('user.html', paid=_user.paid)


@app.route('/code/', methods=["POST"])
@login_required
def code():
    try:
        user_id = request.cookies.get('userID')
        _user = User.query.filter_by(id=user_id).first()
        if not _user:
            flash("This user doesn't exist")
            return redirect(url_for("logout"))
        form = request.form
        text = form.get("code", default="")
        if not text:
            flash("No code received")
        else:
            payment = Payment.query.filter(Payment.code == text).first()
            if not payment:
                flash("This is an invalid code")
            else:
                # Set up a background task
                rq_job = app.scheduler.schedule(
                    scheduled_time=datetime.utcnow(),  # Time for first execution, in UTC timezone
                    interval=1 if app.debug else 60,  # Time before the function is called again, in minutes
                    func='app.tasks.check_payment_status',  # Function to be queued
                    # Keyword arguments passed into function when executed
                    kwargs={'telephone': _user.telephone, 'payment_code': payment.code},
                )
                # Create a corresponding Task object in database based on RQ-assigned task ID
                task = ScheduledTask(
                    id=rq_job.get_id(),
                    name='app.tasks.check_payment_status',
                    start=datetime.utcnow(),
                    interval=1 if app.debug else 60,
                    description='Checking payment status',
                )
                status = task.save()
                if status:
                    flash("Unable to check payment")
                else:
                    payment.scheduled_task_id = task.id
                    db.session.add(payment)
                    db.session.commit()
                    # Update user's paid status
                    _user.paid = True
                    _user.date_paid = datetime.now(tz=pytz.timezone('Africa/Nairobi'))
                    db.session.add(_user)
                    db.session.commit()
    except Exception as err:
        print(err)
        db.session.rollback()
    return redirect(url_for("dashboard"))


@app.route('/receiver', methods=['POST', 'GET'])
def receiver():
    try:
        data = request.get_json()
        if not data:
            return make_response(jsonify({'message': "No data received", 'status': -2})), 401

        sender, amount, date = data.get('sender', ''), data.get('amount', 'Ksh0.00'), data.get('date', '0')
        phone, _id = data['phone'], data['id']

        if not phone:
            return make_response(jsonify({'message': "No phone number received", "status": -3})), 401
        if not _id:
            return make_response(jsonify({'message': "No MPESA code received", "status": -3})), 401
        if not amount:
            return make_response(jsonify({'message': "No amount received", "status": -3})), 401

        if not date or int(date) == 0:
            date = datetime.now()
        else:
            date = datetime.fromtimestamp(int(date) / 1000.0)
            print(date)

        if sender == 'Sample sender':
            return make_response(jsonify({'message': "Success", "status": 0}))

        _user = User.query.filter_by(telephone=process_telephone(phone)).first()
        if not _user:
            return make_response(jsonify({'message': 'User not registered', "status": -4})), 401

        payment = Payment.query.filter(Payment.code == _id).first()
        if payment:
            return make_response(jsonify({'message': "MPESA transaction already saved", "status": -5})), 401

        price = float(amount.split("h")[-1])
        if not price:
            return make_response(jsonify({'message': "No amount received", "status": -6})), 401

        if price >= 5.0:
            payment = Payment(code=_id, sender=sender, creation_date=date, amount=amount, source=phone)
            try:
                # Add record to database
                db.session.add(payment)
                # Save changes to db
                db.session.commit()
            except Exception as err:
                print(err)
                db.session.rollback()
                return ({'message': 'unable to save payment. Please contact admin', 'status': 1}), 401
        else:
            return make_response(jsonify({'message': "1000/= needed for internet connection", "status": -7})), 401
        return make_response(jsonify({'message': "Success", "status": 0}))
    except Exception as err:
        print(err)
        return make_response(jsonify({'message': "Error receiving MPESA response", "status": -1})), 401

from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from forms import SignUpForm, LoginForm
import phonenumbers
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#create app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'

#database set up
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///Info.db'
db = SQLAlchemy(app)
Bootstrap(app)
# Handles login functionality eg creating and removing login sessions
login = LoginManager(app)
#


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    telephone = db.Column(db.Integer, unique=True, nullable=False)
    paid = db.Column(db.Boolean, nullable=False, default=False)
    date_paid = db.Column(db.DateTime, nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.now())

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

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.telephone}')"


@login.user_loader
def load_user(user_id):
    """
     Flask-Login knows nothing about databases, it needs the application's help in loading a user.
     For that reason, the extension expects that the application will configure a user loader function,
     that can be called to load a user given the ID
    """
    return User.query.get(int(user_id))


# Executes before the first request is processed.
@app.before_first_request
def init_db():
    """
    Method creates and initializes the models used
    :return: None
    """
    try:
        # Create any database tables that don't exist yet.
        db.create_all()
    except Exception as err:
        print(err)
        db.session.rollback()


#route
@app.route('/')
def home():
    return redirect(url_for('login'))


def process_telephone(telephone):
    phone = phonenumbers.parse(telephone, "KE")
    phone_number = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    return phone_number


#cookies on login and sign up capture user_id details for verification if code is sent.

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
            # Set up a background task
            sm = ''
            # Update user's paid status
            _user.paid = True
            db.session.add(_user)
            db.session.commit()
    except Exception as err:
        print(err)
    return redirect(url_for("dashboard"))

#route different pages

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp
from flask_wtf import FlaskForm
import os, logging, bleach

app = Flask(__name__, template_folder='templates', static_folder='static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///secure_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['SESSION_COOKIE_SECURE'] = False      
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24  


db = SQLAlchemy(app)
csrf = CSRFProtect(app)
bcrypt = Bcrypt(app)

class FirstApp(db.Model):
    sno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"{self.sno} - {self.fname}"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(190), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

name_regex = r"^[A-Za-z\s'\-]{2,120}$"

class RegisterForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120), Regexp(name_regex)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=190)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField('Register')

class AddPersonForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100), Regexp(name_regex)])
    lname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100), Regexp(name_regex)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=200)])
    submit = SubmitField('Add')

def sanitize_input(text):
    allowed_tags = ['b','i','u','em','strong','p','br','ul','li','ol']
    return bleach.clean(text or '', tags=allowed_tags, attributes={}, strip=True)

# ---------------------- Routes ----------------------
@app.route("/", methods=['GET', 'POST'])
def index():
    form = AddPersonForm()
    if form.validate_on_submit():
        fname = sanitize_input(form.fname.data)
        lname = sanitize_input(form.lname.data)
        email = sanitize_input(form.email.data)

        new_person = FirstApp(fname=fname, lname=lname, email=email)
        db.session.add(new_person)
        db.session.commit()
        flash("Person added successfully!", "success")
        return redirect("/")

    all_people = FirstApp.query.all()
    return render_template("index.html", form=form, people=all_people)

@app.route("/delete/<int:sno>")
def delete(sno):
    person = FirstApp.query.filter_by(sno=sno).first()
    if person:
        db.session.delete(person)
        db.session.commit()
        flash("Record deleted!", "info")
    return redirect("/")

@app.route("/update/<int:sno>", methods=['GET', 'POST'])
def update(sno):
    person = FirstApp.query.filter_by(sno=sno).first()
    form = AddPersonForm(obj=person)
    if form.validate_on_submit():
        person.fname = sanitize_input(form.fname.data)
        person.lname = sanitize_input(form.lname.data)
        person.email = sanitize_input(form.email.data)
        db.session.commit()
        flash("Record updated!", "success")
        return redirect('/')
    return render_template("update.html", form=form, person=person)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "danger")
            return render_template("register.html", form=form)
        user = User(full_name=form.full_name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect("/")
    return render_template("register.html", form=form)

@app.route("/home")
def home():
    return "<h2>Welcome to the Secure Home Page</h2>"

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"Server Error: {e}")
    return render_template("500.html"), 500


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    # Setup logging
    handler = logging.FileHandler('error.log')
    handler.setLevel(logging.ERROR)
    app.logger.addHandler(handler)
    app.run(host="0.0.0.0", port=5000, debug=False)

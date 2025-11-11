from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db, bcrypt
from models import User
from forms import RegisterForm, LoginForm, ContactForm
from utils import sanitize_input
from sqlalchemy import text

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    return '<h2>Secure Lab 08 App (secure_additions) - index</h2><p>Use /register, /login, /contact for tests.</p>'

@bp.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form)
        user = User(full_name=form.full_name.data, email=form.email.data)
        user.set_password(form.password.data, bcrypt)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully', 'success')
        return redirect(url_for('routes.login'))
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data, bcrypt):
            session.permanent = True
            session['user_id'] = user.id
            flash('Logged in', 'success')
            return redirect(url_for('routes.index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@bp.route('/contact', methods=['GET','POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = sanitize_input(form.message.data)
        stmt = text("INSERT INTO contacts (name, email, message) VALUES (:name, :email, :message)")
        try:
            db.session.execute(stmt, {'name': name, 'email': email, 'message': message})
            db.session.commit()
            flash('Message sent', 'success')
            return redirect(url_for('routes.index'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to save message', 'danger')
    return render_template('contact.html', form=form)

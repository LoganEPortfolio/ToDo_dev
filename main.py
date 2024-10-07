from flask import Flask, jsonify,  abort, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_ckeditor import CKEditor
from sqlalchemy.orm import relationship, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
from pprint import pprint
import pandas as pd
import numpy as np
import random
from datetime import date, datetime, timedelta
import os
from functools import wraps
from forms import AddTask, LoginUser, RegisterUser, EditTask

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor(app)

### Setup LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
sql_url = os.environ.get('SQL_URL')

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL', sql_url)
#db = SQLAlchemy(session_options={"autoflush": False})
db = SQLAlchemy()
db.init_app(app)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(250), nullable=False)
    #tasks = relationship('Task', back_populates='user')
    
class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    content = db.Column(db.String(1000))
    due = db.Column(db.String(250))
    date_created = db.Column(db.DateTime, default=datetime.now)
    category = db.Column(db.String(250), nullable=False)
    completed = db.Column(db.Boolean)
    completed_date = db.Column(db.String(250))
    notes = db.Column(db.Boolean)
    

with app.app_context():
    db.create_all()

#### Load User
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

#### Admin Only Function
def admin_only(f):
    @wraps(f)
    def wrapper_function(*args, **kwargs):
        if current_user.id == 1:
            return f(*args, **kwargs)
        else:
            abort(403)
    return wrapper_function

####Main route, brings up tasks due in 7 days
@app.route('/')
def home():
    week_from_now = datetime.now() + timedelta(days=7)
    if current_user.is_authenticated:
        tasks = db.session.query(Task).filter(Task.completed == False, Task.user_id == current_user.id, Task.due <= week_from_now, Task.notes == False).order_by(Task.due)
    else:
        tasks = ''     
    return render_template('index.html', tasks=tasks, notes=False)


@app.route('/<category>')
@login_required
def category_page(category):
    if current_user.is_authenticated:
        if category == 'all':
            tasks = db.session.query(Task).filter(Task.completed == False, Task.user_id == current_user.id, Task.notes == False).order_by(Task.due)
        elif category == 'pastdue':
            tasks = db.session.query(Task).filter(Task.completed == False, Task.user_id == current_user.id, Task.due < datetime.today()-timedelta(days=1), Task.notes == False).order_by(Task.due)
        elif category != 'pastdue':
            tasks = db.session.query(Task).filter(Task.completed == False, Task.user_id == current_user.id, Task.category == category).order_by(Task.due)
    else:
        tasks = ""
    return render_template('index.html', tasks=tasks, category=category)


@app.route('/task/<int:task_id>/notes-add')
@login_required
def notes_add(task_id):
    task = db.get_or_404(Task, task_id)
    if current_user.is_authenticated:
        task.due = ''
        task.notes = True
        db.session.commit()
    return redirect(request.referrer)

@app.route('/edit-notes/<int:task_id>', methods=["GET", "POST"])
@login_required
def edit_notes(task_id):
    task = db.get_or_404(Task, task_id)
    form = EditTask()
    if request.method == 'POST':
        task.content = request.form.get('ckeditor')
        db.session.commit()
        return redirect(url_for('get_task', task_id=task.id))
    return render_template('edit-task.html', task=task, form=form)


@app.route('/add', methods=["GET", "POST"])
@login_required
def add_task():
    form = AddTask()
    
    if form.validate_on_submit() and current_user.is_authenticated:
        with app.app_context():
            new_task = Task(
                title=request.form.get('title'),
                content=request.form.get('content'),
                due=request.form.get('due'),
                user_id = current_user.id,
                category = request.form.get('category'),
                completed = False,
                notes = False
            )
        db.session.add(new_task)
        db.session.commit()
    return render_template('add-task.html', form=form)


@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    task = db.get_or_404(Task, task_id)
    form = EditTask()
    if request.method == 'POST':
        task.content = request.form.get('ckeditor')
        task.due = request.form.get('due')
        task.category = request.form.get('category')
        task.notes = False
        db.session.commit()
        return redirect(url_for('get_task', task_id=task.id))
    return render_template('edit-task.html', task=task, form=form)


@app.route('/task/<task_id>')
@login_required
def get_task(task_id):
    task = db.get_or_404(Task, task_id)
    return render_template('task.html', task=task)


@app.route('/completed')
@login_required
def get_completed():
    tasks = db.session.query(Task).filter(Task.user_id == current_user.id, Task.completed == True)
    return render_template('index.html', tasks = tasks)


@app.route('/task/<int:task_id>/toggle')
@login_required
def toggle_complete(task_id):
    task = db.get_or_404(Task, task_id)
    task.completed = not task.completed
    task.completed_date = datetime.utcnow() if task.completed else None
    db.session.commit()
    return redirect(request.referrer)


@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task_to_delete = db.get_or_404(Task, task_id)
    if current_user.is_authenticated and current_user.id == task_to_delete.user_id:
        db.session.delete(task_to_delete)
        db.session.commit()
        
    if 'completed' in request.referrer:
        return redirect(url_for('get_completed'))
    else:
        return redirect(url_for('home'))

##### USER REGISTER/LOGIN
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterUser()
    if form.validate_on_submit():
        if db.session.execute(db.select(User).where(User.email == form.email.data)).scalar():
            flash("You've already signed up with that account. Please log in.")
            return redirect(url_for('login'))
        else:
            new_user = User(
                email = form.email.data,
                password = generate_password_hash(form.password.data, 'pbkdf2:sha256', 8),
                first_name = form.first_name.data
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(db.session.execute(db.select(User).where(User.email == form.email.data)).scalar())
            return redirect(url_for('home'))
    return render_template('register.html', form=form)
        
        
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginUser()
    if form.validate_on_submit():
        login_email = form.email.data
        login_pw = form.password.data
        user = db.session.execute(db.select(User).where(User.email == login_email)).scalar()
        
        if (user is None):
            flash("Email not found.")
        else:
            if (check_password_hash(user.password, login_pw) is False):
                flash("Incorrect Password.")
            else:
                login_user(user)
                return redirect(url_for('home'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
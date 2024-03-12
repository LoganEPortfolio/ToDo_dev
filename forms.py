from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, BooleanField, DateField, SelectField
from wtforms.validators import DataRequired, URL, Email, EqualTo, InputRequired


class RegisterUser(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired('This is required.')])
    email = StringField('Email', validators=[DataRequired('This is required.'), Email('Must be an email address.')])
    password = PasswordField('Password', validators=[InputRequired(), DataRequired('This is required.'), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', validators=[InputRequired(), DataRequired('This is required.'), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Submit')
    
class LoginUser(FlaskForm):
    email = StringField('Email', validators=[DataRequired('This is required.'), Email('Must be an email address.')])
    password = PasswordField('Password', validators=[DataRequired('This is required')])
    submit = SubmitField("Submit")
    
class AddTask(FlaskForm):
    title = StringField('Title', validators=[DataRequired('This is required.')])
    content = StringField('Content')
    due = DateField('Due Date')
    category = SelectField('Category', 
                           choices=[
                               ('work', 'Work'),
                               ('coding', 'Coding'),
                               ('comics', 'Comics'),
                               ('other', 'Other')
                               ], validators=[DataRequired('This is required.')])
    submit = SubmitField('Submit')
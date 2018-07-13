from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from ..models import  User
from wtforms import ValidationError


class LoginForm(FlaskForm):
    name = StringField(label='', validators=[DataRequired(), Length(min=6, max=20, message='用户名必须介于6-20个字符')],
                       render_kw={"placeholder": "username..."})
    email = StringField(label='', validators=[DataRequired(), Length(1, 64), Email()], render_kw={"placeholder": "Email..."})
    password = PasswordField(label='', validators=[DataRequired()], render_kw={"placeholder": "password..."})
    remember_me = BooleanField(label='remember', default=False)
    submit = SubmitField(label='Login')


class RegistrationForm(FlaskForm):
    email = StringField(label='', validators=[DataRequired(), Length(1, 64), Email()], render_kw={"placeholder": "Email..."})
    username = StringField(label='', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')], render_kw={"placeholder": "Username..."})
    # username = StringField(label='', validators=[
    #     DataRequired(), Length(1, 64)], render_kw={"placeholder": "Username..."})
    password = PasswordField(label='', validators=[DataRequired(), EqualTo('password2', message='Passwords must match')],
                             render_kw={"placeholder": "password..."})
    password2 = PasswordField(label='', validators=[DataRequired()], render_kw={"placeholder": "password_again..."})
    submit = SubmitField(label='register')

    # validate_ 开头的方法会在调用form.validate_on_submit()时被调用
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already registered')

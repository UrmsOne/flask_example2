from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import Required, DataRequired, Length
from flask_pagedown.fields import PageDownField

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    password = PasswordField()
    submit = SubmitField('submit')


class EditProfileForm(FlaskForm):
    name = StringField(label='Real name', validators=[Length(0, 64)])
    location = StringField(label='Location', validators=[Length(0, 64)])
    about_me = TextAreaField(label='About me')
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    title = StringField(label='', validators=[DataRequired(), Length(min=1, max=32, message='标题必须介于6-20个字符')],
                       render_kw={"placeholder": "title..."})
    body = PageDownField('what is your mind?', validators=[DataRequired()])
    submit = SubmitField('Submit')
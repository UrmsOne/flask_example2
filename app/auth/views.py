from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, login_required, logout_user, current_user
from . import auth
from .forms import LoginForm, RegistrationForm
from ..models import User
from .. import db
from ..email import send_email
from uuid import uuid4


@auth.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        print("if1")
        user = User.query.filter_by(email=form.email.data).first()
        # user = User.query.filter_by(username=form.name.data).first()
        if user is not None and user.verify_password(form.password.data):
            print('if2')
            login_user(user, form.remember_me.data)
            flash('You have signed in!')
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        print('if1')
        user = User(email=form.email.data, username=form.username.data, id=str(uuid4()))
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
        # flash('You can now login')
        flash('A confirmation email hsa been sent to you by email')
        return redirect(url_for('main.index'))
    print('not if')
    return render_template('/auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    # print('发送邮件')
    # send_email('18826238513@163.com', 'Confirm Your Account', 'auth/email/confirm', user={'name': 'hello'})
    # return '邮件发送成功'
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account.Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))
    

@auth.before_request
def before_request():
    # and request.endpoint[:5] != 'main.'
    if current_user.is_authenticated and not current_user.confirmed and request.endpoint[:5] != 'auth.'and request.endpoint != 'static':
    # if current_user.confirmed and current_user.is_authenticated:
        print('if1-b')
        return redirect(url_for('auth.unconfirmed'))
   

@auth.before_app_request
def before_request2():
    if current_user.is_authenticated:
        current_user.ping()
        # if not current_user.confirmed \
        #         and request.endpoint[:5] != 'auth.':
        #     return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_authenticated or current_user.confirmed and request.endpoint != 'static':
        print('if1-u')
        return redirect(url_for('main.index'))
    return render_template('auth.unconfirmed.html')


@auth.route('/confirm')
def resend_conf():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm', token=token, user=current_user)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))
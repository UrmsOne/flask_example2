from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, abort, request, current_app
from flask_login import login_required, current_user
from . import main
from .forms import NameForm, EditProfileForm, PostForm
from .. import db
from ..models import User, Permission, Post


@main.route('/', methods=["GET", "POST"])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object(), title=form.title.data)
        db.session.add(post)
        return redirect(url_for('main.index', username=current_user.username))
    # posts = Post.query.order_by(Post.timestamp.desc()).all()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['URMSONE_POSTS_PER_PAGE'], error_out=False
    )
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination)

    
@main.route('/example4_6', methods=["GET", "POST"])
def example4_6():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        print('if1')
        if old_name is not None and old_name != form.name.data:
            flash("Looks like you have changed your name!")
        session['name'] = form.name.data
        return redirect(url_for('.example4_6'))
    print('not if')
    return render_template('example4_3.html', form=form, name=session.get('name'))


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@main.route('/edit-profile', methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated')
        return  redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])



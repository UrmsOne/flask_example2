from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from datetime import datetime
from uuid import uuid4


@login_manager.user_loader
def loader_user(user_id):
    # return User.query.get(int(user_id))
    return User.query.get(user_id)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    # lazy='dynamic' -> 使用Role.users不会自动执行查询，可以在其上添加过滤器：role.users.order_by(User.username).all()
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User': (
                Permission.FOLLOW |
                Permission.COMMENT |
                Permission.WRITE_ARTICLES, True
            ),
            'Moderator': (
                Permission.FOLLOW |
                Permission.COMMENT |
                Permission.WRITE_ARTICLES |
                Permission.MODERATE_COMMENTS, False
            ),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


# class Post(db.Model):
#     # posts -> author => n : 1
#     __tablename__ = 'posts'
#     id = db.Column(db.Integer, primary_key=True)
#     body = db.Column(db.Text)
#     timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
#     author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.String(128), db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Post %r>' % self.title

    # 生成博客文章
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentence(),
                     timestamp=forgery_py.date.date(True),
                     title=forgery_py.lorem_ipsum.title(),
                     author=u)
            db.session.add(p)
            db.session.commit()



class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(128), primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # 用户的密码通过hash后再存入数据库
    password_hash = db.Column(db.String(128))
    # 邮箱确认
    confirmed = db.Column(db.Boolean, default=False)
    # 添加用户资料需要的字段
    # 用户真实姓名
    name = db.Column(db.String(64))
    # 所在地
    location = db.Column(db.String(64))
    # 自我介绍
    about_me = db.Column(db.Text())
    # 注册日期
    member_since = db.Column(db.DateTime(), default=datetime.utcnow())
    # 最后访问日期
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow())
    # 设置文章与作者的关系(posts是Post的对象组成的列表)
    # user = User(),user.posts -> 该作者的所有文章
    # post = Post(), post.author -> 文章的作者
    # posts = db.relationship('Post', backref='author', lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.id is None or self.id == '':
            self.id = str(uuid4())

    def __repr__(self):
        return '<User %r>' % self.username

    # 设置password方法当作属性使用
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    # 将password属性设置为only write属性
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 验证password
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 生成加密后的确认信息

    def generate_confirmation_token(self, expiration=3600):
        # 创建Serializer对象
        # config['SECRET_KEY']为密钥
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        # 使用Serializer对象的dumps方法对方法中的参数加密
        return s.dumps({'confirm.txt': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm.txt') != self.id:
            return False
        self.confirmed = True
        return True

    # 用户权限验证
    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # 刷新用户的最后访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    # 生成虚拟用户
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


# 保持登录与非登陆用户的一致性，不用先检查用户是否登录，就能自由调用 current_user.can()和current_user.is_administrator()
class AnonymousUser(AnonymousUserMixin):

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


# 匿名用户
login_manager.anonymous_user = AnonymousUser

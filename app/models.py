from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from datetime import datetime
import bleach
from markdown import markdown


# 权限常量
class Permission:
    COMMENT = 1
    WRITE = 2
    GROUP = 4
    ADMIN = 8


# 用户角色
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.COMMENT, Permission.WRITE],
            # 'Group_leader': [Permission.COMMENT, Permission.WRITE, Permission.GROUP],
            'Administrator': [Permission.COMMENT, Permission.WRITE, Permission.GROUP, Permission.ADMIN]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    @staticmethod  # 这是个危险的测试方法！
    def give_admin(stu_id):
        user = User.query.filter_by(stu_id=stu_id).first()
        user.role_id = 2
        db.session.add(user)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm
    # has_permission 方法用位与运算符检查组合权限是否包含指定的单独权限

    def __repr__(self):
        return '<Role %r>' % self.name


class Relation(db.Model):
    __tablename__ = 'relations'
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'),
                         primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                          primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def delete(self):
        db.session.delete(self)
        db.session.commit()


# 个人信息：邮箱，姓名，学号，生日，手机号，头像
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    stu_id = db.Column(db.String(13), unique=True)
    birthday = db.Column(db.DateTime(), default=datetime.utcnow)
    phone = db.Column(db.String(11))
    avatar = db.Column(db.String(128), default='default.jpg')  # 头像
    confirmed = db.Column(db.Boolean, default=False)  # 是否验证邮箱
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=1)  # 权限ID
    password_hash = db.Column(db.String(128))
    group_leader = db.relationship('Group', backref='leader', lazy='dynamic')
    my_weekly = db.relationship('Weekly', backref='author', lazy='dynamic')
    groups = db.relationship('Relation',
                             foreign_keys=[Relation.member_id],
                             backref=db.backref('member', lazy='joined'),
                             lazy='dynamic', cascade='all, delete-orphan')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm' : self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset':self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    # 删除用户的还需要把relations 表中的相关记录删除
    def delete(self):
        if self.is_administrator():
            return False
        db.session.delete(self)
        db.session.commit()

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def is_in_group(self, group):
        if group.id is None:
            return False
        return self.groups.filter_by(group_id=group.id).first() is not None

    def __repr__(self):
        return '<User %r>' % self.name


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(64), unique=True, index=True)
    group_leader = db.Column(db.Integer, db.ForeignKey('users.id'))
    introduction = db.Column(db.Text())
    notice = db.Column(db.Text())
    weekly = db.relationship('Weekly', backref='group', lazy='dynamic')
    members = db.relationship('Relation',
                              foreign_keys=[Relation.group_id],
                              backref=db.backref('group', lazy='joined'),
                              lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)
        relation = Relation(group=self, member_id=self.group_leader)
        db.session.add(relation)
        db.session.commit()

    # 删除方法还需要把relations 表中的相关记录删除
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def is_a_member(self, user):
        if user.id is None:
            return False
        return self.members.filter_by(member_id=user.id).first() is not None

    def __repr__(self):
        return '<Group %r>' % self.group_name


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


class Weekly(db.Model):
    __tablename__ = 'weekly'
    id = db.Column(db.Integer, primary_key=True)
    finished_work = db.Column(db.Text())
    summary = db.Column(db.Text())
    demands = db.Column(db.Text())
    plan = db.Column(db.Text())
    remarks = db.Column(db.Text())
    finished_work_html = db.Column(db.Text())
    summary_html = db.Column(db.Text())
    demands_html = db.Column(db.Text())
    plan_html = db.Column(db.Text())
    remarks_html = db.Column(db.Text())
    attachments = db.relationship('Attachment', backref='weekly', lazy='dynamic')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    belong_to = db.Column(db.Integer, db.ForeignKey('groups.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @staticmethod
    def on_change_finished_work(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.finished_work_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                           tags=allowed_tags, strip=True))

    @staticmethod
    def on_change_summary(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.summary_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                          tags=allowed_tags, strip=True))

    @staticmethod
    def on_change_demands(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.demands_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                          tags=allowed_tags, strip=True))

    @staticmethod
    def on_change_plan(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.plan_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                       tags=allowed_tags, strip=True))

    @staticmethod
    def on_change_remarks(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.remarks_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                          tags=allowed_tags, strip=True))


db.event.listen(Weekly.finished_work, 'set', Weekly.on_change_finished_work)
db.event.listen(Weekly.summary, 'set', Weekly.on_change_summary)
db.event.listen(Weekly.demands, 'set', Weekly.on_change_demands)
db.event.listen(Weekly.plan, 'set', Weekly.on_change_plan)
db.event.listen(Weekly.remarks, 'set', Weekly.on_change_remarks)


class Attachment(db.Model):
    weekly_id = db.Column(db.Integer, db.ForeignKey('weekly.id'),
                          primary_key=True)
    attachment_name = db.Column(db.String(128), unique=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

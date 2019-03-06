from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm,\
    PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm

from .. import db
from ..models import User
from ..email import send_email

# 该文件中传入render_template 的参数、列表解释：
# form 表单实例


@auth.before_app_request
def before_request():
    if not current_user.is_authenticated\
            and request.endpoint\
            and request.blueprint != 'auth'\
            and request.endpoint != 'static'\
            and request.endpoint != 'main.index':
        flash('请先登录')
        return redirect(url_for('auth.login'))  # 若没有登录则禁止访问除auth 和 main.index 之外的视图
    if current_user.is_authenticated:
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))  # 若没有验证邮箱则禁止访问除auth 之外的视图


# 未确认邮箱的视图函数
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


# 登录视图
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('无效的用户名或密码')
    return render_template('auth/login.html', form=form)


# 注销
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('账户已经登出')
    return redirect(url_for('main.index'))


# 注册
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    name=form.name.data,
                    stu_id=form.stu_id.data,
                    phone=form.phone.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, '确认您的账户',
                  'auth/email/confirm', user=user, token=token)
        flash('一封确认邮件已经被发送至您的电子邮箱')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


# 确认邮箱
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('您已经成功地确认了您的账户！谢谢')
    else:
        flash('您的确认链接已经失效或者过期')
    return redirect(url_for('main.index'))


# 重新发送确认邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '确认您的账户',
               'auth/email/confirm', user=current_user, token=token)
    flash('一封新的确认邮件已经发送到您的邮箱')
    return redirect(url_for('main.index'))


# 更换密码
@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('您已经成功更改您的密码')
            return redirect(url_for('main.index'))
        else:
            flash('新密码不符合规则，请重新设置')
    return render_template("auth/change_password.html", form=form)


# 重置密码--请求
@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, '重置你的密码',
                       'auth/email/reset_password',
                       user=user, token=token)
        flash('一封重置邮件已经被发送到您的邮箱')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


# 重置密码
@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('您已经更改您的密码')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


# 更换邮箱--请求
@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, '确认您的邮箱地址', 'auth/email/change_email',
                       user=current_user, token=token)
            flash('更改邮箱地址的确认邮件已经被发送至您的邮箱')
            return redirect(url_for('main.index'))
        else:
            flash('邮箱地址无效或者密码错误')
    return render_template("auth/change_email.html", form=form)


# 更换油箱
@auth.route('change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('您的邮箱地址已经更新')
    else:
        flash('无效请求')
    return redirect(url_for('main.index'))

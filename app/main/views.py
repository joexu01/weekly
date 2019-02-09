from flask import render_template, abort, redirect, url_for, flash, request, current_app
from . import main
from .. import db, user_img
from .forms import EditProfileForm, AddUserForm
from ..models import User, Role, Group
from flask_login import login_required, current_user
from ..assist_func import random_string
from ..decorators import admin_required
from ..email import send_email
import os


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/user/<stu_id>')
def user(stu_id):
    user = User.query.filter_by(stu_id=stu_id).first_or_404()
    return render_template('user.html', user=user, user_img=user_img)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        if form.avatar.data:
            suffix = os.path.splitext(form.avatar.data.filename)[1]
            filename = random_string() + suffix  # 用随机文件名替换原有文件名
            user_img.save(form.avatar.data, name=filename)  # 保存图片
            current_user.avatar = filename
        current_user.stu_id = form.stu_id.data
        current_user.birthday = form.birthday.data
        current_user.phone = form.phone.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('您的个人资料已经更新')
        return redirect(url_for('.user', stu_id=current_user.stu_id))
    form.name.data = current_user.name
    form.stu_id.data = current_user.stu_id
    form.birthday.data = current_user.birthday
    form.phone.data = current_user.phone
    return render_template('edit_profile.html', form=form, user_img=user_img)


@main.route('/user_admin', methods=['GET', 'POST'])
@login_required
@admin_required
def user_admin():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.paginate(
        page, per_page=current_app.config['WEEKLY_USER_PER_PAGE'],
        error_out=False)
    users = [{'name': item.name, 'email': item.email, 'stu_id': item.stu_id, 'phone': item.phone,
              'avatar': item.avatar, 'birthday':item.birthday}
             for item in pagination.items]
    return render_template('user_admin.html', users=users, user_img=user_img,
                           pagination=pagination, endpoint='.user_admin')


@main.route('/user_admin/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = AddUserForm()
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
        flash('一封确认邮件已经被发送至新建用户的电子邮箱')
        return redirect(url_for('.user_admin'))
    return render_template('add_user.html', form=form)


@main.route('/user_admin/delete/<stu_id>')
@login_required
@admin_required
def delete_user(stu_id):
    user = User.query.filter_by(stu_id=stu_id).first()
    if user is None:
        flash('找不到用户')
        return redirect(url_for('.user_admin'))
    if user == current_user:
        flash('别删除自己')
        return redirect(url_for('.user_admin'))
    user.delete()
    flash('用户已删除')
    return redirect(url_for('.user_admin'))


# @main.route('/group_admin', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def group_admin():
#     page = request.args.get('page', 1, type=int)
#     pagination = Group.query.paginate(
#         page, per_page=current_app.config['WEEKLY_GROUP_PER_PAGE'],
#         error_out=False)
#     users = [{'group_name': item.group_name, 'leader': item.group_leader, 'stu_id': item.stu_id, 'phone': item.phone,
#               'avatar': item.avatar, 'birthday': item.birthday}
#              for item in pagination.items]
#     return render_template('user_admin.html', users=users, user_img=user_img,
#                            pagination=pagination, endpoint='.user_admin')
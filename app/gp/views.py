from flask import render_template, abort, redirect, url_for, flash, request, current_app
from . import gp
from .. import db, user_img
from .forms import AddGroupForm, EditGroupForm
from ..models import User, Role, Group, Permission
from flask_login import login_required, current_user
from ..assist_func import random_string
from ..decorators import admin_required


@gp.route('/group_admin/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_group():
    form = AddGroupForm()
    if form.validate_on_submit():
        group = Group(group_name=form.group_name.data,
                      group_leader=form.group_leader.data)
        db.session.add(group)
        db.session.commit()
        flash('添加组操作成功')
        return redirect(url_for('gp.group_admin'))
    return render_template('gp/add_group.html', form=form)


@gp.route('/group_admin', methods=['GET', 'POST'])
@login_required
@admin_required
def group_admin():
    page = request.args.get('page', 1, type=int)
    pagination = Group.query.paginate(
        page, per_page=current_app.config['WEEKLY_GROUP_PER_PAGE'],
        error_out=False)
    groups = [{'group_name': item.group_name, 'leader': item.leader.name,
               'introduction': item.introduction, 'amount': item.weekly.count(),
               'group_id': item.id}
              for item in pagination.items]
    return render_template('gp/group_admin.html', groups=groups,
                           pagination=pagination, endpoint='gp.group_admin')


@gp.route('/group/<group_name>', methods=['GET', 'POST'])
@login_required
def view_group(group_name):
    group = Group.query.filter_by(group_name=group_name).first_or_404()
    return render_template("gp/view_group.html", group=group)


@gp.route('/group_admin/delete/<group_id>')
@login_required
@admin_required
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id).first()
    if group is None:
        flash('找不到组')
        return redirect(url_for('gp.group_admin'))
    group.delete()
    return redirect(url_for('gp.group_admin'))


@gp.route('/edit_group/<group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.filter_by(id=group_id).first()
    if current_user.id != group.group_leader and not current_user.can(Permission.ADMIN):
        abort(403)
    form = EditGroupForm(group)
    if form.validate_on_submit():
        group.group_name = form.group_name.data
        group.group_leader = form.group_leader.data
        group.introduction = form.introduction.data
        group.notice = form.notice.data
        db.session.add(group)
        db.session.commit()
        flash('组信息更新成功！')
        return redirect(url_for('gp.view_group', group_name=group.group_name))
    form.group_name.data = group.group_name
    form.group_leader.data = group.group_leader
    form.introduction.data = group.introduction
    form.notice.data = group.notice
    return render_template('gp/edit_group.html', form=form)

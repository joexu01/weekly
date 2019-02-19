from flask import render_template, abort, redirect, url_for, flash,\
    request, current_app, make_response
from . import gp
from .. import db, user_img
from .forms import AddGroupForm, EditGroupForm, SelectMembersForm
from ..models import User, Role, Group, Permission, Relation
from flask_login import login_required, current_user
from ..decorators import admin_required
from sqlalchemy import and_


# 添加组
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


# 组管理（限管理员）
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


# 查看组资料
@gp.route('/group/<group_name>', methods=['GET', 'POST'])
@login_required
def view_group(group_name):
    group = Group.query.filter_by(group_name=group_name).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = group.members.paginate(
        page, per_page=current_app.config['WEEKLY_USER_PER_PAGE'],
        error_out=False)
    members = [{'member': item.member}
               for item in pagination.items]
    return render_template("gp/view_group.html", group=group, members=members,
                           user_img=user_img, pagination=pagination,
                           endpoint='gp.view_group')


# 删除组
@gp.route('/group_admin/delete/<int:group_id>')
@login_required
@admin_required
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id).first()
    if group is None:
        flash('找不到组')
        return redirect(url_for('gp.group_admin'))
    group.delete()
    return redirect(url_for('gp.group_admin'))


# 编辑组资料
@gp.route('/edit_group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
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


# 添加成员
@gp.route('/edit_group/<int:group_id>/add_members', methods=['GET', 'POST'])
@login_required
def add_members(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    if current_user.id != group.group_leader and not current_user.can(Permission.ADMIN):
        abort(403)
    form = SelectMembersForm(group=group)
    if form.validate_on_submit():
        member_array = form.group_members.data
        for member in member_array:
            r = Relation(member_id=member, group_id=group_id)
            db.session.add(r)
        db.session.commit()
        flash('组员添加成功')
        return redirect(url_for('gp.view_group', group_name=group.group_name))
    return render_template("gp/add_members.html", form=form, group=group)


# 删除成员
@gp.route('/edit_group/<int:group_id>/delete_member/<int:member_id>')
@login_required
def delete_member(group_id, member_id):
    group = Group.query.filter_by(id=group_id).first()
    if group is None:
        flash('找不到组')
        return redirect(url_for('gp.view_group', group_name=group.group_name))
    if int(member_id) == group.group_leader:
        flash('不能删除组长，请更换组长后再从组中删除此用户')
        return redirect(url_for('gp.view_group', group_name=group.group_name))
    if current_user.id != group.group_leader and not current_user.can(Permission.ADMIN):
        abort(403)
    r = Relation.query.filter(and_(Relation.group_id == group_id, Relation.member_id == member_id)).first()
    if r is None:
        flash('组内没有此用户')
        return redirect(url_for('gp.view_group', group_name=group.group_name))
    r.delete()
    flash('组员已删除')
    return redirect(url_for('gp.view_group', group_name=group.group_name))


@gp.route('/my_groups', methods=['GET', 'POST'])
@login_required
def my_groups():
    page = request.args.get('page', 1, type=int)
    show_leader = False
    if current_user.is_authenticated:
        show_leader = bool(request.cookies.get('show_leader', ''))
    page = request.args.get('page', 1, type=int)
    if show_leader:
        pagination = Group.query.filter_by(group_leader=current_user.id).paginate(
            page, per_page=current_app.config['WEEKLY_GROUP_PER_PAGE'],
            error_out=False)
        groups = [{'group_name': item.group_name, 'leader': item.leader.name,
                   'introduction': item.introduction, 'amount': item.weekly.count(),
                   'group_id': item.id}
                  for item in pagination.items]
    else:
        pagination = current_user.groups.paginate(
            page, per_page=current_app.config['WEEKLY_GROUP_PER_PAGE'],
            error_out=False)
        groups = [{'group_name': item.group.group_name, 'leader': item.group.leader.name,
                   'introduction': item.group.introduction, 'amount': item.group.weekly.count(),
                   'group_id': item.group.id}
                  for item in pagination.items]
    return render_template('gp/my_groups.html', groups=groups,
                           pagination=pagination, show_leader=show_leader,
                           endpoint='gp.my_groups')


@gp.route('/my_groups/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('gp.my_groups')))
    resp.set_cookie('show_leader', '', max_age=30*24*60*60)
    return resp


@gp.route('/my_groups/leader')
@login_required
def show_leader():
    resp = make_response(redirect(url_for('gp.my_groups')))
    resp.set_cookie('show_leader', '1', max_age=30*24*60*60)
    return resp

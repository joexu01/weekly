from datetime import datetime

from flask import render_template, abort, redirect, url_for, flash,\
    request, current_app, make_response

from flask_login import login_required, current_user

from . import ms
from .forms import SelectGroupForm, NewMissionForm, SelectWeeklyForm

from .. import db
from ..models import Group, Mission

# 该文件中传入render_template 的参数、列表解释：
# pagination--分页，供"_macros.html" 中的pagination_widget 使用
# users 成员列表，（成员的集合，每一个成员对象的属性见weekly/models.py  class User）
# user_img 用户头像集的实例，使用方法：user_img.url( filename ) ，返回头像的url，参考模板中的用法
# endpoint pagination_widget（分页插件） 的参数  详见 "app/templates/_macros.html"
# form 表单实例
# as_leader cookie，bool 类型，if true --  只显示自己作为组长的组， if false --  显示加入的全部组
# missions 任务列表，（任务的集合，每一个成员对象的属性见weekly/models.py  class Mission）


@ms.route('/my_missions', methods=['GET', 'POST'])
@login_required
def my_missions():
    as_leader = False
    if current_user.is_authenticated:
        as_leader = bool(request.cookies.get('as_leader', ''))
    page = request.args.get('page', 1, type=int)
    if as_leader:
        pagination = current_user.assigned_missions.order_by(Mission.timestamp.desc()).paginate(
            page, per_page=current_app.config['WEEKLY_MISSION_PER_PAGE'],
            error_out=False)
    else:
        pagination = current_user.missions.order_by(Mission.timestamp.desc()).paginate(
            page, per_page=current_app.config['WEEKLY_MISSION_PER_PAGE'],
            error_out=False)
    missions = pagination.items
    return render_template("ms/my_missions.html", pagination=pagination, missions=missions,
                           as_leader=as_leader, endpoint='ms.my_missions')


@ms.route('/my_missions/as_member')
@login_required
def as_member():
    resp = make_response(redirect(url_for('ms.my_missions')))
    resp.set_cookie('as_leader', '', max_age=30*24*60*60)
    return resp


@ms.route('/my_missions/as_leader')
@login_required
def as_leader():
    resp = make_response(redirect(url_for('ms.my_missions')))
    resp.set_cookie('as_leader', '1', max_age=30*24*60*60)
    return resp


@ms.route('/new_mission/select_group', methods=['GET', 'POST'])
@login_required
def new_mission_select_group():
    form = SelectGroupForm()
    if form.validate_on_submit():
        resp = make_response(redirect(url_for('ms.new_mission_select_member')))
        resp.set_cookie('group_id', str(form.group.data), max_age=60*60)
        return resp
    return render_template("ms/new_mission.html", form=form)


@ms.route('/new_mission/select_member', methods=['GET', 'POST'])
@login_required
def new_mission_select_member():
    group_id = int(request.cookies.get('group_id', ''))
    group = Group.query.filter_by(id=group_id).first()
    if current_user.id != group.group_leader:
        abort(403)
    form = NewMissionForm(group)
    if form.validate_on_submit():
        deadline_str = form.year.data + '-' + form.month.data + '-' + form.day.data + ' ' +\
                       form.hour.data + ':' + form.minute.data + ':00'
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
        mission = Mission(title=form.title.data, detail=form.detail.data,
                          group_id=group_id, assign_person_id=current_user.id,
                          user_id=form.user.data, deadline=deadline)
        db.session.add(mission)
        db.session.commit()
        return redirect(url_for('ms.my_missions'))
    return render_template("ms/new_mission.html", form=form)


@ms.route('/<mission_id>', methods=['GET', 'POST'])
@login_required
def view_mission(mission_id):
    mission = Mission.query.get_or_404(int(mission_id))
    if current_user.id != mission.user_id and current_user.id != mission.assign_person_id:
        abort(403)
    if mission.user_id == current_user.id and not mission.is_known:
        mission.is_known = True
        db.session.add(mission)
        db.session.commit()
    form = SelectWeeklyForm(user=current_user._get_current_object(), group_id=mission.group_id)
    if form.validate_on_submit():
        mission.weekly_id = form.weekly.data
        mission.is_accomplished = True
        db.session.add(mission)
        db.session.commit()
        flash('提交成功')
        return redirect(url_for('ms.my_missions'))
    return render_template("ms/view_mission.html", mission=mission, form=form)


@ms.route('/terminate/<mission_id>')
@login_required
def terminate(mission_id):
    mission = Mission.query.get_or_404(int(mission_id))
    if current_user.id != mission.assign_person_id:
        abort(403)
    mission.is_terminated = True
    db.session.add(mission)
    db.session.commit()
    return redirect(url_for('ms.my_missions'))

import os

from sqlalchemy import and_

from flask import render_template, abort, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user

from . import wk
from .forms import WeeklyForm, CommentForm

from .. import db, user_img, wk_attachments
from ..models import Permission, Relation, Weekly, Comment
from ..assist_func import random_string

# 该文件中传入render_template 的参数、列表解释：
# pagination--分页，供"_macros.html" 中的 pagination_widget 使用
# comments 评论列表，（评论的集合，每一个成员对象的属性见weekly/models.py  class Comment）
# weekly 周报实例  具体属性见weekly/models.py  class Weekly
# user_img 用户头像集的实例，使用方法：user_img.url( filename ) ，返回头像的url，参考模板中的用法
# wk_attachments 周报附件集的实例，使用方法同上，参考模板中用法
# endpoint pagination_widget（分页插件） 的参数  详见 "app/templates/_macros.html"
# form 表单实例
# missions 任务列表，（任务的集合，每一个成员对象的属性见weekly/models.py  class Mission）


@wk.route('/<group_id>/new_weekly', methods=['GET', 'POST'])
@login_required
def new_weekly(group_id):
    relation = Relation.query.filter(and_(Relation.group_id == group_id,
                                          Relation.member_id == current_user.id)).first()
    if relation is None:
        abort(403)
    form = WeeklyForm()
    form.visible.data = True
    form.commentable.data = True
    if form.validate_on_submit():
        weekly = Weekly(group_id=int(group_id), author_id=current_user.id)
        weekly.subject = form.subject.data
        weekly.finished_work = form.finished_work.data
        weekly.summary = form.summary.data
        weekly.demands = form.demands.data
        weekly.plan = form.plan.data
        weekly.remarks = form.remarks.data
        weekly.visible = form.visible.data
        weekly.commentable = form.commentable.data
        if form.attachment.data:
            suffix = os.path.splitext(form.attachment.data.filename)[1]
            filename = 'file_' + random_string() + suffix
            wk_attachments.save(form.attachment.data, name=filename)
            if weekly.attachment is not None and weekly.attachment != filename:
                os.remove(current_app.config['UPLOADED_ATTACHMENTS_DEST'] + '/'
                          + weekly.attachment)
            weekly.attachment = filename
        db.session.add(weekly)
        db.session.commit()
        return redirect(url_for('wk.view_weekly', weekly_id=weekly.id))
    return render_template("wk/edit_weekly.html", form=form)


@wk.route('/<int:weekly_id>', methods=['GET', 'POST'])
@login_required
def view_weekly(weekly_id):
    weekly = Weekly.query.filter_by(id=weekly_id).first_or_404()
    if not weekly.visible:
        if not current_user.is_in_group(weekly.group):
            flash('该周报仅组内可见')
            return redirect(url_for('gp.view_group', group_name=weekly.group.group_name))
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          author=current_user._get_current_object(),
                          weekly_id=weekly.id)
        db.session.add(comment)
        db.session.commit()
        flash('评论发表成功')
        return redirect(url_for('wk.view_weekly', weekly_id=weekly.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (weekly.comments.count() - 1) // \
            current_app.config['WEEKLY_COMMENT_PER_PAGE'] + 1
    pagination = weekly.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['WEEKLY_COMMENT_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template("wk/view_weekly.html", weekly=weekly, comments=comments, user_img=user_img,
                           wk_attachments=wk_attachments, form=form, pagination=pagination)


@wk.route('/edit/<int:weekly_id>', methods=['GET', 'POST'])
@login_required
def edit_weekly(weekly_id):
    weekly = Weekly.query.filter_by(id=int(weekly_id)).first_or_404()
    if weekly.author != current_user and not current_user.can(Permission.ADMIN):
        flash('您没有编辑周报的权限')
        return redirect(url_for('wk.view_weekly', weekly_id=weekly.id))
    form = WeeklyForm()
    if form.validate_on_submit():
        weekly.subject = form.subject.data
        weekly.finished_work = form.finished_work.data
        weekly.summary = form.summary.data
        weekly.demands = form.demands.data
        weekly.plan = form.plan.data
        weekly.remarks = form.remarks.data
        weekly.visible = form.visible.data
        weekly.commentable = form.commentable.data
        if form.attachment.data:
            suffix = os.path.splitext(form.attachment.data.filename)[1]
            filename = 'file_' + random_string() + suffix
            wk_attachments.save(form.attachment.data, name=filename)
            if weekly.attachment is not None and weekly.attachment != filename:
                os.remove(current_app.config['UPLOADED_ATTACHMENTS_DEST'] + '/'
                          + weekly.attachment)
            weekly.attachment = filename
        weekly.ping()
        db.session.add(weekly)
        db.session.commit()
        flash('周报发布成功')
        return redirect(url_for('wk.view_weekly', weekly_id=weekly.id))
    form.subject.data = weekly.subject
    form.finished_work.data = weekly.finished_work
    form.summary.data = weekly.summary
    form.demands.data = weekly.demands
    form.plan.data = weekly.plan
    form.remarks.data = weekly.remarks
    form.visible.data = weekly.visible
    form.commentable.data = weekly.commentable
    return render_template("wk/edit_weekly.html", form=form)


@wk.route('/delete/<int:weekly_id>')
@login_required
def delete_weekly(weekly_id):
    weekly = Weekly.query.filter_by(id=int(weekly_id)).first_or_404()
    group_name = weekly.group.group_name
    if current_user != weekly.group.leader and not current_user.can(Permission.ADMIN):
        abort(403)
    for c in weekly.comments:
        db.session.delete(c)
        db.session.commit()
    db.session.delete(weekly)
    db.session.commit()
    return redirect(url_for('gp.view_group', group_name=group_name))

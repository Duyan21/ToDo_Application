from flask import Blueprint, request, jsonify, session, render_template
from src.database.models import db, Task
from src.utils.decorators.check_execution_time import check_execution_time
from datetime import datetime

task_bp = Blueprint('task', __name__, url_prefix='')

@task_bp.route('/tasks', methods=['GET'])
@check_execution_time
def get_tasks():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Bạn cần đăng nhập"}), 401

    tasks = Task.query.filter_by(user_id=user_id).all()
    return render_template('tasks.html', tasks=tasks)


@task_bp.route('/api/tasks', methods=['POST'])
@check_execution_time
def create_task():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Bạn cần đăng nhập"}), 401

    data = request.get_json()
    new_task = Task(
        user_id=user_id,
        title=data.get('title'),
        description=data.get('description'),
        deadline=datetime.strptime(data['deadline'], '%Y-%m-%d') if data.get('deadline') else None,
        priority=data.get('priority', 'medium'),
        status='pending',
        reminder_minutes=int(data.get('reminder_minutes', 0))
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"message": "Tạo task thành công!"}), 201


@task_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
@check_execution_time
def edit_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Bạn cần đăng nhập"}), 401

    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    data = request.get_json()
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.priority = data.get('priority', task.priority)
    task.reminder_minutes = int(data.get('reminder_minutes', task.reminder_minutes))
    if data.get('deadline'):
        task.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
    db.session.commit()
    return jsonify({"message": "Cập nhật task thành công!"}), 200


@task_bp.route('/api/tasks/<int:task_id>/complete', methods=['PUT'])
@check_execution_time
def complete_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Bạn cần đăng nhập"}), 401

    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    task.is_done = True
    task.status = 'completed'
    db.session.commit()
    return jsonify({"message": "Hoàn thành task!"}), 200


@task_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@check_execution_time
def delete_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Bạn cần đăng nhập"}), 401

    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Xóa task thành công!"}), 200
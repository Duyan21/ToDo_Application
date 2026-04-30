from flask import Blueprint, request, jsonify, session, render_template
from src.database.models import db, Task
from datetime import datetime, timezone


from src.utils.decorators.require_auth import require_auth
from src.utils.decorators.validate_input import validate_input
from src.utils.decorators.check_execution_time import check_execution_time

task_bp = Blueprint('task', __name__, url_prefix='')

@task_bp.route('/tasks', methods=['GET'])
@require_auth 
@check_execution_time 
def get_tasks():
    user_id = session.get('user_id')
    tasks = Task.query.filter_by(user_id=user_id).all()
    return render_template('tasks.html', tasks=tasks)

@task_bp.route('/tasks', methods=['POST'])
@require_auth
@validate_input(
    required_fields=['title'],
    field_types={'title': str, 'reminder_minutes': int},
    enum_fields={'priority': ['low', 'medium', 'high']}
) 
def create_task():
    user_id = session.get('user_id')
    data = request.get_json()
    
    new_task = Task(
        user_id=user_id,
        title=data['title'],
        description=data.get('description'),
        deadline=datetime.strptime(data['deadline'], '%Y-%m-%d') if data.get('deadline') else None,
        priority=data.get('priority', 'medium'),
        status='pending',
        reminder_minutes=data.get('reminder_minutes', 0)
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"message": "Tạo task thành công!"}), 201

@task_bp.route('/tasks/<int:task_id>/edit', methods=['PUT'])
@require_auth
def edit_task(task_id):
    user_id = session.get('user_id')
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    data = request.get_json()
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.priority = data.get('priority', task.priority)
    task.reminder_minutes = data.get('reminder_minutes', task.reminder_minutes)
    if data.get('deadline'):
        task.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
    
    db.session.commit()
    return jsonify({"message": "Cập nhật task thành công!"}), 200

@task_bp.route('/tasks/<int:task_id>/complete', methods=['PUT']) 
@require_auth
def complete_task(task_id):
    user_id = session.get('user_id')
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    task.is_done = True
    task.status = 'completed'
    db.session.commit()
    return jsonify({"message": "Hoàn thành task!"}), 200

@task_bp.route('/tasks/<int:task_id>/delete', methods=['DELETE'])
@require_auth
def delete_task(task_id):
    user_id = session.get('user_id')
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Xóa task thành công!"}), 200
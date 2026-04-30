from flask import Blueprint, request, jsonify, session, render_template
from src.database.models import db, Task, Notification
from datetime import datetime, timezone
from src.dto.task_dto import TaskDTO, TaskCreateDTO, TaskUpdateDTO

from src.utils.decorators.require_auth import require_auth
from src.utils.decorators.validate_input import validate_input
from src.utils.decorators.check_execution_time import check_execution_time

task_bp = Blueprint('task', __name__, url_prefix='')

@task_bp.route('/tasks', methods=['GET'])
@require_auth 
@check_execution_time 
def get_tasks():
    user_id = session.get('user_id')
    filter_type = request.args.get('filter', 'all')
    
    query = Task.query.filter_by(user_id=user_id)
    
    if filter_type == 'completed':
        query = query.filter_by(is_done=True)
    elif filter_type == 'pending':
        query = query.filter_by(is_done=False, status='pending')
    elif filter_type == 'overdue':
        query = query.filter(Task.is_done == False, Task.deadline < datetime.now())
    
    tasks = query.all()
    return render_template('tasks.html', tasks=tasks, current_filter=filter_type)

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
    
    # Create TaskCreateDTO from request data
    task_create_dto = TaskCreateDTO(
        title=data['title'],
        description=data.get('description'),
        deadline=data.get('deadline'),
        priority=data.get('priority', 'medium'),
        reminder_minutes=data.get('reminder_minutes', 0)
    )
    
    # Create Task model from DTO
    new_task = Task(
        user_id=user_id,
        title=task_create_dto.title,
        description=task_create_dto.description,
        deadline=datetime.strptime(task_create_dto.deadline, '%Y-%m-%dT%H:%M') if task_create_dto.deadline else None,
        priority=task_create_dto.priority,
        status='pending',
        reminder_minutes=task_create_dto.reminder_minutes
    )
    db.session.add(new_task)
    db.session.commit()
    
    # Return TaskDTO response
    task_dto = TaskDTO.from_model(new_task)
    return jsonify({
        "message": "Tạo task thành công!",
        "task": task_dto.to_dict()
    }), 201

@task_bp.route('/tasks/<int:task_id>/edit', methods=['PUT'])
@require_auth
def edit_task(task_id):
    user_id = session.get('user_id')
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    data = request.get_json()
    
    # Create TaskUpdateDTO from request data
    task_update_dto = TaskUpdateDTO(
        title=data.get('title'),
        description=data.get('description'),
        deadline=data.get('deadline'),
        priority=data.get('priority'),
        reminder_minutes=data.get('reminder_minutes')
    )
    
    # Update task model from DTO
    if task_update_dto.title:
        task.title = task_update_dto.title
    if task_update_dto.description is not None:
        task.description = task_update_dto.description
    if task_update_dto.priority:
        task.priority = task_update_dto.priority
    if task_update_dto.reminder_minutes is not None:
        task.reminder_minutes = task_update_dto.reminder_minutes
    if task_update_dto.deadline:
        task.deadline = datetime.strptime(task_update_dto.deadline, '%Y-%m-%dT%H:%M')
    
    db.session.commit()
    print(f"[{datetime.now()}] Task {task_id} updated. Background job will sync notifications in 3 seconds.")
    
    # Return TaskDTO response
    task_dto = TaskDTO.from_model(task)
    return jsonify({
        "message": "Cập nhật task thành công!",
        "task": task_dto.to_dict()
    }), 200

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
    print(f"[{datetime.now()}] Task {task_id} completed. Background job will clean notifications in 3 seconds.")
    
    task_dto = TaskDTO.from_model(task)
    return jsonify({
        "message": "Hoàn thành task!",
        "task": task_dto.to_dict()
    }), 200

@task_bp.route('/tasks/<int:task_id>/uncomplete', methods=['PUT']) 
@require_auth
def uncomplete_task(task_id):
    user_id = session.get('user_id')
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    task.is_done = False
    task.status = 'pending'
    db.session.commit()
    
    task_dto = TaskDTO.from_model(task)
    return jsonify({
        "message": "Chuyển task sang đang làm!",
        "task": task_dto.to_dict()
    }), 200

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

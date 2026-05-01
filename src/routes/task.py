import csv
from importlib.resources import files

from flask import Blueprint, request, jsonify, session, render_template, send_file, redirect, flash
from src.database.models import db, Task, Notification, File
from datetime import datetime, timezone
from src.dto.task_dto import TaskDTO, TaskCreateDTO, TaskUpdateDTO
from werkzeug.utils import secure_filename
import os

from src.utils.decorators.require_auth import require_auth
from src.utils.decorators.validate_input import validate_input
from src.utils.decorators.check_execution_time import check_execution_time
from src.utils.generators.read_csv import read_tasks_from_csv

task_bp = Blueprint('task', __name__, url_prefix='')

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@task_bp.route('/tasks/import', methods=['GET'])
@require_auth 
@check_execution_time 
def import_list():
    user_id = session.get('user_id')
    filter_type = request.args.get('filter', 'all')

    query = File.query.filter_by(user_id=user_id)
    if filter_type == 'pending':
        query = query.filter(File.is_imported == False)
    elif filter_type == 'imported':
        query = query.filter(File.is_imported == True)

    files = query.all()
    return render_template('tasks_import.html', current_filter=filter_type, files=files)

@task_bp.route('/tasks/import/download-sample', methods=['GET'])
@require_auth 
@check_execution_time 
def download_sample():
    sample_file = os.path.join(os.path.dirname(__file__), '..', 'static', 'sample', 'sample.csv')
    sample_file = os.path.abspath(sample_file)
    if not os.path.exists(sample_file):
        return jsonify({"error": "Sample file not found."}), 404

    return send_file(
        sample_file,
        mimetype='text/csv',
        as_attachment=True,
        download_name='sample_tasks.csv'
    )

@task_bp.route('/tasks/upload', methods=['POST'])
@require_auth 
@check_execution_time 
def upload_file():
    user_id = session.get('user_id')
    if 'file' not in request.files:
        flash('Vui lòng chọn file CSV để tải lên.', 'error')
        return redirect('/tasks/import')

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        flash('Vui lòng chọn file CSV để tải lên.', 'error')
        return redirect('/tasks/import')

    if not allowed_file(uploaded_file.filename):
        flash('Chỉ hỗ trợ file CSV.', 'error')
        return redirect('/tasks/import')

    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    upload_folder = os.path.join(workspace_root, 'upload')
    os.makedirs(upload_folder, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(uploaded_file.filename)
    saved_filename = f"{timestamp}_{filename}"
    save_path = os.path.join(upload_folder, saved_filename)
    uploaded_file.save(save_path)

    file_record = File(
        user_id=user_id,
        filename=filename,
        file_path=os.path.relpath(save_path, workspace_root),
        is_imported=False
    )
    db.session.add(file_record)
    db.session.commit()

    flash(f'Tải lên file thành công: {filename}', 'success')
    return redirect('/tasks/import')

@task_bp.route('/tasks/import-run/<int:file_id>', methods=['POST'])
@require_auth 
@check_execution_time 
def import_run(file_id):
    # read file record, if status is pending, read file and import tasks, update status to imported
    user_id = session.get('user_id')
    file_record = File.query.filter_by(id=file_id, user_id=user_id).first()
    if not file_record:
        return jsonify({"error": "Không tìm thấy file."}), 404
    if file_record.is_imported:
        return jsonify({"error": "File đã được nhập trước đó."}), 400
    file_path = os.path.join(os.path.dirname(__file__), '..', '..', file_record.file_path)
    if not os.path.exists(file_path):
        return jsonify({"error": "File không tồn tại trên server."}), 404
    # read file and import tasks
    try:
        for parts in read_tasks_from_csv(file_path):
            if len(parts) < 1:
                continue

            title = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ''
            deadline_str = parts[2].strip() if len(parts) > 2 else ''
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S') if deadline_str else None
            priority = parts[3].strip() if len(parts) > 3 else 'medium'
            reminder_minutes = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0

            new_task = Task(
                user_id=user_id,
                title=title,
                description=description,
                deadline=deadline,
                priority=priority,
                status='pending',
                reminder_minutes=reminder_minutes
            )
            db.session.add(new_task)

        db.session.commit()

        file_record.is_imported = True
        db.session.commit()

        return jsonify({"message": "Nhập tasks thành công!"}), 200
    except Exception as e:
        return jsonify({"error": f"Lỗi khi nhập tasks: {str(e)}"}), 500

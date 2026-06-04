import logging
import os
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    render_template,
    send_file,
    redirect,
    flash,
)
from src.services.task_service import TaskService
from src.services.file_service import FileService
from src.dto.task_dto import TaskDTO, TaskCreateDTO, TaskUpdateDTO
from src.utils.decorators.require_auth import require_auth
from src.utils.decorators.validate_input import validate_input
from src.utils.decorators.check_execution_time import check_execution_time

logger = logging.getLogger(__name__)


task_bp = Blueprint("task", __name__, url_prefix="")


@task_bp.route("/tasks", methods=["GET"])
@require_auth
@check_execution_time
def get_tasks():
    user_id = session.get("user_id")
    filter_type = request.args.get("filter", "all")

    tasks = TaskService.get_tasks_for_user(user_id, filter_type)
    return render_template("tasks.html", tasks=tasks, current_filter=filter_type)


@task_bp.route("/tasks", methods=["POST"])
@require_auth
@validate_input(
    required_fields=["title"],
    field_types={"title": str, "reminder_minutes": int},
    enum_fields={"priority": ["low", "medium", "high"]},
)
def create_task():
    user_id = session.get("user_id")
    data = request.get_json()

    # Create TaskCreateDTO from request data
    task_create_dto = TaskCreateDTO(
        title=data["title"],
        description=data.get("description"),
        deadline=data.get("deadline"),
        priority=data.get("priority", "medium"),
        reminder_minutes=data.get("reminder_minutes", 0),
    )
    new_task = TaskService.create_task(user_id, task_create_dto)

    # Return TaskDTO response
    task_dto = TaskDTO.from_model(new_task)
    return jsonify({"message": "Tạo task thành công!", "task": task_dto.to_dict()}), 201


@task_bp.route("/tasks/<int:task_id>/edit", methods=["PUT"])
@require_auth
def edit_task(task_id):
    user_id = session.get("user_id")
    data = request.get_json()

    # Create TaskUpdateDTO from request data
    task_update_dto = TaskUpdateDTO(
        title=data.get("title"),
        description=data.get("description"),
        deadline=data.get("deadline"),
        priority=data.get("priority"),
        reminder_minutes=data.get("reminder_minutes"),
    )

    # Edit task through service
    task = TaskService.edit_task(user_id, task_id, task_update_dto)
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    # Return TaskDTO response
    task_dto = TaskDTO.from_model(task)
    return (
        jsonify({"message": "Cập nhật task thành công!", "task": task_dto.to_dict()}),
        200,
    )


@task_bp.route("/tasks/<int:task_id>/complete", methods=["PUT"])
@require_auth
def complete_task(task_id):
    user_id = session.get("user_id")
    task = TaskService.complete_task(user_id, task_id)
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    task_dto = TaskDTO.from_model(task)
    return jsonify({"message": "Hoàn thành task!", "task": task_dto.to_dict()}), 200


@task_bp.route("/tasks/<int:task_id>/uncomplete", methods=["PUT"])
@require_auth
def uncomplete_task(task_id):
    user_id = session.get("user_id")
    task = TaskService.uncomplete_task(user_id, task_id)
    if not task:
        return jsonify({"error": "Không tìm thấy task"}), 404

    task_dto = TaskDTO.from_model(task)
    return (
        jsonify({"message": "Chuyển task sang đang làm!", "task": task_dto.to_dict()}),
        200,
    )


@task_bp.route("/tasks/<int:task_id>/delete", methods=["DELETE"])
@require_auth
def delete_task(task_id):
    user_id = session.get("user_id")
    deleted = TaskService.delete_task(user_id, task_id)
    if not deleted:
        return jsonify({"error": "Không tìm thấy task"}), 404

    return jsonify({"message": "Xóa task thành công!"}), 200


@task_bp.route("/tasks/import", methods=["GET"])
@require_auth
@check_execution_time
def import_list():
    user_id = session.get("user_id")
    filter_type = request.args.get("filter", "all")

    files = FileService.get_files_for_user(user_id, filter_type)
    return render_template("tasks_import.html", current_filter=filter_type, files=files)


@task_bp.route("/tasks/import/download-sample", methods=["GET"])
@require_auth
@check_execution_time
def download_sample():
    sample_file = os.path.join(
        os.path.dirname(__file__), "..", "static", "sample", "sample.csv"
    )
    sample_file = os.path.abspath(sample_file)
    if not os.path.exists(sample_file):
        return jsonify({"error": "Sample file not found."}), 404

    return send_file(
        sample_file,
        mimetype="text/csv",
        as_attachment=True,
        download_name="sample_tasks.csv",
    )


@task_bp.route("/tasks/upload", methods=["POST"])
@require_auth
@check_execution_time
def upload_file():
    user_id = session.get("user_id")

    if "file" not in request.files:
        flash("Vui lòng chọn file CSV để tải lên.", "error")
        return redirect("/tasks/import")

    uploaded_file = request.files["file"]

    workspace_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    file_record, message = FileService.upload_file(
        user_id, uploaded_file, workspace_root
    )

    if file_record:
        flash(message, "success")
    else:
        flash(message, "error")

    return redirect("/tasks/import")


@task_bp.route("/tasks/import-run/<int:file_id>", methods=["POST"])
@require_auth
@check_execution_time
def import_run(file_id):
    user_id = session.get("user_id")

    # Get workspace root and file path
    workspace_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    from src.repositories import get_file_repository

    file_repository = get_file_repository()
    file_record = file_repository.get_file_for_user(file_id, user_id)

    if not file_record:
        return jsonify({"error": "Không tìm thấy file."}), 404

    file_path = os.path.join(workspace_root, file_record.file_path)

    # Import tasks through service
    success, message = TaskService.import_tasks_from_csv(user_id, file_path, file_id)

    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400 if "đã được nhập" in message else 404

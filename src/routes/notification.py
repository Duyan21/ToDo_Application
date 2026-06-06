from flask import Blueprint, jsonify, session
from src.services.notification_service import NotificationService
from src.dto.notification_dto import NotificationDTO
from src.utils.decorators.require_auth import require_auth

noti_bp = Blueprint("noti", __name__, template_folder="../../templates")


# Get all notifications with priority sorting
@noti_bp.route("/notifications", methods=["GET"])
@require_auth
def get_notifications():
    user_id = session.get("user_id")

    # Get all notifications with priority sorting
    notifications = NotificationService.get_notifications_for_user(user_id)
    notification_dtos = [NotificationDTO.from_model(noti) for noti in notifications]

    return (
        jsonify(
            {
                "notifications": [dto.to_dict() for dto in notification_dtos],
                "unread_count": len([n for n in notifications if not n.is_read]),
            }
        ),
        200,
    )


# Mark notification as read
@noti_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@require_auth
def mark_notification_as_read(notification_id):
    user_id = session.get("user_id")

    success = NotificationService.mark_notification_as_read(notification_id, user_id)

    if not success:
        return jsonify({"error": "Không tìm thấy notification"}), 404

    return jsonify({"message": "Đã đánh dấu đã đọc"}), 200


# Mark all notifications as read
@noti_bp.route("/notifications/read-all", methods=["POST"])
@require_auth
def mark_all_notifications_as_read():
    user_id = session.get("user_id")

    NotificationService.mark_all_notifications_as_read(user_id)

    return jsonify({"message": "Đã đánh dấu tất cả là đã đọc"}), 200


# Clear all notifications
@noti_bp.route("/notifications/clear", methods=["POST"])
@require_auth
def clear_all_notifications():
    user_id = session.get("user_id")

    # Delete all notifications for this user
    deleted_count = NotificationService.clear_all_notifications(user_id)

    return jsonify({"message": f"Đã xóa {deleted_count} thông báo"}), 200

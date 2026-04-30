from flask import Blueprint, jsonify, session
from datetime import datetime, timedelta
from src.dto.notification_dto import NotificationDTO
from src.utils.decorators.require_auth import require_auth
from src.database.models import db, Task, Notification

noti_bp = Blueprint('noti', __name__, template_folder='../../templates')

# Get all notifications with priority sorting
@noti_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notifications():
    user_id = session.get('user_id')
    
    # Get all notifications with priority sorting
    notifications = Notification.query.filter_by(user_id=user_id).order_by(
        # Overdue first, then by created_at desc
        db.case(
            (Notification.type == 'OVERDUE', 1),
            (Notification.type == 'REMINDER', 2),
            else_=3
        ).asc(),
        Notification.created_at.desc()
    ).all()
    
    notification_dtos = [NotificationDTO.from_model(noti) for noti in notifications]
    
    return jsonify({
        "notifications": [dto.to_dict() for dto in notification_dtos],
        "unread_count": len([n for n in notifications if not n.is_read])
    }), 200

# Mark notification as read
@noti_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@require_auth
def mark_notification_as_read(notification_id):
    user_id = session.get('user_id')
    
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first()
    
    if not notification:
        return jsonify({"error": "Không tìm thấy notification"}), 404
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({"message": "Đã xóa notification"}), 200


# Mark all notifications as read
@noti_bp.route('/notifications/read-all', methods=['POST'])
@require_auth
def mark_all_notifications_as_read():
    user_id = session.get('user_id')
    
    notifications = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).all()
    
    for notification in notifications:
        notification.is_read = True
    
    db.session.commit()
    
    return jsonify({"message": "Đã đánh dấu tất cả là đã đọc"}), 200

# Clear all notifications
@noti_bp.route('/notifications/clear', methods=['POST'])
@require_auth
def clear_all_notifications():
    user_id = session.get('user_id')
    
    # Delete all notifications for this user
    deleted_count = Notification.query.filter_by(user_id=user_id).count()
    Notification.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return jsonify({"message": f"Đã xóa {deleted_count} thông báo"}), 200
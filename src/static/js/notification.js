$(document).ready(function () {
  
  // Notification functionality
  let notifications = [];
  let isDropdownOpen = false;

  // Toggle notification dropdown
  $("#notification-bell").click(function(e) {
    e.stopPropagation();
    isDropdownOpen = !isDropdownOpen;
    $("#notification-dropdown").toggleClass("active");
    
    if (isDropdownOpen) {
      loadNotifications();
    }
  });

  // Close dropdown when clicking outside
  $(document).click(function(e) {
    if (!$(e.target).closest(".notification-wrapper").length) {
      $("#notification-dropdown").removeClass("active");
      isDropdownOpen = false;
    }
  });

  // Load notifications
  function loadNotifications() {
    $.ajax({
      url: "/notifications",
      type: "GET",
      success: function (response) {
        notifications = response.notifications;
        updateNotificationBadge(response.unread_count);
        renderNotifications();
      },
      error: function (xhr) {
        console.error("Error loading notifications:", xhr);
      }
    });
  }

  // Update notification badge
  function updateNotificationBadge(count) {
    const badge = $("#notification-badge");
    if (count > 0) {
      badge.text(count > 99 ? "99+" : count);
      badge.show();
    } else {
      badge.hide();
    }
  }

  // Render notifications
  function renderNotifications() {
    const list = $("#notification-list");
    
    if (notifications.length === 0) {
      list.html('<div class="no-notifications">Không có thông báo</div>');
      return;
    }

    const html = notifications.map(noti => {
      const icon = noti.type === 'OVERDUE' ? '🚨' : '⏰';
      const typeClass = noti.type === 'OVERDUE' ? 'overdue' : 'reminder';
      const unreadClass = !noti.is_read ? 'unread' : '';
      const time = formatTime(noti.created_at);
      
      return `
        <div class="notification-item ${typeClass} ${unreadClass}" data-id="${noti.id}">
          <div class="notification-content">
            <div class="notification-icon">${icon}</div>
            <div class="notification-text">
              <div class="notification-message">${noti.message}</div>
              <div class="notification-time">${time}</div>
              ${!noti.is_read ? `
                <div class="notification-actions">
                  <button class="notification-action-btn mark-read" data-id="${noti.id}">Đánh dấu đã đọc</button>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');

    list.html(html);
  }

  // Format time
  function formatTime(timeString) {
    const date = new Date(timeString);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds

    if (diff < 60) return "Vừa xong";
    if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
    if (diff < 604800) return `${Math.floor(diff / 86400)} ngày trước`;
    
    return date.toLocaleDateString('vi-VN');
  }

  // Mark notification as read
  $(document).on("click", ".mark-read", function(e) {
    e.stopPropagation();
    const notificationId = $(this).data("id");
    
    // Add reading animation class
    const notificationElement = $(`.notification-item[data-id="${notificationId}"]`);
    notificationElement.addClass('reading');
    
    $.ajax({
      url: `/notifications/${notificationId}/read`,
      type: "POST",
      success: function (response) {
        showAutoAlert(response.message);
        
        // After successful API call, update the UI with animation
        setTimeout(() => {
          notificationElement.removeClass('reading unread').addClass('read');
          updateNotificationBadge();
        }, 500); // Match animation duration
      },
      error: function (xhr) {
        alert(xhr.responseJSON ? xhr.responseJSON.error : "Lỗi hệ thống");
        // Remove animation class on error
        notificationElement.removeClass('reading');
      }
    });
  });

  // Mark all notifications as read
  $("#mark-all-read").click(function(e) {
    e.stopPropagation();
    
    $.ajax({
      url: "/notifications/read-all",
      type: "POST",
      success: function (response) {
        loadNotifications();
      },
      error: function (xhr) {
        console.error("Error marking all as read:", xhr);
      }
    });
  });

  // Clear all notifications
  $("#clear-all").click(function(e) {
    e.stopPropagation();
    
    $.ajax({
      url: "/notifications/clear",
      type: "POST",
      success: function (response) {
        loadNotifications();
      },
      error: function (xhr) {
        console.error("Error clearing notifications:", xhr);
      }
    });
  });

  // Auto-refresh notifications every 30 seconds
  setInterval(function() {
    if (!isDropdownOpen) {
      loadNotifications();
    }
  }, 30000);

  
  // Initial load
  loadNotifications();

});

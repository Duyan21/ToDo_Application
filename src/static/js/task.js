$(document).ready(function () {
  
  // Auto-close alert function
  function showAutoAlert(message, duration = 2000) {
    $("#auto-alert-message").text(message);
    $("#auto-alert").removeClass("hide").addClass("show");
    
    setTimeout(function() {
      $("#auto-alert").removeClass("show").addClass("hide");
      setTimeout(function() {
        $("#auto-alert").removeClass("hide");
      }, 300);
    }, duration);
  }
  
  // Logout functionality
  $("#btn-logout").click(function () {
    $.ajax({
      url: "/api/logout",
      type: "POST",
      success: function (response) {
        showAutoAlert(response.message);
        setTimeout(function() {
          window.location.href = "/signin";
        }, 1000);
      },
      error: function (xhr) {
        alert(xhr.responseJSON ? xhr.responseJSON.error : "Lỗi hệ thống");
      }
    });
  });

  
  // Filter functionality
  $(".filter-btn").click(function () {
    var filterType = $(this).data("filter");
    
    // Update active button
    $(".filter-btn").removeClass("active");
    $(this).addClass("active");
    
    // Reload page with filter parameter
    window.location.href = "/tasks?filter=" + filterType;
  });

  // tạo task
  $("#btn-add-task").click(function () {
    $("#modal-title").text("Tạo task mới");
    $("#task-id").val("");
    // Reset form
    $("#input-title").val("");
    $("#input-description").val("");
    $("#input-deadline").val("");
    $("#input-priority").val("medium");
    $("#input-reminder").val(0);
    $("#modal-overlay").addClass("active");
  });

  // Đóng modal
  $("#btn-cancel").click(function () {
    $("#modal-overlay").removeClass("active");
  });

  // Lưu task 
  $("#btn-save").click(function () {
    var taskId = $("#task-id").val();
    var data = {
      title: $("#input-title").val(),
      description: $("#input-description").val(),
      deadline: $("#input-deadline").val(),
      priority: $("#input-priority").val(),
      reminder_minutes: parseInt($("#input-reminder").val()) || 0
    };

    
    var url = taskId ? "/tasks/" + taskId + "/edit" : "/tasks";
    var method = taskId ? "PUT" : "POST";

    $.ajax({
      url: url,
      type: method,
      contentType: "application/json",
      data: JSON.stringify(data),
      success: function (response) {
        showAutoAlert(response.message);
        setTimeout(function() {
          location.reload();
        }, 1500);
      },
      error: function (xhr) {
        alert(xhr.responseJSON ? xhr.responseJSON.error : "Lỗi hệ thống");
      }
    });
  });

  // Mở modal chỉnh sửa
  $(".btn-edit").click(function () {
    var card = $(this).closest(".task-card");
    $("#modal-title").text("Chỉnh sửa task");
    $("#task-id").val(card.data("id"));
    $("#input-title").val(card.data("title"));
    $("#input-description").val(card.data("description"));
    $("#input-deadline").val(card.data("deadline"));
    $("#input-priority").val(card.data("priority"));
    $("#input-reminder").val(card.data("reminder"));
    $("#modal-overlay").addClass("active");
  });

  // Hoàn thành task 
  $(document).on("click", ".btn-complete", function () {
    console.log("Complete button clicked");
    var taskId = $(this).closest(".task-card").data("id");
    console.log("Task ID:", taskId);
    $.ajax({
      url: "/tasks/" + taskId + "/complete",
      type: "PUT",
      success: function (response) {
        console.log("Complete success:", response);
        showAutoAlert(response.message);
        setTimeout(function() {
          location.reload();
        }, 1500);
      },
      error: function (xhr) {
        console.log("Complete error:", xhr);
        alert(xhr.responseJSON ? xhr.responseJSON.error : "Lỗi hệ thống");
      }
    });
  });

  // Chuyển task sang đang làm
  $(document).on("click", ".btn-uncomplete", function () {
    console.log("Uncomplete button clicked");
    var taskId = $(this).closest(".task-card").data("id");
    console.log("Task ID:", taskId);
    $.ajax({
      url: "/tasks/" + taskId + "/uncomplete",
      type: "PUT",
      success: function (response) {
        console.log("Uncomplete success:", response);
        showAutoAlert(response.message);
        setTimeout(function() {
          location.reload();
        }, 1500);
      },
      error: function (xhr) {
        console.log("Uncomplete error:", xhr);
        alert(xhr.responseJSON ? xhr.responseJSON.error : "Lỗi hệ thống");
      }
    });
  });

  // Xóa task
  $(".btn-delete").click(function () {
    if (!confirm("Bạn có chắc muốn xóa task này không?")) return;
    var taskId = $(this).closest(".task-card").data("id");
    $.ajax({
      url: "/tasks/" + taskId + "/delete",
      type: "DELETE",
      success: function (response) {
        showAutoAlert(response.message);
        setTimeout(function() {
          location.reload();
        }, 1500);
      },
      error: function (xhr) {
        alert(xhr.responseJSON ? xhr.responseJSON.error : "Lỗi hệ thống");
      }
    });
  });

  // khi click vào thì sẽ chuyển qua trang import task /tasks/import
  $("#btn-import-task").click(function (e) {
    window.location.href = "/tasks/import";
    e.preventDefault();
  });
});
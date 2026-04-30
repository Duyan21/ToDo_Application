$(document).ready(function () {

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
        alert(response.message);
        location.reload();
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
  $(".btn-complete").click(function () {
    var taskId = $(this).closest(".task-card").data("id");
    $.ajax({
      url: "/tasks/" + taskId + "/complete",
      type: "PUT",
      success: function (response) {
        alert(response.message);
        location.reload();
      }
    });
  });

  // Xóa task
  $(".btn-delete").click(function () {
    if (!confirm("Ní có chắc muốn xóa task này không?")) return;
    var taskId = $(this).closest(".task-card").data("id");
    $.ajax({
      url: "/tasks/" + taskId + "/delete",
      type: "DELETE",
      success: function (response) {
        alert(response.message);
        location.reload();
      }
    });
  });

});
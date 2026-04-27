$(document).ready(function () {
  $("#show-register").click(function (e) {
    window.location.href = "/register";
    e.preventDefault();
  });

  $("#show-login").click(function (e) {
    window.location.href = "/signin";
    e.preventDefault();
  });

  $("#register-form").submit(function (e) {
    e.preventDefault();
    $.ajax({
      url: "/api/register",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        name: $("#reg-name").val(),
        email: $("#reg-email").val(),
        password: $("#reg-password").val()
      }),
      success: function (response) {
        alert(response.message);
        window.location.href = "/signin";
        e.preventDefault();
      },
      error: function (xhr) {
        alert(xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'Đăng ký không thành công');
      }
    });
  });

  $("#login-form").submit(function (e) {
    e.preventDefault();
    $.ajax({
      url: "/api/signin",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        email: $("#login-email").val(),
        password: $("#login-password").val()
      }),
      success: function (response) {
        alert(response.message);
        window.location.href = "/tasks";
      },
      error: function (xhr) {
        alert(xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'Đăng nhập không thành công');
      }
    });
  });
});

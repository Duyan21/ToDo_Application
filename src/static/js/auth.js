const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function switchTab(tab) {
  const isSignin = tab === 'signin';
  $('#login-form').toggle(isSignin);
  $('#register-form').toggle(!isSignin);
  $('#footer-signin').toggle(isSignin);
  $('#footer-register').toggle(!isSignin);
  $('#tab-signin').toggleClass('active', isSignin);
  $('#tab-register').toggleClass('active', !isSignin);
  ['login-error', 'register-error',
   'login-email-error', 'login-password-error',
   'reg-name-error', 'reg-email-error', 'reg-password-error', 'reg-confirm-password-error'
  ].forEach(function(id) { clearError(id); });
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.style.display = 'block';
}

function clearError(elementId) {
  const el = document.getElementById(elementId);
  if (el) { el.textContent = ''; el.style.display = 'none'; }
}

function validateLogin() {
  let valid = true;
  const email = $('#login-email').val().trim();
  const password = $('#login-password').val();

  clearError('login-email-error');
  clearError('login-password-error');

  if (!email) {
    showError('login-email-error', 'Vui lòng nhập email');
    valid = false;
  } else if (!EMAIL_RE.test(email)) {
    showError('login-email-error', 'Email không đúng định dạng');
    valid = false;
  }

  if (!password) {
    showError('login-password-error', 'Vui lòng nhập mật khẩu');
    valid = false;
  }

  return valid;
}

function validateRegister() {
  let valid = true;
  const name = $('#reg-name').val().trim();
  const email = $('#reg-email').val().trim();
  const password = $('#reg-password').val();
  const confirm = $('#reg-confirm-password').val();

  clearError('reg-name-error');
  clearError('reg-email-error');
  clearError('reg-password-error');
  clearError('reg-confirm-password-error');

  if (!name) {
    showError('reg-name-error', 'Vui lòng nhập họ tên');
    valid = false;
  }

  if (!email) {
    showError('reg-email-error', 'Vui lòng nhập email');
    valid = false;
  } else if (!EMAIL_RE.test(email)) {
    showError('reg-email-error', 'Email không đúng định dạng');
    valid = false;
  }

  if (!password) {
    showError('reg-password-error', 'Vui lòng nhập mật khẩu');
    valid = false;
  } else if (password.length < 8) {
    showError('reg-password-error', 'Mật khẩu phải có ít nhất 8 ký tự');
    valid = false;
  }

  if (!confirm) {
    showError('reg-confirm-password-error', 'Vui lòng xác nhận mật khẩu');
    valid = false;
  } else if (password && confirm !== password) {
    showError('reg-confirm-password-error', 'Mật khẩu xác nhận không khớp');
    valid = false;
  }

  return valid;
}

$(document).ready(function () {
  if (new URLSearchParams(window.location.search).get('tab') === 'register') {
    switchTab('register');
  }

  $('#login-email').on('input', function () { clearError('login-email-error'); });
  $('#login-password').on('input', function () { clearError('login-password-error'); });
  $('#reg-name').on('input', function () { clearError('reg-name-error'); });
  $('#reg-email').on('input', function () { clearError('reg-email-error'); });
  $('#reg-password').on('input', function () { clearError('reg-password-error'); });
  $('#reg-confirm-password').on('input', function () { clearError('reg-confirm-password-error'); });

  $("#register-form").submit(function (e) {
    e.preventDefault();
    clearError('register-error');
    if (!validateRegister()) return;

    const btn = $(this).find('button[type="submit"]');
    btn.prop('disabled', true);
    $.ajax({
      url: "/api/register",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        name: $("#reg-name").val(),
        email: $("#reg-email").val(),
        password: $("#reg-password").val()
      }),
      success: function () {
        window.location.href = "/home";
      },
      error: function (xhr) {
        const msg = xhr.responseJSON && xhr.responseJSON.error
          ? xhr.responseJSON.error
          : 'Đăng ký không thành công';
        showError('register-error', msg);
        btn.prop('disabled', false);
      }
    });
  });

  $("#login-form").submit(function (e) {
    e.preventDefault();
    clearError('login-error');
    if (!validateLogin()) return;

    const btn = $(this).find('button[type="submit"]');
    btn.prop('disabled', true);
    $.ajax({
      url: "/api/signin",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        email: $("#login-email").val(),
        password: $("#login-password").val()
      }),
      success: function () {
        window.location.href = "/home";
      },
      error: function (xhr) {
        const msg = xhr.responseJSON && xhr.responseJSON.error
          ? xhr.responseJSON.error
          : 'Đăng nhập không thành công';
        showError('login-error', msg);
        btn.prop('disabled', false);
      }
    });
  });
});

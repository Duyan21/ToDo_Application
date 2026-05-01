$(document).ready(function () {
  // Handle file import button click
  window.importFile = function (fileId) {
    $.ajax({
      url: '/tasks/import-run/' + fileId,
      method: 'POST',
      success: function (response) {
        alert(response.message);
        location.reload(); // Refresh the page to update the file status
      },
      error: function (xhr) {
        alert('Error importing file: ' + xhr.responseJSON.message);
      }
    });
  };

  // Handle filter button click
  window.filterTasks = function (filter) {
    $('.filter-btn').removeClass('active');
    $('.filter-btn[data-filter="' + filter + '"]').addClass('active');
    window.location.href = '/tasks/import?filter=' + encodeURIComponent(filter);
  };
});
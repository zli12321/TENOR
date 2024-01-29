

// label.js

// Event listener for the "Proceed to task" button
function showConfirmationPopup() {
  // Display the confirmation dialog
  var confirmation = window.confirm("Are you sure you want to proceed to the study?");

  // If the user clicks 'OK' in the confirmation dialog (I agree), submit the form
  if (confirmation) {
    // Get the form element and submit it
    var form = document.getElementById('proceedForm');
    form.submit();
  }
  // If the user clicks 'Cancel' in the confirmation dialog (I disagree), do nothing
  else {
    // You can add any additional actions you want here or leave it empty
    // For example, you can show a different message or redirect somewhere else.
  }
}

    

// Get the "Finish" link element
const finishLink = document.getElementById('finish');

// Add an event listener to the link
finishLink.addEventListener('click', function(event) {
  // Prevent the link from redirecting immediately
  event.preventDefault();

  // Display the confirmation dialog
  const confirmation = confirm("Are you sure you want to finish? After you click 'OK', it will redirect you to the survey page");

  // If the user clicks "OK" in the confirmation dialog, redirect them to the "Finish" page
  if (confirmation) {
    window.location.href = finishLink.href;
  }
  // If the user clicks "Cancel" in the confirmation dialog, do nothing
  // The link will remain inactive
});
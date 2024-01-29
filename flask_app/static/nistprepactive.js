const select = document.querySelector(".suggestion");
const label = document.querySelector(".text_input");
const submitButton = document.getElementById("myBtn")

submitButton.disabled = true;

let selectValue = 0;
let labelValue = 0;

select.addEventListener("change", (e) => {
  selectValue = e.target.value.length;
  // console.log(selectValue.length)
  console.log(selectValue)
  checkButtonEnabled();
  // console.log(selectValue)
});

label.addEventListener("input", (e) => {
  labelContent = e.target.value.trim();
  labelValue = labelContent.length;
  console.log(labelValue)
  // console.log(labelValue.length)
  checkButtonEnabled();
});

// function checkButtonEnabled() {
//   if (selectValue && labelValue) {
//     submitButton.disabled = true;
//   } else if (selectValue || labelValue) {
//     submitButton.disabled = false;
//   }
// }
function checkButtonEnabled() {
  if ((selectValue != 0) && (labelValue === 0) || ((selectValue === 0) && (labelValue != 0))){
    submitButton.disabled = false;
  }
  else {
    submitButton.disabled = true;
  }


}


document.getElementById("extraBtn").addEventListener("click", function() {
  document.getElementById("myBtn").disabled = false; // Enable the "submit & next" button
  document.forms[0].submit(); // Submit the form
});

const skipButton = document.querySelector('#extraBtn');
skipButton.addEventListener('click', showLoader)

submitButton.addEventListener('click', showLoader)
const loader = document.querySelector('#loading')


function showLoader() {
  loader.style.display = 'block';
}

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
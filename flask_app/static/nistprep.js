let wordsToHighlight = [];
const acc = document.querySelectorAll(".right_topics");
// console.log(acc)
let specialChars = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/;


textElement = document.getElementById("text");
oritextElement = document.getElementById("original_text");
// console.log(textElement.innerText)
const original_text = oritextElement.innerText;
const viewButtons = document.querySelectorAll(".view");

// const REGEXP_SPECIAL_CHAR = /[\!\#\$\%\^\&\*\)\(\+\=\.\<\>\{\}\[\]\:\;\'\"\|\~\`\_\-]/g;
// const REGEXP_SPECIAL_CHAR = /[\&\*\)\(\+\=\.\<\>]/g;
const REGEXP_SPECIAL_CHAR = /[\<\>]/g;
num = 0;


// Highlight by default using first set of labels
const firstWordsEl = document.querySelector('#pred_key').querySelectorAll('span');

const firstWordsArr = [];
    Array.from(firstWordsEl).forEach(function (ele) {
      firstWordsArr.push(ele.innerText);
    });
highlighWords(firstWordsArr);

viewButtons.forEach((btn, index) => {
  btn.setAttribute("highlighted", "false");
  if (index == 0) {
    btn.setAttribute("highlighted", "true");
  }
  btn.addEventListener("click", function (event) {
    // removeAllActive()
    let topic_el =
      btn.parentElement.nextElementSibling.getElementsByTagName("span");

    const wordsArr = [];
    Array.from(topic_el).forEach(function (ele) {
      wordsArr.push(ele.innerText);
    });

    if (btn.getAttribute("highlighted") === "true") {
      textElement.innerHTML = original_text;
      btn.setAttribute("highlighted", "false");
    } else {
      highlighWords(wordsArr);
      btn.setAttribute("highlighted", "true");
    }


  });
});

// Manually set the first button to be "highlighted"

function highlighWords(words) {
  console.log(words);
  var text = original_text;
  words.forEach((word) => {
    console.log(specialChars.test(word))
    if (!specialChars.test(word) && word.length > 2) {
      const pattern = new RegExp(word, "g");
      text = text.replace(pattern, `<mark>${word}</mark>`);
      textElement.innerHTML = text;
      // console.log(textElement)
    }
  });
}

// Selectors
const select = document.querySelector(".suggestion");
const label = document.querySelector(".text_input");
const submitButton = document.getElementById("myBtn");
const skipButton = document.querySelector('#extraBtn');
const labelInput = document.querySelector("#written");
const labelSelection = document.querySelector("#labelSelection");
const loader = document.querySelector('#loading')

submitButton.disabled = true;

// Event Listeners
submitButton.addEventListener('click', showLoader)
skipButton.addEventListener('click', showLoader)

function showLoader() {
  loader.style.display = 'block';
}

let selectValue = 0;
let labelValue = 0;

select.addEventListener("change", (e) => {
  selectValue = e.target.value.length;
  // console.log(selectValue.length)
  // console.log(selectValue)
  checkButtonEnabled();
  // console.log(selectValue)
});

label.addEventListener("input", (e) => {
  labelContent = e.target.value.trim();
  labelValue = labelContent.length;
  // labelValue = e.target.value.length;
  // console.log(labelValue)
  // console.log(labelValue.length)
  checkButtonEnabled();
});

function checkButtonEnabled() {
  if (
    (selectValue != 0 && labelValue === 0) ||
    (selectValue === 0 && labelValue != 0)
  ) {
    submitButton.disabled = false;
  } else {
    submitButton.disabled = true;
  }
}

var minutesLabel = document.getElementById("minutes");
var secondsLabel = document.getElementById("seconds");
var totalSeconds = 0;

console.log(minutesLabel);
console.log(secondsLabel);

setInterval(setTime, 1000);

function setTime() {
  ++totalSeconds;
  secondsLabel.innerHTML = pad(totalSeconds % 60);
  minutesLabel.innerHTML = pad(parseInt(totalSeconds / 60));
}

function pad(val) {
  var valString = val + "";
  if (valString.length < 2) {
    return "0" + valString;
  } else {
    return valString;
  }
}

document.getElementById("extraBtn").addEventListener("click", function () {
  document.getElementById("myBtn").disabled = false; // Enable the "submit & next" button
  document.forms[0].submit(); // Submit the form
});


// Get the "Finish" link element
const finishLink = document.getElementById('finish');

// Add an event listener to the link
finishLink.addEventListener('click', function(event) {
  // Prevent the link from redirecting immediately
  event.preventDefault();

  // Display the confirmation dialog
  const confirmation = confirm("Are you sure you want to finish the session?");

  // If the user clicks "OK" in the confirmation dialog, redirect them to the "Finish" page
  if (confirmation) {
    window.location.href = finishLink.href;
  }
  // If the user clicks "Cancel" in the confirmation dialog, do nothing
  // The link will remain inactive
});
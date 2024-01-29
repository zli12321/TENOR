let wordsToHighlight = [];

const acc = document.querySelectorAll(".accordion");
const accordionButtons = document.querySelectorAll(".accordion-btn");

const span_words = document.querySelectorAll(".accordion-item-header");
const viewButtons = document.querySelectorAll(".accordion-btn");
console.log({ viewButtons });

viewButtons.forEach((btn, index) => {
  btn.addEventListener("click", function (event) {
    removeAllActive();

    let content = btn.parentElement;
    content.classList.add("active");
    btn.innerText = "Hide";

    let topic_el = btn.parentElement.nextElementSibling.getElementsByTagName("li");

    const wordsArr = [];
    Array.from(topic_el).forEach(function (ele) {
      wordsArr.push(ele.innerText);
    });
    highlighWords(wordsArr);
  });
});

const textElement = document.getElementById("text");
const original_text = textElement.textContent;

function highlighWords(words) {
  var text = original_text;
  words.forEach((word) => {
    if (word.length>2){
      const pattern = new RegExp(word, "gi");
      text = text.replace(
        pattern,
        "<span style='background-color:yellow'>" + word + "</span>"
      );
      textElement.innerHTML = text;
    }
  });
}

function removeAllActive() {
  viewButtons.forEach((button) => {
    button.parentElement.classList.remove("active");
    button.innerText = "View";
  });
}

// texts =  document.getElementById("text")
// var markInstance = new Mark(texts);

// keywords = []
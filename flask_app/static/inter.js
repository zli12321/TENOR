var rangeSlider = document.getElementById("rs-range-line");
var rangeBullet = document.getElementById("rs-bullet");
var output = getElementById("ppp");
const Http = new XMLHttpRequest();
var current;
            

// rangeSlider.addEventListener("input", showSliderValue, false);

// function showSliderValue() {

//   rangeBullet.innerHTML = rangeSlider.value;
//   var bulletPosition = (rangeSlider.value /rangeSlider.max);
//   rangeBullet.style.left = (bulletPosition * 350) + "px";

// }


rangeSlider.oninput = function(){
    rangeBullet.innerHTML = rangeSlider.value;
    var bulletPosition = (rangeSlider.value /rangeSlider.max);
    rangeBullet.style.left = (bulletPosition * 350) + "px";
    current = this.value;
    probability.innerHTML=current
    // output = getElementById("ppp")

    // I've added this call to the server, which send 'current' value
    // Http.open('POST', '/slider_update')
    // Http.send(current)
}
const wordsToHighlight = ["goal", "risk", "organizations"];

const textElement = document.getElementById("text");
const text = textElement.textContent;

wordsToHighlight.forEach(word => {
    const pattern = new RegExp("\\b" + word + "\\b", "gi");
    const highlightedText = text.replace(pattern, "<span class='highlight'>" + word + "</span>");
    textElement.innerHTML = highlightedText;
});

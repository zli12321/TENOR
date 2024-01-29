// Start the timer for saving label data
var timer = setInterval(saveLabels, 60000); // 1 minute (1 * 60 * 1000 milliseconds)

// var url = 'https://nist-topic-model.umiacs.umd.edu/'
// Function to save labels data
let labelSeconds = localStorage.getItem("labelSeconds");
if (!labelSeconds) {
    labelSeconds = 0;
}
function saveLabels() {
    labelSeconds += 60
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url, false);
    xhr.send(labelSeconds);
    localStorage.setItem("labelSeconds", labelSeconds)
}

// Timer on navigation
let seconds = localStorage.getItem("sessionSeconds");
if (!seconds) {
    seconds = 0;
}

function showReminderPopup30() {
    alert("30 minutes have passed through the study!");
}

function showReminderPopup45() {
    alert("45 minutes have passed through the study! You can start wrapping up at 55 minutes and take the survey");
}

function showReminderPopup60() {
    alert("Time is up! You can click \'Finish\' to take the survey now");
}

let sessionTimer = setInterval(countUpSession, 1000);

function countUpSession() {
    ++seconds;

    if (seconds === 1800) {
        showReminderPopup30();
    }
    if (seconds === 2700) {
        showReminderPopup30();
    }
    if (seconds === 4020) {
        showReminderPopup60();
    }

    let hour = Math.floor(seconds / 3600);
    let minute = Math.floor((seconds - hour * 3600) / 60);
    let updSecond = seconds - (hour * 3600 + minute * 60);

    if (updSecond < 10){
        updSecond = "0" + updSecond;
    }

    if (minute < 10){
        minute = "0" + minute;
    }

    if (hour < 10){
        hour = "0" + hour;
    }
    
        
    document.getElementById("sessionTimer").innerHTML = hour + ":" + minute + ":" + updSecond;
    localStorage.setItem("sessionSeconds", seconds)
}

let logoutButton = document.getElementById("finish");
logoutButton.addEventListener("click", clearLocalStorage);

function clearLocalStorage() {
    seconds = 0;
    localStorage.clear();
}


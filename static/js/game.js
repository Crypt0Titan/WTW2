let timer;
let timeLeft;

function updateCountdown() {
    const countdownElement = document.getElementById('countdown');
    const startTime = new Date(document.getElementById('start-time').dataset.startTime);
    const now = new Date();
    timeLeft = startTime - now;

    if (timeLeft <= 0) {
        countdownElement.textContent = "Game has started!";
        clearInterval(timer);  // Ensure the timer is cleared when the game starts
        window.location.href = "/game/" + gameId + "/play";  // Redirect to play game
    } else {
        const seconds = Math.floor(timeLeft / 1000);  // Get total seconds left
        countdownElement.textContent = seconds + "s";  // Display seconds with 's' to indicate seconds
    }
}

function startCountdownTimer() {
    timer = setInterval(updateCountdown, 1000);  // Keep the setInterval call and clear it as needed
    updateCountdown();  // Initial call to update countdown
}

function submitAnswers() {
    const form = document.getElementById('answer-form');
    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.game_complete) {
            window.location.href = "/game/" + gameId + "/result";  // Redirect to game results page
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const gameStartTime = new Date(document.getElementById('start-time').dataset.startTime);
    const now = new Date();
    const timeUntilStart = (gameStartTime - now) / 1000;  // Time until game start in seconds

    if (timeUntilStart > 0) {
        setTimeout(() => {
            startCountdownTimer();  // Start the countdown timer if the game hasn't started yet
        }, timeUntilStart * 1000);
    } else {
        startCountdownTimer();  // If the game has already started, start the countdown immediately
    }

    // Handle form submission for answers
    document.getElementById('answer-form').addEventListener('submit', function(e) {
        e.preventDefault();  // Prevent default form submission
        submitAnswers();
    });
});

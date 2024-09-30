let timer;
let timeLeft;

function startTimer(duration) {
    timeLeft = duration;
    timer = setInterval(function() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        document.getElementById('timer').textContent = 
            (minutes < 10 ? "0" + minutes : minutes) + ":" + 
            (seconds < 10 ? "0" + seconds : seconds);
        
        if (--timeLeft < 0) {
            clearInterval(timer);
            submitAnswers();
        }
    }, 1000);
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
        window.location.href = `/game/${gameId}/result`;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const gameStartTime = new Date(document.getElementById('game-start-time').dataset.startTime);
    const now = new Date();
    const timeUntilStart = (gameStartTime - now) / 1000;
    
    if (timeUntilStart > 0) {
        setTimeout(() => {
            startTimer(document.getElementById('time-limit').dataset.timeLimit);
        }, timeUntilStart * 1000);
    } else {
        startTimer(document.getElementById('time-limit').dataset.timeLimit);
    }

    document.getElementById('answer-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitAnswers();
    });
});

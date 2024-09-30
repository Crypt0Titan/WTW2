document.addEventListener('DOMContentLoaded', function() {
    const startGameButtons = document.querySelectorAll('.start-game-btn');
    
    startGameButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const gameId = this.dataset.gameId;
            fetch(`/admin/start_game/${gameId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Game started successfully');
                        location.reload();
                    } else {
                        alert('Failed to start game: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while starting the game');
                });
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin.js loaded');
    const startGameButtons = document.querySelectorAll('.start-game-btn');
    
    console.log('Number of start game buttons found:', startGameButtons.length);

    startGameButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const gameId = this.dataset.gameId;
            console.log('Start game button clicked for game ID:', gameId);
            fetch(`/admin/start_game/${gameId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
                .then(response => response.json())
                .then(data => {
                    console.log('Start game response:', data);
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

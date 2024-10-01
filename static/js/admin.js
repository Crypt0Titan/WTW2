document.addEventListener('DOMContentLoaded', function () {
    const startGameButtons = document.querySelectorAll('.start-game-btn');

    startGameButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            const gameId = this.getAttribute('data-game-id');

            if (gameId) {
                fetch(`/admin/start_game/${gameId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => {
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        console.error('Failed to start game.');
                    }
                })
                .catch(error => console.error('Error:', error));
            } else {
                console.error('Game ID is undefined.');
            }
        });
    });
});

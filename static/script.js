document.getElementById('unfollowForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const formData = new FormData(this);
    const statusUpdates = document.getElementById('statusUpdates');
    statusUpdates.innerHTML = ''; // Limpa mensagens anteriores
    document.getElementById('result').style.display = 'block';

    // Iniciar a conexão SSE
    const eventSource = new EventSource(`/status?username=${formData.get('username')}&password=${formData.get('password')}&limit=${formData.get('limit')}`);

    eventSource.onmessage = function(event) {
        // Exibe as atualizações de status
        statusUpdates.innerHTML += event.data + "\n";
    };

    eventSource.onerror = function() {
        statusUpdates.innerHTML += "Erro ao receber as atualizações.\n";
        eventSource.close();
    };
});

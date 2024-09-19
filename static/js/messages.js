document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function() {
        const messages = document.querySelectorAll('.messages .alert');
        messages.forEach(function(message) {
            message.style.display = 'none';
        });
    }, 8000); // 4000 milliseconds = 8 seconds
});
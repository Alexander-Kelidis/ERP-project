document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function() {
        const messages = document.querySelectorAll('.messages .alert');
        messages.forEach(function(message) {
            message.style.display = 'none';
        });
    }, 4000); // 4000 milliseconds = 4 seconds
});
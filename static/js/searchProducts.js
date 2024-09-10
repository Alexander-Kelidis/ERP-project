document.addEventListener('DOMContentLoaded', function() {
    const searchField = document.getElementById('searchField');
    const table = document.getElementById('productsTable');
    let rows = table.getElementsByTagName('tr');

    searchField.addEventListener('keyup', function() {
        const filter = searchField.value.trim().toLowerCase();

        rows = table.getElementsByTagName('tr'); // Update rows on each keyup

        for (let i = 0; i < rows.length; i++) {
            const nameCell = rows[i].querySelector('.name');
            const supplierCell = rows[i].querySelector('.supplier');
            const dateCell = rows[i].querySelector('.date');

            const nameText = nameCell ? nameCell.textContent.trim().toLowerCase() : '';
            const supplierText = supplierCell ? supplierCell.textContent.trim().toLowerCase() : '';
            const dateText = dateCell ? dateCell.textContent.trim().toLowerCase() : '';

            const isVisible = nameText.includes(filter) || supplierText.includes(filter) || dateText.includes(filter);

            rows[i].style.display = isVisible ? '' : 'none';
        }
    });
});


    
  
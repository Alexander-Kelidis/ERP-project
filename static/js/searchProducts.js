
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
            const productIdCell = rows[i].querySelector('.productid'); 

            const nameText = nameCell ? nameCell.textContent.trim().toLowerCase() : '';
            const supplierText = supplierCell ? supplierCell.textContent.trim().toLowerCase() : '';
            const productIdText = productIdCell ? productIdCell.textContent.trim().toLowerCase() : ''; // Treat as string 

            // Update the visibility condition to include product_id
            const isVisible = nameText.includes(filter) || supplierText.includes(filter) || productIdText.includes(filter);

            rows[i].style.display = isVisible ? '' : 'none';
        }
    });
});

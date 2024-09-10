document.addEventListener('DOMContentLoaded', function() {
  const searchField = document.getElementById('searchField');
  const table = document.getElementById('customersTable');
  const rows = table.getElementsByTagName('tr');

  searchField.addEventListener('keyup', function() {
      const filter = searchField.value.toLowerCase();

      for (let i = 0; i < rows.length; i++) {
          const customernameCell = rows[i].querySelector('.customername');
          const companynameCell = rows[i].querySelector('.companyname');
          const dateCell = rows[i].querySelector('.date');
          const countryCell = rows[i].querySelector('.country');
          
          const nameText = customernameCell ? customernameCell.textContent.toLowerCase() : '';
          const companyText = companynameCell ? companynameCell.textContent.toLowerCase() : '';
          const dateText = dateCell ? dateCell.textContent.toLowerCase() : '';
          const countryText = countryCell ? countryCell.textContent.toLowerCase() : '';

          if (nameText.includes(filter) || countryText.includes(filter) || companyText.includes(filter) || dateText.includes(filter)) {
              rows[i].style.display = '';
          } else {
              rows[i].style.display = 'none';
          }
      }
  });
});
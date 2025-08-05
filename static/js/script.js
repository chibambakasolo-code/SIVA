document.addEventListener('DOMContentLoaded', function() {
    // Initialize sample data
    document.getElementById('initSampleData').addEventListener('click', function() {
        if (confirm('This will load sample data and overwrite any existing data. Continue?')) {
            fetch('/initialize_sample_data')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Sample data loaded successfully!');
                        window.location.reload();
                    }
                });
        }
    });

    // Search functionality
    const searchInput = document.getElementById('searchItem');
    const searchResults = document.getElementById('searchResults');
    const saleForm = document.getElementById('saleForm');
    
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        fetch(`/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(items => {
                searchResults.innerHTML = '';
                
                if (items.length === 0) {
                    searchResults.style.display = 'none';
                    return;
                }
                
                items.forEach(item => {
                    const itemElement = document.createElement('button');
                    itemElement.type = 'button';
                    itemElement.className = 'list-group-item list-group-item-action';
                    itemElement.innerHTML = `
                        <strong>${item.name}</strong> (${item.category})<br>
                        <small>Price: K${item.price.toFixed(2)} | Stock: ${item.quantity}</small>
                    `;
                    
                    itemElement.addEventListener('click', function() {
                        document.getElementById('saleItemId').value = item.id;
                        document.getElementById('saleItemName').textContent = `${item.name} (K${item.price.toFixed(2)})`;
                        document.getElementById('salePrice').value = item.price;
                        searchResults.style.display = 'none';
                        saleForm.style.display = 'block';
                    });
                    
                    searchResults.appendChild(itemElement);
                });
                
                searchResults.style.display = 'block';
            });
    });
    
    // Hide search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
    
    // Calculate total price when quantity changes
    document.getElementById('saleQuantity').addEventListener('input', function() {
        const quantity = parseFloat(this.value) || 1;
        const itemId = document.getElementById('saleItemId').value;
        
        if (itemId) {
            fetch(`/get_item?id=${itemId}`)
                .then(response => response.json())
                .then(item => {
                    if (item) {
                        document.getElementById('salePrice').value = (item.price * quantity).toFixed(2);
                    }
                });
        }
    });
    
    // Record sale
    document.getElementById('recordSale').addEventListener('click', function() {
        const itemId = document.getElementById('saleItemId').value;
        const quantity = document.getElementById('saleQuantity').value;
        const price = document.getElementById('salePrice').value;
        
        if (!itemId || !quantity || !price) {
            alert('Please fill all fields');
            return;
        }
        
        fetch('/add_sale', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item_id: itemId,
                quantity: quantity,
                price: price
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Sale recorded successfully!');
                window.location.reload();
            } else {
                alert('Error: ' + (data.error || 'Failed to record sale'));
            }
        });
    });
    
    // Chart buttons
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const chartType = this.getAttribute('data-type');
            loadChart(chartType);
        });
    });
    
    // Add item form
    document.getElementById('saveItem').addEventListener('click', function() {
        const formData = {
            name: document.getElementById('itemName').value,
            category: document.getElementById('itemCategory').value,
            price: parseFloat(document.getElementById('itemPrice').value),
            quantity: parseInt(document.getElementById('itemQuantity').value),
            threshold: parseInt(document.getElementById('itemThreshold').value)
        };
        
        // Validate
        if (!formData.name || !formData.category || isNaN(formData.price) || 
            isNaN(formData.quantity) || isNaN(formData.threshold)) {
            alert('Please fill all fields with valid values');
            return;
        }
        
        fetch('/update_inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item_id: 'new',
                updates: formData
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Item added successfully!');
                window.location.reload();
            } else {
                alert('Failed to add item');
            }
        });
    });
    
    // Edit item buttons
    document.querySelectorAll('.edit-item').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.getAttribute('data-id');
            
            fetch(`/get_item?id=${itemId}`)
                .then(response => response.json())
                .then(item => {
                    if (item) {
                        document.getElementById('editItemId').value = item.id;
                        document.getElementById('editItemName').value = item.name;
                        document.getElementById('editItemCategory').value = item.category || '';
                        document.getElementById('editItemPrice').value = item.price;
                        document.getElementById('editItemQuantity').value = item.quantity;
                        document.getElementById('editItemThreshold').value = item.threshold;
                        
                        // Show modal
                        const modal = new bootstrap.Modal(document.getElementById('editItemModal'));
                        modal.show();
                    }
                });
        });
    });
    
    // Update item
    document.getElementById('updateItem').addEventListener('click', function() {
        const itemId = document.getElementById('editItemId').value;
        const formData = {
            name: document.getElementById('editItemName').value,
            category: document.getElementById('editItemCategory').value,
            price: parseFloat(document.getElementById('editItemPrice').value),
            quantity: parseInt(document.getElementById('editItemQuantity').value),
            threshold: parseInt(document.getElementById('editItemThreshold').value)
        };
        
        fetch('/update_inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item_id: itemId,
                updates: formData
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Item updated successfully!');
                window.location.reload();
            } else {
                alert('Failed to update item');
            }
        });
    });
    
    // Delete item buttons
    document.querySelectorAll('.delete-item').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.getAttribute('data-id');
            
            if (confirm('Are you sure you want to delete this item?')) {
                fetch('/update_inventory', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        item_id: itemId,
                        updates: {quantity: 0} // Mark for deletion
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Item deleted successfully!');
                        window.location.reload();
                    } else {
                        alert('Failed to delete item');
                    }
                });
            }
        });
    });
    
    // Refresh sales button
    document.getElementById('refreshSales').addEventListener('click', function() {
        window.location.reload();
    });
});

function loadChart(chartType) {
    fetch(`/get_charts?type=${chartType}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('chartContainer');
            container.innerHTML = ''; // Clear previous chart
            
            // Create a div for the chart
            const chartDiv = document.createElement('div');
            chartDiv.id = 'dynamicChart';
            container.appendChild(chartDiv);
            
            Plotly.newPlot('dynamicChart', data.data, data.layout);
        });
                          }

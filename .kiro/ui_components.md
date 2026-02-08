# UI Components Guide

## Overview
All UI components use vanilla JavaScript with no frameworks. Server-rendered HTML templates with client-side interactivity.

## Transactions Page

### Dual Dropdown System
**Location**: `templates/transactions.html`

**Implementation**:
```javascript
function renderCategorySelect(txn) {
    // Determine current selection
    let parentId = '';
    let subId = '';
    
    if (txn.category_id) {
        for (const cat of categories) {
            if (cat.id === txn.category_id) {
                parentId = cat.id;  // It's a parent
                break;
            }
            if (cat.subcategories) {
                const sub = cat.subcategories.find(s => s.id === txn.category_id);
                if (sub) {
                    parentId = cat.id;  // Found parent
                    subId = sub.id;     // It's a subcategory
                    break;
                }
            }
        }
    }
    
    // Render parent dropdown
    const parent = categories.find(c => c.id == parentId);
    const subs = parent?.subcategories || [];
    
    return `
        <div style="display: flex; gap: 5px;">
            <select class="category" onchange="handleCategoryChange(${txn.id}, this)">
                <option value="">Category...</option>
                ${categories.map(cat => 
                    `<option value="${cat.id}" ${parentId == cat.id ? 'selected' : ''}>${cat.name}</option>`
                ).join('')}
            </select>
            <select class="subcategory" onchange="updateCategory(${txn.id}, this.value)" 
                    style="${subs.length ? '' : 'display:none;'}">
                <option value="">Subcategory...</option>
                ${subs.map(sub => 
                    `<option value="${sub.id}" ${subId == sub.id ? 'selected' : ''}>${sub.name}</option>`
                ).join('')}
            </select>
        </div>
    `;
}

function handleCategoryChange(txnId, selectElement) {
    const parentId = selectElement.value;
    const parent = categories.find(c => c.id == parentId);
    const subs = parent?.subcategories || [];
    
    const subSelect = selectElement.parentElement.querySelector('.subcategory');
    
    if (subs.length > 0) {
        // Show subcategory dropdown
        subSelect.innerHTML = '<option value="">Subcategory...</option>' + 
            subs.map(sub => `<option value="${sub.id}">${sub.name}</option>`).join('');
        subSelect.style.display = '';
    } else {
        // Hide and save parent
        subSelect.style.display = 'none';
        updateCategory(txnId, parentId);
    }
}
```

**Key Features**:
- First dropdown shows all parent categories
- Second dropdown appears only when parent has subcategories
- Automatically saves when parent without subs is selected
- Preserves selection on page reload

### Bulk Operations
```javascript
function updateSelectedCount() {
    const selected = document.querySelectorAll('.txn-select:checked');
    document.getElementById('selected-count').textContent = selected.length;
}

async function approveSelected() {
    const checkboxes = document.querySelectorAll('.txn-select:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.id));
    
    // Validate all have categories
    const missingCategory = selectedIds.some(id => {
        const txn = transactions.find(t => t.id === id);
        return !txn.category_id;
    });
    
    if (missingCategory) {
        alert('All transactions must have a category before approving');
        return;
    }
    
    // Approve all
    for (const id of selectedIds) {
        const txn = transactions.find(t => t.id === id);
        await fetch(`/api/transactions/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                is_approved: true,
                category_id: txn.category_id
            })
        });
    }
    
    await loadTransactions();
}
```

## Configuration Page

### Text Editor Mode
**Location**: `templates/config.html`

**Format**:
```
Income Categories:
Income
Income | Salary
Income | Bonus

Expense Categories:
Groceries
Home
Home | Rent
Home | Utilities
```

**Implementation**:
```javascript
function renderCategoriesTree() {
    const incomeText = document.getElementById('income-text');
    const expenseText = document.getElementById('expense-text');
    
    let incomeLines = [];
    let expenseLines = [];
    
    categories.forEach(cat => {
        const color = cat.color ? ' | ' + cat.color : '';
        const line = `${cat.name}${color}`;
        
        if (cat.type === 'income') {
            incomeLines.push(line);
            if (cat.subcategories) {
                cat.subcategories.forEach(sub => {
                    const subColor = sub.color ? ' | ' + sub.color : '';
                    incomeLines.push(`${cat.name} | ${sub.name}${subColor}`);
                });
            }
        } else if (cat.type === 'expense') {
            expenseLines.push(line);
            if (cat.subcategories) {
                cat.subcategories.forEach(sub => {
                    const subColor = sub.color ? ' | ' + sub.color : '';
                    expenseLines.push(`${cat.name} | ${sub.name}${subColor}`);
                });
            }
        }
    });
    
    incomeText.value = incomeLines.join('\n');
    expenseText.value = expenseLines.join('\n');
}
```

### Change Confirmation
```javascript
async function saveAllCategories() {
    // ... validation ...
    
    // Analyze changes
    const toCreate = [];
    const toUpdate = [];
    const toDelete = [];
    
    // ... analysis logic ...
    
    // Show confirmation
    let message = 'Review changes:\n\n';
    
    if (toCreate.length > 0) {
        message += `✅ CREATE (${toCreate.length}):\n${toCreate.map(c => '  + ' + c).join('\n')}\n\n`;
    }
    
    if (toUpdate.length > 0) {
        message += `✏️ UPDATE (${toUpdate.length}):\n${toUpdate.map(c => '  ~ ' + c).join('\n')}\n\n`;
    }
    
    if (toDelete.length > 0) {
        message += `❌ DELETE (${toDelete.length}):\n${toDelete.map(c => '  - ' + c).join('\n')}\n\n`;
    }
    
    message += 'Continue?';
    
    if (!confirm(message)) return;
    
    // Execute changes...
}
```

### List View Mode
```javascript
function renderCategoriesList() {
    const list = document.getElementById('categories-list');
    list.innerHTML = '';
    
    categories.forEach(cat => {
        const div = document.createElement('div');
        div.style.cssText = 'background: #f8f9fa; padding: 15px; margin-bottom: 10px; border-radius: 4px;';
        div.innerHTML = `
            <div>
                <span class="badge badge-${cat.type}">${cat.type}</span>
                <strong>${cat.name}</strong>
                <span style="color: #6c757d;">${(cat.subcategories || []).length} subcategories</span>
            </div>
            <button class="btn btn-primary" onclick="openCategoryDialog(${cat.id})">Edit</button>
        `;
        list.appendChild(div);
    });
}
```

## Dashboard Page

### Chart.js Integration
**Location**: `templates/dashboard.html`

```javascript
// Category spending pie chart
const ctx = document.getElementById('categoryChart').getContext('2d');
new Chart(ctx, {
    type: 'pie',
    data: {
        labels: categoryLabels,
        datasets: [{
            data: categoryAmounts,
            backgroundColor: categoryColors
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'right'
            }
        }
    }
});

// Monthly trend line chart
const trendCtx = document.getElementById('trendChart').getContext('2d');
new Chart(trendCtx, {
    type: 'line',
    data: {
        labels: months,
        datasets: [{
            label: 'Income',
            data: incomeData,
            borderColor: '#28a745',
            fill: false
        }, {
            label: 'Expenses',
            data: expenseData,
            borderColor: '#dc3545',
            fill: false
        }]
    }
});
```

## Common Patterns

### API Calls
```javascript
// GET
const response = await fetch('/api/transactions');
const data = await response.json();

// POST
await fetch('/api/categories', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: 'Groceries', type: 'expense'})
});

// PATCH
await fetch(`/api/transactions/${id}`, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({category_id: 5})
});

// DELETE
await fetch(`/api/categories/${id}`, {method: 'DELETE'});
```

### Error Handling
```javascript
try {
    const res = await fetch('/api/categories', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (!res.ok) {
        const error = await res.text();
        throw new Error(`Failed: ${error}`);
    }
    
    const result = await res.json();
    // Success
} catch (error) {
    alert('Error: ' + error.message);
    console.error(error);
}
```

### Modal Dialogs
```javascript
function openModal() {
    document.getElementById('my-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('my-modal').classList.remove('active');
}
```

**CSS**:
```css
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
}

.modal.active {
    display: flex;
    align-items: center;
    justify-content: center;
}
```

## Styling Conventions

### Colors
- Primary: `#007bff` (blue)
- Success: `#28a745` (green)
- Danger: `#dc3545` (red)
- Warning: `#ffc107` (yellow)
- Secondary: `#6c757d` (gray)

### Badges
```css
.badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}

.badge-income { background: #d4edda; color: #155724; }
.badge-expense { background: #f8d7da; color: #721c24; }
.badge-approved { background: #28a745; color: white; }
.badge-pending { background: #ffc107; color: #000; }
```

### Buttons
```css
.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.btn-primary { background: #007bff; color: white; }
.btn-success { background: #28a745; color: white; }
.btn-danger { background: #dc3545; color: white; }
```

## Accessibility

- Use semantic HTML (`<button>`, `<select>`, etc.)
- Include labels for form inputs
- Use ARIA attributes where needed
- Ensure keyboard navigation works
- Maintain color contrast ratios

## Performance Tips

- Minimize DOM manipulation
- Use event delegation for dynamic elements
- Debounce search/filter inputs
- Cache API responses when appropriate
- Use CSS for animations (not JavaScript)

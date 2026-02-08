#!/usr/bin/env python3
"""Update frontend to handle paginated responses and string amounts"""

import re

def update_transactions_html():
    with open('transactions.html', 'r') as f:
        content = f.read()
    
    # Update loadTransactions to handle pagination
    old_load = r"const res = await fetch\(`/api/transactions\?\$\{params\}`\);\s*transactions = await res\.json\(\);"
    new_load = """const res = await fetch(`/api/transactions?${params}`);
            const data = await res.json();
            transactions = data.transactions || [];
            pagination = data.pagination || {};"""
    
    content = re.sub(old_load, new_load, content)
    
    # Add pagination variable at top of script
    old_vars = r"let transactions = \[\];"
    new_vars = """let transactions = [];
        let pagination = {};"""
    content = re.sub(old_vars, new_vars, content)
    
    # Update amount parsing to handle strings
    old_amount = r"const amount = parseFloat\(txn\.amount\);"
    new_amount = "const amount = parseFloat(txn.amount || 0);"
    content = re.sub(old_amount, new_amount, content)
    
    # Add pagination controls before table
    pagination_html = '''
        <div class="pagination" id="pagination" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
            <div>
                <span id="page-info">Page 1 of 1 (0 items)</span>
            </div>
            <div style="display: flex; gap: 10px;">
                <button onclick="goToPage(1)" id="btn-first" style="padding: 6px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer;">First</button>
                <button onclick="goToPage(pagination.page - 1)" id="btn-prev" style="padding: 6px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer;">Previous</button>
                <select id="page-select" onchange="goToPage(parseInt(this.value))" style="padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px;"></select>
                <button onclick="goToPage(pagination.page + 1)" id="btn-next" style="padding: 6px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer;">Next</button>
                <button onclick="goToPage(pagination.pages)" id="btn-last" style="padding: 6px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer;">Last</button>
                <select id="per-page" onchange="changePerPage()" style="padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px;">
                    <option value="25">25 per page</option>
                    <option value="50">50 per page</option>
                    <option value="100" selected>100 per page</option>
                    <option value="200">200 per page</option>
                </select>
            </div>
        </div>'''
    
    # Insert pagination before table
    content = re.sub(
        r'(<div class="bulk-actions">.*?</div>)',
        r'\1\n' + pagination_html,
        content,
        flags=re.DOTALL
    )
    
    # Add pagination functions before closing script tag
    pagination_funcs = '''
        function updatePagination() {
            if (!pagination.total) {
                document.getElementById('pagination').style.display = 'none';
                return;
            }
            
            document.getElementById('pagination').style.display = 'flex';
            document.getElementById('page-info').textContent = 
                `Page ${pagination.page} of ${pagination.pages} (${pagination.total} items)`;
            
            // Update buttons
            document.getElementById('btn-first').disabled = pagination.page === 1;
            document.getElementById('btn-prev').disabled = pagination.page === 1;
            document.getElementById('btn-next').disabled = pagination.page === pagination.pages;
            document.getElementById('btn-last').disabled = pagination.page === pagination.pages;
            
            // Update page select
            const pageSelect = document.getElementById('page-select');
            pageSelect.innerHTML = '';
            for (let i = 1; i <= pagination.pages; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = `Page ${i}`;
                if (i === pagination.page) option.selected = true;
                pageSelect.appendChild(option);
            }
        }
        
        function goToPage(page) {
            if (page < 1 || page > pagination.pages) return;
            const params = new URLSearchParams(window.location.search);
            params.set('page', page);
            window.history.pushState({}, '', `?${params}`);
            loadTransactions();
        }
        
        function changePerPage() {
            const perPage = document.getElementById('per-page').value;
            const params = new URLSearchParams(window.location.search);
            params.set('per_page', perPage);
            params.set('page', '1');
            window.history.pushState({}, '', `?${params}`);
            loadTransactions();
        }
'''
    
    # Add before closing script tag
    content = re.sub(
        r'(</script>)',
        pagination_funcs + r'\n    \1',
        content
    )
    
    # Update renderTransactions to call updatePagination
    content = re.sub(
        r'(function renderTransactions\(\) \{.*?tbody\.innerHTML = \'\';)',
        r'\1\n            updatePagination();',
        content,
        flags=re.DOTALL
    )
    
    # Update loadTransactions to include page params
    old_params = r"const params = new URLSearchParams\(\);"
    new_params = """const params = new URLSearchParams();
            
            // Pagination
            const urlParams = new URLSearchParams(window.location.search);
            const page = urlParams.get('page') || '1';
            const perPage = urlParams.get('per_page') || '100';
            params.append('page', page);
            params.append('per_page', perPage);"""
    
    content = re.sub(old_params, new_params, content)
    
    with open('transactions.html', 'w') as f:
        f.write(content)
    
    print("✓ Updated transactions.html")

def update_config_html():
    with open('config.html', 'r') as f:
        content = f.read()
    
    # Update rules loading
    content = re.sub(
        r"const res = await fetch\('/api/category-rules'\);\s*rules = await res\.json\(\);",
        "const res = await fetch('/api/category-rules');\n            const data = await res.json();\n            rules = data.rules || [];",
        content
    )
    
    # Update forecast loading
    content = re.sub(
        r"const res = await fetch\('/api/forecast'\);\s*items = await res\.json\(\);",
        "const res = await fetch('/api/forecast');\n            const data = await res.json();\n            items = data.items || [];",
        content
    )
    
    # Update amount parsing
    content = re.sub(
        r"parseFloat\(item\.amount\)",
        "parseFloat(item.amount || 0)",
        content
    )
    
    with open('config.html', 'w') as f:
        f.write(content)
    
    print("✓ Updated config.html")

if __name__ == '__main__':
    print("Updating frontend files...\n")
    update_transactions_html()
    update_config_html()
    print("\n✅ Frontend updated successfully!")
    print("\nChanges made:")
    print("  • Transactions page now handles paginated responses")
    print("  • Added pagination controls (page navigation)")
    print("  • All amount parsing handles string values")
    print("  • Config page updated for rules and forecast pagination")

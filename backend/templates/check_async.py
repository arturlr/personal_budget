import re

with open('config.html', 'r') as f:
    lines = f.readlines()

in_async_function = False
function_depth = 0

for i, line in enumerate(lines, 1):
    # Check for async function declaration
    if 'async function' in line or 'async (' in line:
        in_async_function = True
        function_depth = 0
    
    # Track braces
    function_depth += line.count('{')
    function_depth -= line.count('}')
    
    # Reset when function ends
    if in_async_function and function_depth == 0 and '}' in line:
        in_async_function = False
    
    # Check for await outside async function
    if 'await ' in line and not in_async_function:
        # Ignore comments and strings
        if not line.strip().startswith('//') and 'async' not in line:
            print(f"Line {i}: {line.strip()}")

print("\n✓ Check complete")

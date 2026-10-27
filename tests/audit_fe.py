import re

with open('templates/index.html', encoding='utf-8') as f:
    html = f.read()

with open('static/js/app.js', encoding='utf-8') as f:
    js = f.read()

# Extract all event handlers from HTML: onclick="foo(...)", onchange="bar(...)", etc.
handlers = re.findall(r'on(?:click|change|submit|input)=["\']([a-zA-Z0-9_]+)\(', html)
handlers = set(handlers)
print(f'Total HTML event handlers found: {len(handlers)}')

# Find definitions in JS
missing_handlers = []
for h in sorted(handlers):
    # Search for function h( or const h = or window.h =
    pattern = rf'(?:function\s+{h}\s*\(|(?:const|let|var|window\.{h})\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>|window\.{h}\s*=)'
    if not re.search(pattern, js):
        missing_handlers.append(h)

if missing_handlers:
    print('WARNING: Missing handlers in app.js:', missing_handlers)
else:
    print('SUCCESS: All HTML event handler functions are defined in app.js!')

# Check element IDs in app.js vs index.html
js_ids = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", js))
html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
missing_ids = js_ids - html_ids
# filter dynamic ones
missing_ids = [i for i in missing_ids if not i.startswith('ai-chat-typing-indicator')]
if missing_ids:
    print('WARNING: Missing element IDs in index.html:', missing_ids)
else:
    print('SUCCESS: All element IDs referenced in app.js exist in index.html!')

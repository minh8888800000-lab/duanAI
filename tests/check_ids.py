import re

with open('static/js/app.js', encoding='utf-8') as f:
    js_content = f.read()

with open('templates/index.html', encoding='utf-8') as f:
    html_content = f.read()

ids_in_js = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", js_content))
ids_in_html = set(re.findall(r'id=["\']([^"\']+)["\']', html_content))

missing_ids = sorted(list(ids_in_js - ids_in_html))
print('Found IDs in JS:', len(ids_in_js))
print('Found IDs in HTML:', len(ids_in_html))
print('IDs in JS but MISSING in HTML:', missing_ids)

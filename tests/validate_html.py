from html.parser import HTMLParser

class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in self.void_elements:
            return
        if not self.stack:
            self.errors.append(f'Extra closing tag </{tag}> at {self.getpos()}')
            return
        last_tag, pos = self.stack.pop()
        if last_tag != tag:
            self.errors.append(f'Mismatched closing tag: expected </{last_tag}> (from {pos}), got </{tag}> at {self.getpos()}')

v = Validator()
with open('templates/index.html', encoding='utf-8') as f:
    v.feed(f.read())

print('Total errors:', len(v.errors))
for e in v.errors[:10]:
    print(e)
print('Remaining unclosed tags in stack:', len(v.stack))
for t, p in v.stack:
    print('Unclosed:', t, 'at line', p)

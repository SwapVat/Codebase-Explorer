import re

with open("src/App.jsx", "r") as f:
    content = f.read()

# Fix the conflicting color namespace
# Classes like `text-primary` need to be changed to `text-content-primary`
# Classes like `bg-primary` need to be changed to `bg-bg-primary`
# Classes like `border-primary` need to be changed to `border-border-primary`

replacements = {
    r'\bbg-primary\b': 'bg-bg-primary',
    r'\bbg-secondary\b': 'bg-bg-secondary',
    r'\bbg-secondary/50\b': 'bg-bg-secondary/50',
    r'\bbg-secondary/80\b': 'bg-bg-secondary/80',
    r'\bbg-tertiary\b': 'bg-bg-tertiary',
    r'\bbg-tertiary/50\b': 'bg-bg-tertiary/50',
    r'\bbg-tertiary/80\b': 'bg-bg-tertiary/80',
    r'\bbg-quaternary\b': 'bg-bg-quaternary',
    r'\bbg-quaternary/30\b': 'bg-bg-quaternary/30',
    
    r'\btext-primary\b': 'text-content-primary',
    r'\btext-secondary\b': 'text-content-secondary',
    r'\btext-muted\b': 'text-content-muted',
    r'\btext-inverted\b': 'text-content-inverted',
    
    r'\bborder-primary\b': 'border-border-primary',
    r'\bborder-secondary\b': 'border-border-secondary',
    r'\bborder-tertiary\b': 'border-border-tertiary',
}

for pattern, replacement in replacements.items():
    content = re.sub(pattern, replacement, content)

with open("src/App.jsx", "w") as f:
    f.write(content)


import os

# Resolve path relative to this script — works on any machine
file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'tkinter', 'screens', 'wallet_screen.py')

content = open(file, encoding='utf-8').read()
content = content.replace(
    '.strftime("%B")',
    '.strftime("%B").upper()'
)
open(file, 'w', encoding='utf-8').write(content)
print('Done')

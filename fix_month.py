file = r'c:\Users\zam\Documents\Tkinter_system\PC_Tkinter\tkinter\screens\wallet_screen.py'
content = open(file, encoding='utf-8').read()
content = content.replace(
    '.strftime("%B")',
    '.strftime("%B").upper()'
)
open(file, 'w', encoding='utf-8').write(content)
print('Done')

import os

# Resolve path relative to this script — works on any machine
file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'tkinter', 'screens', 'wallet_screen.py')

lines = open(file, encoding='utf-8').readlines()

# find _tx_item
tx_start = next(i for i, l in enumerate(lines) if '    def _tx_item(self, parent, t):' in l)
tx_end = next(i for i, l in enumerate(lines) if i > tx_start and l.startswith('    def '))

# find _open_tx_dialog
dlg_start = next(i for i, l in enumerate(lines) if '    def _open_tx_dialog(self, kind):' in l)
dlg_end = next(i for i, l in enumerate(lines) if i > dlg_start and l.startswith('    def '))

print('_tx_item:', tx_start+1, 'to', tx_end)
print('_open_tx_dialog:', dlg_start+1, 'to', dlg_end)
for i in range(tx_start, tx_end):
    print(i+1, lines[i].rstrip())
print('---')
for i in range(dlg_start, dlg_end):
    print(i+1, lines[i].rstrip())

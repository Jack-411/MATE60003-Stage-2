from imports import *

from BandGapGUI import BandGapGUI
import SystemCtrl

def on_close(root):
    root.destroy()
    SystemCtrl.clear_pycache()
    sys.exit(0)

def main():
    root = tk.Tk()
    gui = BandGapGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

if __name__ == "__main__":
    main()
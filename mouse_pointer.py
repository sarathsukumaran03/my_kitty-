import sys
import time
import threading
import tkinter as tk
import pyperclip
from pynput import keyboard, mouse

# Global state to hold our copied items
copied_stack = []
MAX_SLOTS = 3
pasting_mode = False

# Detect if the user is running macOS or Windows/Linux to assign correct keys
IS_MAC = sys.platform == "darwin"
HOTKEY_MODIFIERS = "Cmd + Option" if IS_MAC else "Ctrl + Alt"

# --- GUI CODE (Floating Cursor Overlay) ---
class CursorOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True) # Removes window borders and title bars
        self.root.attributes("-topmost", True) # Keeps the window always on top

        # Transparent background trick (uses system transparent color matching)
        if IS_MAC:
            self.root.attributes("-alpha", 0.85) # Smooth transparency for Mac
        else:
            self.root.attributes("-alpha", 0.90)
            self.root.wm_attributes("-transparentcolor", "black") # Transparent color for Windows

        # Custom styling: dark, clean HUD
        self.frame = tk.Frame(self.root, bg="#1a1a1a", bd=2, relief="ridge", highlightbackground="#333333")
        self.frame.pack(fill="both", expand=True)

        self.label = tk.Label(
            self.frame,
            text="[No Items Copied]",
            fg="#00E676", # Retro bright green text
            bg="#1a1a1a",
            font=("Courier", 10, "bold"),
            justify="left"
        )
        self.label.pack(padx=10, pady=8)

        # Start hidden until we copy something
        self.root.withdraw()

    def update_text(self, items, is_pasting_mode=False):
        if not items:
            self.root.withdraw()
            return

        header = "📋 PRESS 1, 2, or 3 TO PASTE:\n" if is_pasting_mode else "🛒 CARRIED ITEMS:\n"
        preview_lines = []
        for i, text in enumerate(items):
            truncated = text[:15].replace("\n", " ") + "..." if len(text) > 15 else text
            active_marker = "👉 " if is_pasting_mode else "  "
            preview_lines.append(f"{active_marker}[{i+1}] {truncated}")

        self.label.config(text=header + "\n".join(preview_lines))
        self.root.deiconify() # Reveal overlay

    def move_to(self, x, y):
        # Position overlay 15 pixels down and 15 pixels right from the mouse pointer
        self.root.geometry(f"+{x+15}+{y+15}")

# Initialize the UI in a background thread so it doesn't block keyboard listeners
overlay = None
def start_gui():
    global overlay
    overlay = CursorOverlay()
    overlay.root.mainloop()

gui_thread = threading.Thread(target=start_gui, daemon=True)
gui_thread.start()

# Let GUI initialize
time.sleep(0.5)

# --- KEYBOARD & CLIPBOARD LOGIC ---
def trigger_copy():
    global copied_stack

    # 1. Simulate a standard copy command to grab highlighted text
    controller = keyboard.Controller()
    if IS_MAC:
        with controller.pressed(keyboard.Key.cmd):
            controller.tap('c')
    else:
        with controller.pressed(keyboard.Key.ctrl):
            controller.tap('c')

    time.sleep(0.15) # Brief pause to allow the system clipboard to update

    # 2. Extract text from the clipboard and put it into our stack
    new_text = pyperclip.paste()
    if new_text and (not copied_stack or copied_stack[-1] != new_text):
        if len(copied_stack) >= MAX_SLOTS:
            copied_stack.pop(0) # Keep stack capped at 3 slots
        copied_stack.append(new_text)
        print(f"Copied: {new_text}")
        overlay.update_text(copied_stack)

def enter_paste_mode():
    global pasting_mode
    if not copied_stack:
        return
    pasting_mode = True
    overlay.update_text(copied_stack, is_pasting_mode=True)

def select_and_paste(slot_index):
    global pasting_mode, copied_stack
    if slot_index < len(copied_stack):
        target_text = copied_stack[slot_index]

        # Place selected text back on the system clipboard
        pyperclip.copy(target_text)

        # Simulate paste command
        controller = keyboard.Controller()
        if IS_MAC:
            with controller.pressed(keyboard.Key.cmd):
                controller.tap('v')
        else:
            with controller.pressed(keyboard.Key.ctrl):
                controller.tap('v')

        # Remove the pasted item from our carried stack
        copied_stack.pop(slot_index)

    pasting_mode = False
    overlay.update_text(copied_stack)

# --- MONITORING SYSTEM INPUT ---
def on_key_press(key):
    global pasting_mode
    if pasting_mode:
        # If we are selecting an item to paste, capture numbers 1, 2, or 3
        if hasattr(key, 'char') and key.char in ['1', '2', '3']:
            index = int(key.char) - 1
            select_and_paste(index)
            return False # Suppress key from registering on screen
        else:
            # Any other key cancels paste mode
            pasting_mode = False
            overlay.update_text(copied_stack)

# Mouse movement hook: constantly updates visual window position
def on_mouse_move(x, y):
    if overlay:
        overlay.move_to(x, y)

# Hotkey declarations
hotkeys_map = {
    '<ctrl>+<alt>+c' if not IS_MAC else '<cmd>+<alt>+c': trigger_copy,
    '<ctrl>+<alt>+v' if not IS_MAC else '<cmd>+<alt>+v': enter_paste_mode
}

# Start background event loops
keyboard_listener = keyboard.Listener(on_press=on_key_press)
keyboard_listener.start()

mouse_listener = mouse.Listener(on_move=on_mouse_move)
mouse_listener.start()

hotkey_listener = keyboard.GlobalHotKeys(hotkeys_map)
hotkey_listener.start()

print(f"🚀 Multi-Copy Active! Press {HOTKEY_MODIFIERS} + C to copy, and {HOTKEY_MODIFIERS} + V to paste.")
# Keep the main process running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting Multi-Copy tool.")
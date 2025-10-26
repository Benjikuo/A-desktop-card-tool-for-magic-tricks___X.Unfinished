import tkinter as tk
from PIL import Image, ImageTk
import subprocess

WHITE_IMG = "./image/button/card_button_white.png"
GRAY_IMG = "./image/button/card_button_gray.png"
ORANGE_IMG = "./image/button/card_button_orange.png"
TARGET_SCRIPT = "card.py"
BG_COLOR = "#00FF00"
SCALE = 0.52
card_program = None


def toggle_cards(event=None):
    global card_program
    if card_program and card_program.poll() is None:
        label.config(image=photo_white)
        print("🟥 close card.py")
        card_program.terminate()
        card_program = None
    else:
        label.config(image=photo_orange)
        print("🟩 open card.py")
        card_program = subprocess.Popen(["python", TARGET_SCRIPT])


def press_in(event):
    label.config(image=photo_gray)


def press_out(event):
    toggle_cards()


def check_card_program():
    global card_program
    if card_program and card_program.poll() is not None:
        label.config(image=photo_white)
        print("⬜ card.py is closed")
        card_program = None
    root.after(500, check_card_program)


root = tk.Tk()
root.overrideredirect(True)
root.config(bg=BG_COLOR)
root.wm_attributes("-transparentcolor", BG_COLOR)
root.geometry("+142+697")


img_white = Image.open(WHITE_IMG)
img_gray = Image.open(GRAY_IMG)
img_orange = Image.open(ORANGE_IMG)

if SCALE != 1.0:
    w, h = img_white.size
    img_white = img_white.resize((int(w * SCALE), int(h * SCALE)))
    img_gray = img_gray.resize((int(w * SCALE), int(h * SCALE)))
    img_orange = img_orange.resize((int(w * SCALE), int(h * SCALE)))

photo_white = ImageTk.PhotoImage(img_white)
photo_gray = ImageTk.PhotoImage(img_gray)
photo_orange = ImageTk.PhotoImage(img_orange)


label = tk.Label(root, image=photo_white, bg=BG_COLOR, bd=0)
label.pack()

check_card_program()

label.bind("<ButtonPress-1>", press_in)
label.bind("<ButtonRelease-1>", press_out)
root.mainloop()

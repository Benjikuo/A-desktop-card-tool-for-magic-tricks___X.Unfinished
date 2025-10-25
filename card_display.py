import tkinter as tk
from PIL import Image, ImageTk
import os, card_logic

BG_COLOR = "#09FF00"
IMAGE_FOLDER = "image/card"
CARD_SIZE = (74, 111)
BOX_SIZE = (80, 120)


def load_image(name, size):
    return ImageTk.PhotoImage(Image.open(os.path.join(IMAGE_FOLDER, name)).resize(size))


def key_pressed(event):
    if event.keysym == "Escape":
        root.destroy()


root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-transparentcolor", BG_COLOR)

w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"{w}x{h}+0+0")

canvas = tk.Canvas(root, width=w, height=h, bg=BG_COLOR, highlightthickness=0)
canvas.pack(fill="both", expand=True)

box_img = load_image("box.png", BOX_SIZE)
back_img = load_image("back.png", CARD_SIZE)
card_imgs = [
    load_image(f, CARD_SIZE)
    for f in os.listdir(IMAGE_FOLDER)
    if f.endswith(".png") and f not in ("box.png", "back.png")
]

card_logic.CardBox(canvas, w / 2, h - 108, box_img, back_img, card_imgs)

root.bind("<Key>", key_pressed)
root.mainloop()

import tkinter as tk
from PIL import Image, ImageTk
import os, random

# --- 基本設定 ---
BG_COLOR = "#09FF00"
IMAGE_FOLDER = "image/card"
CARD_SIZE = (74, 111)
BOX_SIZE = (80, 120)


def load_image(name, size):
    return ImageTk.PhotoImage(Image.open(os.path.join(IMAGE_FOLDER, name)).resize(size))


class CardBox:
    def __init__(self, canvas, x, y, box_img, back_img, card_imgs):
        self.canvas = canvas
        self.x, self.y = x, y
        self.box_img = box_img
        self.back_img = back_img
        self.card_imgs = card_imgs.copy()
        self.used_cards = set()

        self.box_id = canvas.create_image(x, y, image=self.box_img, tags="box")
        canvas.tag_bind(self.box_id, "<Button-1>", self.spawn_card)

    def spawn_card(self, event=None):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 沒有可用的卡片了！")
            return

        img = random.choice(available)
        self.used_cards.add(img)
        card = Card(self.canvas, self.x, self.y - 150, self.back_img, img, self)


class Card:
    def __init__(self, canvas, x, y, back_img, front_img, box):
        self.canvas = canvas
        self.back_img = back_img
        self.front_img = front_img
        self.box = box
        self.face_up = False

        self.card_id = canvas.create_image(x, y, image=self.back_img, tags="card")
        self.canvas.tag_bind(self.card_id, "<Button-1>", self.flip)

    def flip(self, event=None):
        self.face_up = not self.face_up
        self.canvas.itemconfig(
            self.card_id,
            image=self.front_img if self.face_up else self.back_img,
        )


root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-transparentcolor", BG_COLOR)

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.geometry(f"{screen_w}x{screen_h}+0+0")
canvas = tk.Canvas(
    root, width=screen_w, height=screen_h, bg=BG_COLOR, highlightthickness=0
)
canvas.pack(fill="both", expand=True)

box_img = load_image("box.png", BOX_SIZE)
back_img = load_image("back.png", CARD_SIZE)
card_imgs = [
    load_image(f, CARD_SIZE)
    for f in os.listdir(IMAGE_FOLDER)
    if f.endswith(".png") and f not in ("box.png", "box.png", "back.png")
]

card_box = CardBox(canvas, screen_w / 2, screen_h - 108, box_img, back_img, card_imgs)

root.mainloop()

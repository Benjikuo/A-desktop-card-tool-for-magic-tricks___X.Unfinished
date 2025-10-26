import tkinter as tk
from PIL import Image, ImageTk
import os, random, math

BG_COLOR = "#00FF00"
CARD_FOLDER = "image/card"
CARD_SIZE = (74, 111)
BOX_SIZE = (80, 120)


class Box:
    def __init__(self, canvas, x, y, box_img, back_img, card_imgs):
        self.canvas = canvas
        self.x, self.y = x, y

        self.box_img = box_img
        self.back_img = back_img
        self.card_imgs = card_imgs.copy()

        self.this_box = canvas.create_image(x, y, image=self.box_img, tags="box")
        self.used_cards = set()

        canvas.tag_bind(self.this_box, "<Button-1>", self.spawn_card)

    def spawn_card(self, event=None):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            return
        img = random.choice(available)
        self.used_cards.add(img)
        Card(self.canvas, self.x, self.y - 150, self.back_img, img, self)


class Card:
    def __init__(self, canvas, x, y, back_img, front_img, box):
        self.canvas = canvas
        self.back_img = back_img
        self.front_img = front_img
        self.box = box
        self.face_up = False
        self.flipping = False
        self.interactable = False
        self._drag_data = {"x": 0, "y": 0, "moved": False}
        self._start_pos = (0, 0)
        self.this_card = canvas.create_image(
            x, y + 50, image=self.back_img, tags="card"
        )
        self.animate_up(0)
        self.canvas.tag_bind(self.this_card, "<ButtonPress-1>", self.start_drag)
        self.canvas.tag_bind(self.this_card, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.this_card, "<ButtonRelease-1>", self.stop_drag)

    def animate_up(self, step):
        if step < 10:
            self.canvas.move(self.this_card, 0, -5)
            self.canvas.after(20, lambda: self.animate_up(step + 1))
        else:
            self.interactable = True

    def start_drag(self, event):
        if not self.interactable:
            return

        self._start_pos = (event.x, event.y)
        self.card_start = self.canvas.coords(self.this_card)
        self._drag_data = {"x": event.x, "y": event.y, "moved": False}
        self.canvas.tag_raise(self.this_card)

    def on_drag(self, event):
        if not self.interactable:
            return

        dx = event.x - self._start_pos[0]
        dy = event.y - self._start_pos[1]
        if abs(dx) > 2 or abs(dy) > 2:
            self._moved = True
        self.canvas.coords(
            self.this_card, self.card_start[0] + dx, self.card_start[1] + dy
        )

    def stop_drag(self, event):
        if not self.interactable:
            return

        dist = math.hypot(event.x - self._start_pos[0], event.y - self._start_pos[1])
        if dist < 5 and not self._drag_data["moved"]:
            self.flip_animated()
        self._drag_data = {"x": 0, "y": 0, "moved": False}

    def flip_animated(self, step=0):
        if self.flipping or not self.interactable:
            return

        self.flipping = True
        total_steps = 10
        shrink_steps = total_steps // 2

        def scale_image(scale):
            img = self.front_img if self.face_up else self.back_img
            pil = ImageTk.getimage(img)
            w, h = pil.size
            new_w = max(1, int(w * scale))
            resized = pil.resize((new_w, h))
            return ImageTk.PhotoImage(resized)

        def animate(step):
            if step < shrink_steps:
                scale = 1 - (step / shrink_steps)
                img = scale_image(scale)
                self.tk_tmp = img
                self.canvas.itemconfig(self.this_card, image=img)
                self.canvas.after(25, lambda: animate(step + 1))
            elif step == shrink_steps:
                self.face_up = not self.face_up
                self.canvas.itemconfig(
                    self.this_card,
                    image=self.front_img if self.face_up else self.back_img,
                )
                self.canvas.after(25, lambda: animate(step + 1))
            elif step <= total_steps:
                scale = (step - shrink_steps) / shrink_steps
                img = scale_image(scale)
                self.tk_tmp = img
                self.canvas.itemconfig(self.this_card, image=img)
                self.canvas.after(25, lambda: animate(step + 1))
            else:
                self.flipping = False

        animate(0)


def load_image(name, size):
    return ImageTk.PhotoImage(Image.open(os.path.join(CARD_FOLDER, name)).resize(size))


def key_pressed(event):
    k = event.keysym.lower()

    # actions = {
    #     "s": card_box.spread,
    #     "w": card_box.spread_sorted,
    #     "d": card_box.delete,
    #     "f": card_box.flash_all_cards,
    # }
    # suit_map = {"z": "spade", "x": "diamond", "c": "club", "v": "heart"}
    # value_map = {
    #     "a": 1,
    #     "1": 1,
    #     "2": 2,
    #     "3": 3,
    #     "4": 4,
    #     "5": 5,
    #     "6": 6,
    #     "7": 7,
    #     "8": 8,
    #     "9": 9,
    #     "0": 10,
    #     "j": 11,
    #     "q": 12,
    #     "k": 13,
    # }

    # if k in actions:
    #     actions[k]()
    # if k in suit_map:
    #     card_box.spread_suit(suit_map[k])
    # if k in value_map:
    #     card_box.spread_value(value_map[k])


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
    for f in os.listdir(CARD_FOLDER)
    if f.endswith(".png") and f not in ("box.png", "back.png")
]

Box(canvas, screen_w / 2, screen_h - 108, box_img, back_img, card_imgs)

root.bind("<Key>", key_pressed)
root.mainloop()

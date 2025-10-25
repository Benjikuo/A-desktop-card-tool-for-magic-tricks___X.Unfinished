import tkinter as tk
from PIL import Image, ImageTk
import os, random, math

BG_COLOR = "#09FF00"
IMAGE_FOLDER = "image/card"
CARD_SIZE = (74, 111)
BOX_SIZE = (80, 120)

RIBBON_SPACING = 20
WAVE_RANGE = 60
WAVE_HEIGHT = 15
WAVE_Y_THRESHOLD = 100
RIBBON_RISE_HEIGHT = 150

focused_card = None


class CardBox:
    def __init__(self, canvas, x, y, box_img, back_img, card_imgs):
        self.canvas = canvas
        self.x, self.y = x, y
        self.box_img = box_img
        self.back_img = back_img
        self.card_imgs = card_imgs.copy()
        self.used_cards = set()
        self.all_cards = []

        self.image_id = canvas.create_image(x, y, image=self.box_img, tags="box")
        canvas.tag_bind(self.image_id, "<Button-1>", self.spawn_card)

    def spawn_card(self, event=None):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 所有卡片都已生成完畢！")
            return
        img = random.choice(available)
        self.used_cards.add(img)
        card = Card(self.canvas, self.x, self.y, self.back_img, img, self)
        self.all_cards.append(card)


class Card:
    def __init__(
        self,
        canvas,
        x,
        y,
        back_img,
        front_img,
        box,
        skip_animation=False,
        is_ribbon=False,
    ):
        self.canvas = canvas
        self.back_img = back_img
        self.front_img = front_img
        self.box = box
        self.face_up = False
        self.image_id = canvas.create_image(x, y, image=self.back_img, tags="card")
        self.flipping = False
        self.ready = False
        self.destroyed = False
        self.is_ribbon = is_ribbon
        self.base_x = x
        self.base_y = y
        self.target_y = y
        self.touched = False
        self.rising = False
        self._drag_data = {"x": 0, "y": 0, "moved": False}
        self._press_pos = (0, 0)

        if skip_animation:
            self.ready = True
            self.bind_events()
        else:
            self.animate_up(0)

    def animate_up(self, step):
        if self.destroyed:
            return
        if step < 18:
            self.canvas.move(self.image_id, 0, -7)
            self.canvas.after(15, lambda: self.animate_up(step + 1))
        else:
            self.ready = True
            self.bind_events()

    def bind_events(self):
        self.canvas.tag_bind(self.image_id, "<ButtonPress-1>", self.start_drag)
        self.canvas.tag_bind(self.image_id, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.image_id, "<ButtonRelease-1>", self.stop_drag)

    def start_drag(self, event):
        global focused_card
        if not self.ready:
            return
        focused_card = self
        self._press_pos = (event.x, event.y)
        self._drag_data = {"x": event.x, "y": event.y, "moved": False}
        self.canvas.tag_raise(self.image_id)

    def on_drag(self, event):
        if not self.ready:
            return
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        if abs(dx) > 2 or abs(dy) > 2:
            self._drag_data["moved"] = True
        self.canvas.move(self.image_id, dx, dy)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def stop_drag(self, event):
        if not self.ready:
            return
        dist = math.hypot(event.x - self._press_pos[0], event.y - self._press_pos[1])
        if dist < 5 and not self._drag_data["moved"]:
            self.flip_animated()
        self._drag_data = {"x": 0, "y": 0, "moved": False}

    def flip_animated(self, step=0):
        if self.flipping or not self.ready:
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
                self.canvas.itemconfig(self.image_id, image=img)
                self.canvas.after(25, lambda: animate(step + 1))
            elif step == shrink_steps:
                self.face_up = not self.face_up
                self.canvas.itemconfig(
                    self.image_id,
                    image=self.front_img if self.face_up else self.back_img,
                )
                self.canvas.after(25, lambda: animate(step + 1))
            elif step <= total_steps:
                scale = (step - shrink_steps) / shrink_steps
                img = scale_image(scale)
                self.tk_tmp = img
                self.canvas.itemconfig(self.image_id, image=img)
                self.canvas.after(25, lambda: animate(step + 1))
            else:
                self.flipping = False

        animate(0)


def load_image(name, size):
    place = os.path.join(IMAGE_FOLDER, name)
    return ImageTk.PhotoImage(Image.open(place).resize(size))


def key_pressed(event):
    return


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
    if f.endswith(".png") and f not in ("box.png", "back.png")
]

card_box = CardBox(canvas, screen_w / 2, screen_h - 108, box_img, back_img, card_imgs)

root.bind("<Key>", key_pressed)
root.mainloop()

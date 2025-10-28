import tkinter as tk
from PIL import Image, ImageTk
import os, random, math

BG_COLOR = "#000000"
CARD_FOLDER = "image/card"
CARD_SIZE = (74, 111)
BOX_SIZE = (80, 120)

HANDLE_RADIUS = 20

RIBBON_SPACING = 20
SIMPLE_SPACING = 100
WAVE_RANGE = 60
WAVE_HEIGHT = 15
WAVE_Y_THRESHOLD = 100
RIBBON_RISE_HEIGHT = 150

focused_card = None
ribbon_spreads = []


class Drag:
    def __init__(self, canva, x, y, item_id, w=None, h=None):
        self.canva = canva
        self.item_id = item_id
        self.item_x, self.item_y = x, y
        self.start_x, self.start_y = 0, 0
        self.dx, self.dy = 0, 0
        self.draggable = True
        self.dragged = False
        self.w = w
        self.h = h

        self.canva.tag_bind(self.item_id, "<Button-1>", self.start_drag)
        self.canva.tag_bind(self.item_id, "<B1-Motion>", self.on_drag)
        self.canva.tag_bind(self.item_id, "<ButtonRelease-1>", self.stop_drag)
        self.canva.tag_bind(self.item_id, "<Button-2>", lambda e: self.middle_click(e))
        self.canva.tag_bind(self.item_id, "<Button-3>", lambda e: self.right_click(e))

    def start_drag(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.canva.tag_raise(self.item_id)

    def on_drag(self, event):
        if not self.draggable:
            return

        self.dx = event.x - self.start_x
        self.dy = event.y - self.start_y
        dist = math.hypot(self.dx, self.dy)
        if dist > 5:
            self.dragged = True
            x = self.item_x + self.dx
            y = self.item_y + self.dy
            if self.w and self.h:
                self.canva.coords(self.item_id, x, y, x + self.w, y + self.h)
            else:
                self.canva.coords(self.item_id, x, y)
        else:
            self.dragged = False

    def stop_drag(self, event):
        if self.dragged:
            self.item_x += self.dx
            self.item_y += self.dy
            self.dragged = False
        else:
            self.left_click(event)

    def left_click(self, event):
        pass

    def middle_click(self, event):
        pass

    def right_click(self, event):
        pass


class Box(Drag):
    def __init__(self, canva, x, y, box_img, back_img, card_imgs_names):
        self.box_img = box_img
        self.this_box = canva.create_image(x, y, image=self.box_img, tags="box")
        super().__init__(canva, x, y, self.this_box)
        self.initial_x, self.initial_y = x, y
        self.back_img = back_img
        self.card_imgs_names = card_imgs_names.copy()
        self.used_card_names = set()
        self.available = []

        self.left_click = self.spawn_card
        self.middle_click = self.reset_position
        self.right_click = self.create_spread

    def reset_position(self, event=None):
        self.item_x = self.initial_x
        self.item_y = self.initial_y
        self.canva.coords(self.item_id, self.item_x, self.item_y)

    def spawn_card(self, event=None):
        self.available = [
            name for name in self.card_imgs_names if name not in self.used_card_names
        ]
        if not self.available:
            print("⚠️ All cards have been generated!")
            return

        card_name = random.choice(self.available)
        front_img = load_image(card_name, CARD_SIZE)
        card = Card(
            self.canva,
            self,
            self.item_x,
            self.item_y,
            self.back_img,
            front_img,
            card_name,
        )
        self.used_card_names.add(card_name)
        self.canva.tag_raise(self.item_id)
        card.up()

    def take_card(self, card_name):
        if card_name not in self.used_card_names:
            self.used_card_names.add(card_name)

    def return_card(self, card_name):
        if card_name in self.used_card_names:
            self.used_card_names.remove(card_name)

    def create_spread(self, event=None):
        self.available = [
            name for name in self.card_imgs_names if name not in self.used_card_names
        ]
        if not self.available:
            print("⚠️ All cards have been generated!")
            return

        self.used_card_names.update(self.available)
        Group(self.canva, self, self.back_img, self.available)


class Group(Drag):
    def __init__(self, canva, box, back_img, cards):
        x = box.item_x - 100
        y = box.item_y
        self.w = CARD_SIZE[0] / 4
        self.h = CARD_SIZE[1]
        self.this_group = canva.create_rectangle(
            x,
            y,
            x + self.w,
            y + self.h,
            fill="#333333",
            outline="#444444",
            width=3,
            tags="group_handle",
        )
        super().__init__(canva, x, y, self.this_group, self.w, self.h)
        self.box = box
        self.back_img = back_img
        self.cards = cards

        self.middle_click = self.delete_group

    def delete_group(self, event=None):
        for card_name in self.cards:
            self.box.return_card(card_name)
        self.box.canva.delete(self.item_id)

    # 建立排列 (cards_names 為卡片檔名清單)
    def create(self, cards_names, start_x, start_y):
        total_width = CARD_SIZE[0] + (len(cards_names) - 1) * RIBBON_SPACING
        self.handle_x = start_x - CARD_SIZE[0] // 2 - HANDLE_RADIUS - 10
        self.handle_y = start_y

        # 逐張生成卡片
        for i, name in enumerate(cards_names):
            if name not in self.box.used_card_names:
                self.box.used_card_names.add(name)
            front_img = load_image(name, CARD_SIZE)
            x = start_x + i * RIBBON_SPACING
            y = start_y
            self.canva.after(
                i * 40,
                lambda n=name, x=x, y=y, f=front_img: self._spawn_card(f, n, x, y),
            )

    # 建立單張卡
    def _spawn_card(self, front_img, name, x, y):
        card = Card(self.canva, self.box, x, y, self.back_img, front_img, name)
        self.cards.append(card)

    # 橫向展開 (spread)
    def spread(self):
        if not self.cards:
            print("⚠️ No cards to spread.")
            return
        total = len(self.cards)
        screen_w = self.canva.winfo_width()
        start_x = (screen_w - (CARD_SIZE[0] + (total - 1) * SIMPLE_SPACING)) // 2
        y = self.cards[0].item_y
        for i, card in enumerate(self.cards):
            target_x = start_x + i * SIMPLE_SPACING
            self._move_card_to(card, target_x, y)

    def _move_card_to(self, card, target_x, target_y, step=0):
        cx, cy = self.canva.coords(card.this_card)
        dx = (target_x - cx) / 5
        dy = (target_y - cy) / 5
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            self.canva.coords(card.this_card, target_x, target_y)
            card.item_x, card.item_y = target_x, target_y
            return
        self.canva.move(card.this_card, dx, dy)
        self.canva.after(
            16, lambda: self._move_card_to(card, target_x, target_y, step + 1)
        )

    # 彩帶排列 (ribbon_wave)
    def ribbon_wave(self):
        if not self.cards:
            return
        for i, card in enumerate(self.cards):
            offset = math.sin(i / 2) * 25
            self.canva.coords(card.this_card, card.item_x, card.item_y - offset)

    # 根據滑鼠波動 (互動)
    def update_wave(self, event):
        for i, card in enumerate(self.cards):
            dx = abs(event.x - card.item_x)
            offset = 20 * math.exp(-(dx**2) / 2000)
            self.canva.coords(card.this_card, card.item_x, card.item_y - offset)


class Card(Drag):
    def __init__(
        self,
        canva,
        box,
        x,
        y,
        back_img,
        front_img,
        card_name,
        in_spread=False,
    ):
        self.back_img = back_img
        self.front_img = front_img
        self.this_card = canva.create_image(x, y, image=self.back_img, tags="card")
        super().__init__(canva, x, y, self.this_card)
        self.box = box
        self.card_name = card_name
        self.flipping = False
        self.face_up = False
        self.in_spread = in_spread

        self.left_click = self.flip
        self.middle_click = self.delete

    def up(self):
        total_steps = 12
        height = 130

        def animate_up(step):
            if self.dragged:
                return

            if step < total_steps:
                self.item_x += 0
                self.item_y -= height / total_steps
                self.canva.coords(self.item_id, self.item_x, self.item_y)
                self.canva.after(10, lambda: animate_up(step + 1))

        animate_up(0)

    def flip(self, event=None):
        if self.flipping:
            return

        if self.in_spread:
            self.in_spread = False
            self.up()
            self.flip()

        self.flipping = True
        total_steps = 16
        shrink_steps = total_steps / 2

        def scale_image(scale):
            img = self.front_img if self.face_up else self.back_img
            pil = ImageTk.getimage(img)
            w, h = pil.size
            new_w = max(1, int(w * scale))
            resized = pil.resize((new_w, h))
            return ImageTk.PhotoImage(resized)

        def animate_scale(step):
            if step < shrink_steps:
                scale = (shrink_steps - step) / shrink_steps
                img = scale_image(scale)
                self.img = img  # type: ignore
                self.canva.itemconfig(self.this_card, image=img)
            elif step == shrink_steps:
                self.face_up = not self.face_up
            elif step <= total_steps:
                scale = (step - shrink_steps) / shrink_steps
                img = scale_image(scale)
                self.img = img  # type: ignore
                self.canva.itemconfig(self.this_card, image=img)
            else:
                self.flipping = False
                return

            self.canva.after(10, lambda: animate_scale(step + 1))

        animate_scale(0)

    def delete(self, event=None):
        star_effect(self.canva, self.item_x, self.item_y)
        self.canva.delete(self.this_card)
        self.box.return_card(self.card_name)

    def update_wave(self, mouse_y):
        dy = abs(self.base_y - mouse_y)
        if dy < 100:
            offset = 15 * math.exp(-(dy**2) / 4000)
            self.target_y = self.base_y - offset
        else:
            self.target_y = self.base_y

    def move_toward_target(self):
        current_x, current_y = self.canva.coords(self.this_card)
        diff = self.target_y - current_y
        if abs(diff) > 0.5:
            self.canva.move(self.this_card, 0, diff * self.wave_speed)


def star_effect(canva, x, y, count=10):
    stars_group = []
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(10, 70)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        star = canva.create_text(
            x,
            y,
            text="✦",
            fill=random.choice(["#FFFB00", "#FFDD33", "#FFFF99"]),
            font=("Arial", random.randint(9, 11)),
        )
        stars_group.append(star)
        move_star(canva, star, dx, dy, 0)
        delay = random.randint(500, 1000)
        canva.after(delay, lambda s=star: canva.delete(s))


def move_star(canva, star, dx, dy, step):
    if step > 80:
        return

    canva.move(star, dx / (10 + step * 2), dy / (10 + step * 2))
    canva.after(10, lambda: move_star(canva, star, dx, dy, step + 1))


"""
    def _handle_click(self, event):
        if not self.ready or self.rising:
            return
        self.flip()

    def _handle_left_press(self, event):
        global focused_card
        if not self.ready:
            return
        focused_card = self
        if self.is_ribbon and not self.touched:
            self.rising = True
            self.ribbon_rise()
            if not self.face_up:
                self.canva.after(300, self.flip)
        self.touched = True
        super()._handle_left_press(event)

    def ribbon_rise(self):
        current_x, current_y = self.canva.coords(self.image_id)
        target_y = current_y - RIBBON_RISE_HEIGHT
        self._animate_rise(current_x, current_y, target_y, 0)

    def _animate_rise(self, base_x, start_y, target_y, step):
        steps = 10
        if step < steps:
            progress = step / steps
            new_y = start_y + (target_y - start_y) * progress
            current_x, _ = self.canva.coords(self.image_id)
            self.canva.coords(self.image_id, current_x, new_y)
            self.canva.after(
                20, lambda: self._animate_rise(base_x, start_y, target_y, step + 1)
            )
        else:
            self.base_y = target_y
            self.rising = False

    def delete(self, event=None):
        global focused_card
        if not self.ready or self.destroyed:
            return
        self.destroyed = True
        x, y = self.canva.coords(self.image_id)
        # star_effect(self.canva, x, y)
        self.canva.delete(self.image_id)
        self.box.used_cards.discard(self.front_img)
        focused_card = None


def spread_wave():
    for card in group.all_cards:
        if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
            current_x, current_y = canva.coords(card.image_id)
            diff = card.target_y - current_y
            if abs(diff) > 0.5:
                new_y = current_y + diff * 0.3
                canva.coords(card.image_id, current_x, new_y)
    canva.after(16, spread_wave)


def update_wave(event):
    mouse_x = event.x
    mouse_y = event.y
    for card in group.all_cards:
        if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
            dy = abs(card.base_y - mouse_y)
            if dy > WAVE_Y_THRESHOLD:
                card.target_y = card.base_y
            else:
                dx = abs(card.base_x - mouse_x)
                if dx < WAVE_RANGE:
                    offset = WAVE_HEIGHT * math.exp(
                        -(dx**2) / (2 * (WAVE_RANGE / 2) ** 2)
                    )
                    card.target_y = card.base_y - offset
                else:
                    card.target_y = card.base_y


def reset_wave(event=None):
    for card in group.all_cards:
        if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
            card.target_y = card.base_y


def star_effect(canva, x, y, count=15):
    stars = []
    for _ in range(count):
        dx, dy = random.randint(-40, 40), random.randint(-40, 40)
        star = canva.create_text(
            x,
            y,
            text="✦",
            fill=random.choice(["#FFD700", "#FFCC33", "#FFFF99"]),
            font=("Arial", 10),
        )
        stars.append(star)
        move_star(canva, star, dx, dy, 0)
    canva.after(1000, lambda: [canva.delete(s) for s in stars])


def move_star(canva, star, dx, dy, step):
    canva.move(star, dx / (10 + step * 2), dy / (10 + step * 2))
    canva.after(20, lambda: move_star(canva, star, dx, dy, step + 1))


def reset(event=None):
    global focused_card
    for card in group.all_cards:
        card.destroyed = True
    for item in canva.find_withtag("card"):
        canva.delete(item)
    for item in canva.find_withtag("ribbon_handle"):
        canva.delete(item)
    group.used_cards.clear()
    group.all_cards.clear()
    ribbon_spreads.clear()
    focused_card = None


def delete_all(event=None):
    global focused_card
    for item in canva.find_withtag("card"):
        x, y = canva.coords(item)
        star_effect(canva, x, y)
        canva.delete(item)
    for item in canva.find_withtag("ribbon_handle"):
        canva.delete(item)
    group.used_cards.clear()
    group.all_cards.clear()
    ribbon_spreads.clear()
    focused_card = None


def flip_all(event=None):
    cards = [c for c in group.all_cards if c.ready and not c.destroyed]
    if not cards:
        return
    all_face_up = all(c.face_up for c in cards)
    target_state = not all_face_up
    for card in cards:
        if card.face_up != target_state:
            card.flip_animated()
            """


def load_image(name, size):
    place = os.path.join(CARD_FOLDER, name)
    return ImageTk.PhotoImage(Image.open(place).resize(size))


def key_pressed(event):
    key = event.keysym.lower()
    ctrl = (event.state & 0x4) != 0

    # sortcut
    # shortcuts = {
    #     "w": group.ribbon_spread_sorted,
    #     "s": group.ribbon_spread,
    #     "r": reset,
    #     "t": spawn_random_card,
    #     "d": destroy,
    #     "f": flip,
    # }
    # ctrl_shortcuts = {
    #     "d": delete_all,
    #     "f": flip_all,
    #     "s": group.ribbon_spread,
    # }
    # func = (ctrl_shortcuts if ctrl else shortcuts).get(key)
    # if func:
    #     func()
    #     return

    # suit group
    # suit_map = {"z": "spade", "x": "diamond", "c": "club", "v": "heart"}
    # if key in suit_map:
    #     group.ribbon_spread_by_suit(suit_map[key])
    #     return

    # value group
    # value = None
    # if key == "a":
    #     value = 1
    # elif key == "0":
    #     value = 10
    # elif key == "j":
    #     value = 11
    # elif key == "q":
    #     value = 12
    # elif key == "k":
    #     value = 13
    # elif key.isdigit():
    #     value = int(key)

    # if value:
    #     group.spawn_cards_by_value(value)


root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-transparentcolor", BG_COLOR)

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.geometry(f"{screen_w}x{screen_h}+0+0")
canva = tk.Canvas(
    root, width=screen_w, height=screen_h, bg=BG_COLOR, highlightthickness=0
)
canva.pack(fill="both", expand=True)

box_img = load_image("box.png", BOX_SIZE)
back_img = load_image("back.png", CARD_SIZE)
card_imgs_names = [
    f
    for f in os.listdir(CARD_FOLDER)
    if f.endswith(".png") and f not in ("box.png", "back.png")
]

Box(canva, screen_w / 2, screen_h - 108, box_img, back_img, card_imgs_names)

# root.bind("<Motion>", update_wave)
# root.bind("<Leave>", reset_wave)
root.bind("<Key>", key_pressed)

# spread_wave()
root.mainloop()

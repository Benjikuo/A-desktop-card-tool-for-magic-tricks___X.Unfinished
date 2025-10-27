import tkinter as tk
from PIL import Image, ImageTk
import os, random, math

BG_COLOR = "#00FF00"
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
    def __init__(self, canvas, x, y, item_name):
        self.canvas = canvas
        self.item = item_name
        self.item_x = x
        self.item_y = y
        self.start_x = None
        self.start_y = None
        self.moved = False

        self.canvas.tag_bind(self.item, "<Button-1>", self._start_drag)
        self.canvas.tag_bind(self.item, "<B1-Motion>", self._on_drag)
        self.canvas.tag_bind(self.item, "<ButtonRelease-1>", self._stop_drag)

    def _start_drag(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def _on_drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        dist = math.hypot(dx, dy)
        if dist > 5:
            self._moved = True
            self.item_x = self.start_x + dx
            self.item_y = self.start_y + dy

    def _stop_drag(self, event):
        if self.moved:
            self.moved = False
        else:
            self.on_left_click()

    def on_left_click(self):
        pass


"""
class Group:
    def __init__(self, canva, cards, back_img, box):
        self.canva = canva
        self.cards = cards
        self.back_img = back_img
        self.box = box
        self.card_objects = []
        self.handle_id = None
        self.handle_x = 0
        self.handle_y = 0
        self._drag_data = {"x": 0, "y": 0}

    def create(self, start_x, start_y):
        self.handle_x = start_x - CARD_SIZE[0] // 2 - HANDLE_RADIUS - 10
        self.handle_y = start_y
        self.handle_id = self.canva.create_oval(
            self.handle_x - HANDLE_RADIUS,
            self.handle_y - HANDLE_RADIUS,
            self.handle_x + HANDLE_RADIUS,
            self.handle_y + HANDLE_RADIUS,
            fill="#FF8C00",
            outline="#FF6600",
            width=3,
            tags="ribbon_handle",
        )
        self.canva.tag_bind(self.handle_id, "<ButtonPress-1>", self._start_drag_group)
        self.canva.tag_bind(self.handle_id, "<B1-Motion>", self._drag_group)
        self.canva.tag_bind(self.handle_id, "<ButtonRelease-1>", self._stop_drag_group)
        for i, img in enumerate(self.cards):
            x = start_x + i * RIBBON_SPACING
            y = start_y
            delay = i * 50
            self.canva.after(
                delay, lambda img=img, x=x, y=y: self._spawn_card(img, x, y)
            )

    def _spawn_card(self, img, x, y):
        self.box.used_cards.add(img)
        card = Card(
            self.canva,
            x,
            y,
            self.back_img,
            img,
            self.box,
            skip_animation=True,
            is_ribbon=True,
        )
        self.card_objects.append(card)
        self.box.all_cards.append(card)

    def get_filename_for_img(self, img):
        img_str = str(img)
        for i, card_img in enumerate(self.card_imgs):
            if str(card_img) == img_str:
                return self.card_filenames[i]
        return ""

    def get_card_sort_key(self, img):
        filename = self.get_filename_for_img(img)
        if not filename:
            return (99, 99)
        name = filename.replace(".png", "").lower()
        if "joker" in name:
            if "1" in name:
                return (0, 0)
            else:
                return (4, 14)
        suit_order = {"spade": 1, "diamond": 2, "club": 3, "heart": 4}
        suit = 5
        for s in suit_order:
            if s in name:
                suit = suit_order[s]
                break
        rank = 0
        parts = name.split("-")
        if len(parts) == 2:
            try:
                rank = int(parts[1].replace("(", "").replace(")", ""))
            except:
                rank = 0
        return (suit, rank)

    def spawn_cards_by_value(self, rank):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 所有卡片都已生成完畢！")
            return
        filtered = []
        for img in available:
            filename = self.get_filename_for_img(img)
            if filename:
                name = filename.replace(".png", "").lower()
                if "joker" in name:
                    continue
                parts = name.split("-")
                if len(parts) == 2:
                    try:
                        card_rank = int(parts[1].replace("(", "").replace(")", ""))
                        if card_rank == rank:
                            filtered.append(img)
                    except:
                        pass
        if not filtered:
            print(f"⚠️ 沒有可用的數字 {rank} 卡片！")
            return
        sorted_cards = sorted(filtered, key=self.get_card_sort_key)
        total_width = CARD_SIZE[0] + (len(sorted_cards) - 1) * SIMPLE_SPACING
        screen_w = self.canva.winfo_width()
        screen_h = self.canva.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1
        for i, img in enumerate(sorted_cards):
            x = start_x + i * SIMPLE_SPACING
            y = start_y
            delay = i * 100
            self.canva.after(
                delay, lambda img=img, x=x, y=y: self._spawn_simple_card(img, x, y)
            )

    def _spawn_simple_card(self, img, x, y):
        self.used_cards.add(img)
        card = Card(self.canva, x, y, self.back_img, img, self, skip_animation=True)
        self.all_cards.append(card)

    def ribbon_spread_sorted(self):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 所有卡片都已生成完畢！")
            return
        filtered = [
            img
            for img in available
            if "joker" not in self.get_filename_for_img(img).lower()
        ]
        if not filtered:
            print("⚠️ 沒有可用的卡片！")
            return
        sorted_cards = sorted(filtered, key=self.get_card_sort_key)
        total_width = CARD_SIZE[0] + (len(sorted_cards) - 1) * RIBBON_SPACING
        screen_w = self.canva.winfo_width()
        screen_h = self.canva.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1
        ribbon = Group(self.canva, sorted_cards, self.back_img, self)
        ribbon.create(start_x, start_y)
        ribbon_spreads.append(ribbon)

    def ribbon_spread_by_suit(self, suit_name):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 所有卡片都已生成完畢！")
            return
        suit_map = {"spade": 1, "diamond": 2, "club": 3, "heart": 4}
        target_suit = suit_map.get(suit_name, 0)
        filtered = []
        for img in available:
            filename = self.get_filename_for_img(img)
            if "joker" in filename.lower():
                continue
            suit, rank = self.get_card_sort_key(img)
            if suit == target_suit:
                filtered.append(img)
        if not filtered:
            print(f"⚠️ 沒有可用的{suit_name}卡片！")
            return
        sorted_cards = sorted(filtered, key=lambda img: self.get_card_sort_key(img)[1])
        total_width = CARD_SIZE[0] + (len(sorted_cards) - 1) * RIBBON_SPACING
        screen_w = self.canva.winfo_width()
        screen_h = self.canva.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1
        ribbon = Group(self.canva, sorted_cards, self.back_img, self)
        ribbon.create(start_x, start_y)
        ribbon_spreads.append(ribbon)

    def ribbon_spread(self):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 所有卡片都已生成完畢！")
            return
        filtered = [
            img
            for img in available
            if "joker" not in self.get_filename_for_img(img).lower()
        ]
        if not filtered:
            print("⚠️ 沒有可用的卡片！")
            return
        shuffled = filtered.copy()
        random.shuffle(shuffled)
        total_width = CARD_SIZE[0] + (len(shuffled) - 1) * RIBBON_SPACING
        screen_w = self.canva.winfo_width()
        screen_h = self.canva.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1
        ribbon = Group(self.canva, shuffled, self.back_img, self)
        ribbon.create(start_x, start_y)
        ribbon_spreads.append(ribbon)
"""

"""
class Box(Drag):
    def __init__(self, canva, x, y, box_img, back_img, card_imgs, card_filenames):
        super().__init__(self, canva)
        self.initial_x = x
        self.initial_y = y
        self.x, self.y = x, y
        self.box_img = box_img
        self.back_img = back_img
        self.card_imgs = card_imgs.copy()
        self.card_filenames = card_filenames.copy()
        self.used_cards = set()
        self.all_cards = []
        self.image_id = canva.create_image(x, y, image=self.box_img, tags="box")
        self.setup_drag(canva, self.image_id)
        self.left_click(self.spawn_card)
        self.set_on_middle_click(self.reset_position)

    def reset_position(self, event=None):
        current_x, current_y = self.canva.coords(self.image_id)
        self.canva.move(
            self.image_id, self.initial_x - current_x, self.initial_y - current_y
        )

    def spawn_card(self, event=None):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 所有卡片都已生成完畢！")
            return
        img = random.choice(available)
        self.used_cards.add(img)
        box_coords = self.canva.coords(self.image_id)
        card = Card(self.canva, box_coords[0], box_coords[1], self.back_img, img, self)
        self.all_cards.append(card)
"""


class Card(Drag):
    def __init__(
        self,
        canva,
        x,
        y,
        back_img,
        front_img,
        # box,
        # skip_animation=False,
        # is_ribbon=False,
    ):
        super().__init__(canva, x, y, "card")  # type: ignore
        self.back_img = back_img
        self.front_img = front_img
        # self.box = box
        self.face_up = False
        # self.image_id = canva.create_image(x, y, image=self.back_img, tags="card")
        # self.canva = canva
        # self.canva.tag_lower(self.image_id, "box")
        # self.flipping = False
        # self.ready = False
        # self.destroyed = False
        # self.is_ribbon = is_ribbon
        # self.base_x = x
        # self.base_y = y
        # self.target_y = y
        # self.touched = False
        # self.rising = False
        # if skip_animation:
        #     self.ready = True
        #     self.bind_events()
        # else:
        #     self.animate_up(0)

        self.on_left_click = self.flip

    def flip(self):
        # if self.flipping or not self.ready:
        #     return
        self.flipping = True
        total_steps = 10
        shrink_steps = total_steps // 2
        print("it workds")

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
                self.tk_tmp = img  # type: ignore
                self.canva.itemconfig(self.image_id, image=img)
                self.canva.after(25, lambda: animate(step + 1))
            elif step == shrink_steps:
                self.canva.update_idletasks()
                self.face_up = not self.face_up
                self.canva.itemconfig(
                    self.image_id,
                    image=self.front_img if self.face_up else self.back_img,
                )
                self.canva.after(25, lambda: animate(step + 1))
            elif step <= total_steps:
                scale = (step - shrink_steps) / shrink_steps
                img = scale_image(scale)
                self.tk_tmp = img  # type: ignore
                self.canva.itemconfig(self.image_id, image=img)
                self.canva.after(25, lambda: animate(step + 1))
            else:
                self.flipping = False

        animate(0)


"""
    def animate_up(self, step):
        if self.destroyed:
            return
        if step < 18:
            self.canva.move(self.image_id, 0, -7)
            self.canva.after(15, lambda: self.animate_up(step + 1))
        else:
            self.ready = True
            self.bind_events()

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
        star_effect(self.canva, x, y)
        self.canva.delete(self.image_id)
        self.box.used_cards.discard(self.front_img)
        if focused_card == self:
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
card_imgs = [
    load_image(f, CARD_SIZE)
    for f in os.listdir(CARD_FOLDER)
    if f.endswith(".png") and f not in ("box.png", "back.png")
]

card_filenames = [
    f
    for f in os.listdir(CARD_FOLDER)
    if f.endswith(".png") and f not in ("box.png", "back.png")
]

a = Card(canva, 300, 400, back_img)

# group = Box(
# canva, screen_w / 2, screen_h - 108, box_img, back_img, card_imgs, card_filenames
# )

# root.bind("<Motion>", update_wave)
# root.bind("<Leave>", reset_wave)
root.bind("<Key>", key_pressed)

# spread_wave()
root.mainloop()

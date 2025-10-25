import tkinter as tk
from PIL import Image, ImageTk
import os, random, math

BG_COLOR = "#09FF00"
IMAGE_FOLDER = "image/card"
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


class Draggable:
    def __init__(self):
        self._drag_data = {"x": 0, "y": 0, "start_x": 0, "start_y": 0, "moved": False}
        self._on_left_click = None
        self._on_middle_click = None
        self._on_right_click = None
        self._on_drag_move = None

    def setup_drag(self, canvas, image_id):
        self.canvas = canvas
        self.image_id = image_id
        canvas.tag_bind(image_id, "<ButtonPress-1>", self._handle_left_press)
        canvas.tag_bind(image_id, "<B1-Motion>", self._handle_drag)
        canvas.tag_bind(image_id, "<ButtonRelease-1>", self._handle_left_release)
        canvas.tag_bind(image_id, "<Button-2>", self._handle_middle_click)
        canvas.tag_bind(image_id, "<Button-3>", self._handle_right_click)

    def set_on_left_click(self, callback):
        self._on_left_click = callback

    def set_on_middle_click(self, callback):
        self._on_middle_click = callback

    def set_on_right_click(self, callback):
        self._on_right_click = callback

    def set_on_drag_move(self, callback):
        self._on_drag_move = callback

    def _handle_left_press(self, event):
        self._drag_data = {
            "x": event.x,
            "y": event.y,
            "start_x": event.x,
            "start_y": event.y,
            "moved": False,
        }
        self.canvas.tag_raise(self.image_id)

    def _handle_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]

        if abs(dx) > 2 or abs(dy) > 2:
            self._drag_data["moved"] = True

        self.canvas.move(self.image_id, dx, dy)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

        if self._on_drag_move:
            self._on_drag_move(dx, dy)

    def _handle_left_release(self, event):
        dist = math.hypot(
            event.x - self._drag_data["start_x"], event.y - self._drag_data["start_y"]
        )

        if dist < 5 and not self._drag_data["moved"]:
            if self._on_left_click:
                self._on_left_click(event)

        self._drag_data = {"x": 0, "y": 0, "start_x": 0, "start_y": 0, "moved": False}

    def _handle_middle_click(self, event):
        if self._on_middle_click:
            self._on_middle_click(event)

    def _handle_right_click(self, event):
        if self._on_right_click:
            self._on_right_click(event)


class RibbonSpread:
    def __init__(self, canvas, cards, back_img, box):
        self.canvas = canvas
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

        self.handle_id = self.canvas.create_oval(
            self.handle_x - HANDLE_RADIUS,
            self.handle_y - HANDLE_RADIUS,
            self.handle_x + HANDLE_RADIUS,
            self.handle_y + HANDLE_RADIUS,
            fill="#FF8C00",
            outline="#FF6600",
            width=3,
            tags="ribbon_handle",
        )

        self.canvas.tag_bind(self.handle_id, "<ButtonPress-1>", self._start_drag_group)
        self.canvas.tag_bind(self.handle_id, "<B1-Motion>", self._drag_group)
        self.canvas.tag_bind(self.handle_id, "<ButtonRelease-1>", self._stop_drag_group)

        for i, img in enumerate(self.cards):
            x = start_x + i * RIBBON_SPACING
            y = start_y
            delay = i * 50
            self.canvas.after(
                delay, lambda img=img, x=x, y=y: self._spawn_card(img, x, y)
            )

    def _spawn_card(self, img, x, y):
        self.box.used_cards.add(img)
        card = Card(
            self.canvas,
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

    def _start_drag_group(self, event):
        self._drag_data = {"x": event.x, "y": event.y}
        self.canvas.tag_raise(self.handle_id)

    def _drag_group(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]

        self.canvas.move(self.handle_id, dx, dy)
        self.handle_x += dx
        self.handle_y += dy

        for card in self.card_objects:
            if not card.destroyed:
                self.canvas.move(card.image_id, dx, dy)
                card.base_x += dx
                card.base_y += dy
                card.target_y += dy

        self._drag_data = {"x": event.x, "y": event.y}

    def _stop_drag_group(self, event):
        self._drag_data = {"x": 0, "y": 0}


class CardBox(Draggable):
    def __init__(self, canvas, x, y, box_img, back_img, card_imgs, card_filenames):
        super().__init__()
        self.initial_x = x
        self.initial_y = y
        self.x, self.y = x, y
        self.box_img = box_img
        self.back_img = back_img
        self.card_imgs = card_imgs.copy()
        self.card_filenames = card_filenames.copy()
        self.used_cards = set()
        self.all_cards = []

        self.image_id = canvas.create_image(x, y, image=self.box_img, tags="box")
        self.setup_drag(canvas, self.image_id)
        self.set_on_left_click(self.spawn_card)
        self.set_on_middle_click(self.reset_position)

    def reset_position(self, event=None):
        current_x, current_y = self.canvas.coords(self.image_id)
        self.canvas.move(
            self.image_id, self.initial_x - current_x, self.initial_y - current_y
        )

    def spawn_card(self, event=None):
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 所有卡片都已生成完畢！")
            return
        img = random.choice(available)
        self.used_cards.add(img)
        box_coords = self.canvas.coords(self.image_id)
        card = Card(self.canvas, box_coords[0], box_coords[1], self.back_img, img, self)
        self.all_cards.append(card)

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

    def spawn_cards_by_rank(self, rank):
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
        screen_w = self.canvas.winfo_width()
        screen_h = self.canvas.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1

        for i, img in enumerate(sorted_cards):
            x = start_x + i * SIMPLE_SPACING
            y = start_y
            delay = i * 100
            self.canvas.after(
                delay, lambda img=img, x=x, y=y: self._spawn_simple_card(img, x, y)
            )

    def _spawn_simple_card(self, img, x, y):
        self.used_cards.add(img)
        card = Card(self.canvas, x, y, self.back_img, img, self, skip_animation=True)
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
        screen_w = self.canvas.winfo_width()
        screen_h = self.canvas.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1

        ribbon = RibbonSpread(self.canvas, sorted_cards, self.back_img, self)
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
        screen_w = self.canvas.winfo_width()
        screen_h = self.canvas.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1

        ribbon = RibbonSpread(self.canvas, sorted_cards, self.back_img, self)
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
        screen_w = self.canvas.winfo_width()
        screen_h = self.canvas.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1

        ribbon = RibbonSpread(self.canvas, shuffled, self.back_img, self)
        ribbon.create(start_x, start_y)
        ribbon_spreads.append(ribbon)


class Card(Draggable):
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
        super().__init__()
        self.back_img = back_img
        self.front_img = front_img
        self.box = box
        self.face_up = False
        self.image_id = canvas.create_image(x, y, image=self.back_img, tags="card")
        self.canvas = canvas
        self.canvas.tag_lower(self.image_id, "box")
        self.flipping = False
        self.ready = False
        self.destroyed = False
        self.is_ribbon = is_ribbon
        self.base_x = x
        self.base_y = y
        self.target_y = y
        self.touched = False
        self.rising = False

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
        self.setup_drag(self.canvas, self.image_id)
        self.set_on_left_click(self._handle_click)
        self.set_on_middle_click(self.destroy)

    def _handle_click(self, event):
        if not self.ready or self.rising:
            return
        self.flip_animated()

    def _handle_left_press(self, event):
        global focused_card
        if not self.ready:
            return
        focused_card = self

        if self.is_ribbon and not self.touched:
            self.rising = True
            self.ribbon_rise()
            if not self.face_up:
                self.canvas.after(300, self.flip_animated)

        self.touched = True
        super()._handle_left_press(event)

    def ribbon_rise(self):
        current_x, current_y = self.canvas.coords(self.image_id)
        target_y = current_y - RIBBON_RISE_HEIGHT
        self._animate_rise(current_x, current_y, target_y, 0)

    def _animate_rise(self, base_x, start_y, target_y, step):
        steps = 10
        if step < steps:
            progress = step / steps
            new_y = start_y + (target_y - start_y) * progress
            current_x, _ = self.canvas.coords(self.image_id)
            self.canvas.coords(self.image_id, current_x, new_y)
            self.canvas.after(
                20, lambda: self._animate_rise(base_x, start_y, target_y, step + 1)
            )
        else:
            self.base_y = target_y
            self.rising = False

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
                self.canvas.update_idletasks()
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

    def destroy(self, event=None):
        global focused_card
        if not self.ready or self.destroyed:
            return
        self.destroyed = True
        x, y = self.canvas.coords(self.image_id)
        star_effect(self.canvas, x, y)
        self.canvas.delete(self.image_id)
        self.box.used_cards.discard(self.front_img)
        if focused_card == self:
            focused_card = None


def delete(event=None):
    global focused_card
    if focused_card and focused_card.ready:
        focused_card.destroy()


def flip(event=None):
    if focused_card and focused_card.ready:
        focused_card.flip_animated()


def flip_all(event=None):
    cards = [c for c in card_box.all_cards if c.ready and not c.destroyed]
    if not cards:
        return
    all_face_up = all(c.face_up for c in cards)
    target_state = not all_face_up
    for card in cards:
        if card.face_up != target_state:
            card.flip_animated()


def delete_all(event=None):
    global focused_card
    for item in canvas.find_withtag("card"):
        x, y = canvas.coords(item)
        star_effect(canvas, x, y)
        canvas.delete(item)
    for item in canvas.find_withtag("ribbon_handle"):
        canvas.delete(item)
    card_box.used_cards.clear()
    card_box.all_cards.clear()
    ribbon_spreads.clear()
    focused_card = None


def reset(event=None):
    global focused_card
    for card in card_box.all_cards:
        card.destroyed = True
    for item in canvas.find_withtag("card"):
        canvas.delete(item)
    for item in canvas.find_withtag("ribbon_handle"):
        canvas.delete(item)
    card_box.used_cards.clear()
    card_box.all_cards.clear()
    ribbon_spreads.clear()
    focused_card = None


def spread(event=None):
    card_box.ribbon_spread()


def spread_sorted(event=None):
    card_box.ribbon_spread_sorted()


def spread_spade(event=None):
    card_box.ribbon_spread_by_suit("spade")


def spread_diamond(event=None):
    card_box.ribbon_spread_by_suit("diamond")


def spread_club(event=None):
    card_box.ribbon_spread_by_suit("club")


def spread_heart(event=None):
    card_box.ribbon_spread_by_suit("heart")


def spawn_rank_1(event=None):
    card_box.spawn_cards_by_rank(1)


def spawn_rank_2(event=None):
    card_box.spawn_cards_by_rank(2)


def spawn_rank_3(event=None):
    card_box.spawn_cards_by_rank(3)


def spawn_rank_4(event=None):
    card_box.spawn_cards_by_rank(4)


def spawn_rank_5(event=None):
    card_box.spawn_cards_by_rank(5)


def spawn_rank_6(event=None):
    card_box.spawn_cards_by_rank(6)


def spawn_rank_7(event=None):
    card_box.spawn_cards_by_rank(7)


def spawn_rank_8(event=None):
    card_box.spawn_cards_by_rank(8)


def spawn_rank_9(event=None):
    card_box.spawn_cards_by_rank(9)


def spawn_rank_10(event=None):
    card_box.spawn_cards_by_rank(10)


def spawn_rank_11(event=None):
    card_box.spawn_cards_by_rank(11)


def spawn_rank_12(event=None):
    card_box.spawn_cards_by_rank(12)


def spawn_rank_13(event=None):
    card_box.spawn_cards_by_rank(13)


def update_wave(event):
    mouse_x = event.x
    mouse_y = event.y
    for card in card_box.all_cards:
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


def smooth_wave_animation():
    for card in card_box.all_cards:
        if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
            current_x, current_y = canvas.coords(card.image_id)
            diff = card.target_y - current_y
            if abs(diff) > 0.5:
                new_y = current_y + diff * 0.3
                canvas.coords(card.image_id, current_x, new_y)
    canvas.after(16, smooth_wave_animation)


def reset_wave(event=None):
    for card in card_box.all_cards:
        if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
            card.target_y = card.base_y


def load_image(path, size):
    img = Image.open(path).resize(size)
    return ImageTk.PhotoImage(img)


def star_effect(canvas, x, y, count=15):
    stars = []
    for _ in range(count):
        dx, dy = random.randint(-40, 40), random.randint(-40, 40)
        star = canvas.create_text(
            x,
            y,
            text="✦",
            fill=random.choice(["#FFD700", "#FFCC33", "#FFFF99"]),
            font=("Arial", 10),
        )
        stars.append(star)
        move_star(canvas, star, dx, dy, 0)
    canvas.after(1000, lambda: [canvas.delete(s) for s in stars])


def move_star(canvas, star, dx, dy, step):
    canvas.move(star, dx / (10 + step * 2), dy / (10 + step * 2))
    canvas.after(20, lambda: move_star(canvas, star, dx, dy, step + 1))


def key_pressed(event):
    key = event.keysym.lower()
    ctrl = (event.state & 0x4) != 0

    if not ctrl:
        if key == "r":
            reset()
        elif key == "s":
            spread()
        elif key == "w":
            spread_sorted()
        elif key == "d":
            delete()
        elif key == "f":
            flip()
        elif key == "z":
            spread_spade()
        elif key == "x":
            spread_diamond()
        elif key == "c":
            spread_club()
        elif key == "v":
            spread_heart()
        elif key == "1":
            spawn_rank_1()
        elif key == "2":
            spawn_rank_2()
        elif key == "3":
            spawn_rank_3()
        elif key == "4":
            spawn_rank_4()
        elif key == "5":
            spawn_rank_5()
        elif key == "6":
            spawn_rank_6()
        elif key == "7":
            spawn_rank_7()
        elif key == "8":
            spawn_rank_8()
        elif key == "9":
            spawn_rank_9()
        elif key == "0":
            spawn_rank_10()
        elif key == "q":
            spawn_rank_12()
        elif key == "a":
            spawn_rank_1()
        elif key == "j":
            spawn_rank_11()
        elif key == "k":
            spawn_rank_13()
    else:
        if key == "d":
            delete_all()
        elif key == "f":
            flip_all()


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

box_img = load_image(os.path.join(IMAGE_FOLDER, "box.png"), BOX_SIZE)
back_img = load_image(os.path.join(IMAGE_FOLDER, "back.png"), CARD_SIZE)

card_files = [
    f
    for f in os.listdir(IMAGE_FOLDER)
    if f.endswith(".png") and f not in ("case.png", "back.png", "box.png")
]
card_imgs = [load_image(os.path.join(IMAGE_FOLDER, f), CARD_SIZE) for f in card_files]

card_box = CardBox(
    canvas, screen_w / 2, screen_h - 108, box_img, back_img, card_imgs, card_files
)

canvas.bind("<Motion>", update_wave)
canvas.bind("<Leave>", reset_wave)
smooth_wave_animation()

root.bind("<Key>", key_pressed)
root.mainloop()

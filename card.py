import tkinter as tk
from PIL import Image, ImageTk
import os, random, math, time

BG_COLOR = "#000000"
CARD_FOLDER = "image/card"
CARD_SIZE = (74, 111)
BOX_SIZE = (80, 120)

SPREAD_SPACING = 20
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
        self.dragged = False
        self.w = w
        self.h = h

        self.canva.tag_bind(self.item_id, "<Button-1>", self._start_drag)
        self.canva.tag_bind(self.item_id, "<B1-Motion>", self._on_drag)
        self.canva.tag_bind(self.item_id, "<ButtonRelease-1>", self._stop_drag)
        self.canva.tag_bind(self.item_id, "<Button-2>", lambda e: self.middle_click(e))
        self.canva.tag_bind(self.item_id, "<Button-3>", lambda e: self.right_click(e))

    def _start_drag(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.canva.tag_raise(self.item_id)

    def _on_drag(self, event):
        self.dx = event.x - self.start_x
        self.dy = event.y - self.start_y
        dist = math.hypot(self.dx, self.dy)

        if dist > 5:
            self.dragging(True)
            x = self.item_x + self.dx
            y = self.item_y + self.dy
            if self.w and self.h:
                self.canva.coords(self.item_id, x, y, x + self.w, y + self.h)
            else:
                self.canva.coords(self.item_id, x, y)
            self.dragged = True
        else:
            self.dragged = False

    def _stop_drag(self, event):
        if self.dragged:
            self.dragging(False)
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

    def dragging(self, state):
        pass


class Box(Drag):
    def __init__(self, canva, x, y, box_img, back_img, card_imgs_names):
        self.box_img = box_img
        self.this_box = canva.create_image(x, y, image=self.box_img, tags="box")
        super().__init__(canva, x, y, self.this_box)
        self.initial_x, self.initial_y = x, y
        self.back_img = back_img
        self.all_cards = set(card_imgs_names)
        self.unused_card_names = set(card_imgs_names)
        self.used_card = []
        self.spreading = False

        self.left_click = self.spawn_card
        self.middle_click = self.reset_position
        self.right_click = self.spawn_spread

    def reset_position(self, event=None):
        self.item_x = self.initial_x
        self.item_y = self.initial_y
        self.canva.coords(self.item_id, self.item_x, self.item_y)

    def spawn_card(self, event=None):
        if not self.unused_card_names or self.spreading:
            return

        card_name = random.choice(list(self.unused_card_names))
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
        self.take_card(card_name, card)
        self.canva.tag_raise(self.item_id)
        card.up()

    def delete_card(self, targets):
        def delete_next(i):
            if i < len(targets):
                if targets[i] in self.used_card:
                    targets[i].delete(count=5)
                self.canva.after(50, lambda i=i + 1: delete_next(i))

        delete_next(0)

    def take_card(self, card_name, card):
        self.unused_card_names.discard(card_name)
        self.used_card.append(card)

    def return_card(self, card_name, card):
        self.unused_card_names.add(card_name)
        self.used_card.remove(card)

    def spawn_spread(
        self,
        event=None,
        group="all",
        sort="random",
        delete_used=True,
        face_up=False,
    ):
        if self.spreading:
            return

        self.spreading = True

        if delete_used:
            from_group = self.all_cards.copy()
        else:
            from_group = self.unused_card_names

        if group == "all":
            available = list(from_group)
        elif group == "spade":
            available = [name for name in from_group if "spade" in name]
        elif group == "diamond":
            available = [name for name in from_group if "diamond" in name]
        elif group == "club":
            available = [name for name in from_group if "club" in name]
        elif group == "heart":
            available = [name for name in from_group if "heart" in name]
        else:
            available = []

        if not available:
            print("⚠️ All cards have been generated!")
            return

        Group(self.canva, self, self.back_img, available, sort, face_up)


class Group(Drag):
    def __init__(self, canva, box, back_img, available, sort, face_up):
        n = len(available)
        screen_w = canva.winfo_width()
        screen_h = canva.winfo_height()

        total_width = CARD_SIZE[0] + (n - 1) * SPREAD_SPACING
        x = (screen_w - total_width) / 2 - CARD_SIZE[0] / 2 + 2
        y = screen_h / 2 - CARD_SIZE[1] / 2

        self.w = CARD_SIZE[0] / 4
        self.h = CARD_SIZE[1]
        self.this_group = canva.create_rectangle(
            x,
            y,
            x + self.w,
            y + self.h,
            fill="#111111",
            outline="#444444",
            width=3,
            tags="group",
        )
        super().__init__(canva, x, y, self.this_group, self.w, self.h)
        self.box = box
        self.back_img = back_img
        self.spawn_x = self.item_x
        self.spawn_y = self.item_y
        self.face_up = face_up
        self.group_cards = []
        self.moving = False
        self.flipping = False
        self.stacking = False
        self.stacked = False
        self.drag_box = None

        def standard_sort(name):
            if "joker-(1)" in name:
                return (-1, -1)
            if "joker-(2)" in name:
                return (99, 99)

            order = ["spade", "diamond", "club", "heart"]
            suit = next(i for i, s in enumerate(order) if s in name)
            digits = "".join(ch for ch in name if ch.isdigit())
            rank = int(digits)
            return (suit, rank)

        if sort == "random":
            self.available = random.sample(available.copy(), len(available))
        elif sort == "standard":
            self.available = sorted(available, key=standard_sort)
        else:
            print("⚠️ Invalid sort option:", sort)
        self.spread()

    def dragging(self, state, card=None):
        if state:
            x1, y1 = self.canva.coords(self.group_cards[0].this_card)
            x2, y2 = self.canva.coords(self.group_cards[-1].this_card)

            x1 -= CARD_SIZE[0] / 2
            x2 += CARD_SIZE[0] / 2
            y1 -= CARD_SIZE[1] / 2
            y2 += CARD_SIZE[1] / 2

            if self.drag_box == None:
                self.drag_box = self.canva.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    outline="#FFA500",
                    width=3,
                    dash=(3, 3),
                    tags="drag_outline",
                )
            else:
                self.canva.coords(self.drag_box, x1, y1, x2, y2)
        else:
            self.spawn_x += self.dx
            self.spawn_y += self.dy
            if self.drag_box:
                self.canva.delete(self.drag_box)
                self.drag_box = None

        self.moving = state
        target_cards = card if card is not None else self.group_cards
        for i in target_cards:
            i.move_card(self.dx, self.dy, state)

    def spread(self):
        if not self.available:
            print("⚠️ No cards to spread.")
            return

        def generat_next(step):
            if self.available:
                card_name = self.available.pop(0)
                if card_name not in self.box.unused_card_names:
                    for c in self.box.used_card:
                        if c.card_name == card_name:
                            self.box.delete_card([c])
                            print("🟩 Card deleted:", card_name)
                            break

                front_img = load_image(card_name, CARD_SIZE)
                x = self.spawn_x + CARD_SIZE[0] / 2 + 35 + step * SPREAD_SPACING
                y = self.spawn_y + CARD_SIZE[1] / 2
                self.spawn_card(front_img, card_name, x, y, face_up=self.face_up)
                step += 1
                self.canva.after(50, lambda s=step: generat_next(s))
            else:
                self.box.spreading = False
                self.canva.itemconfig(self.this_group, fill="#222222")
                self.left_click = self.flip_all
                self.middle_click = self.delete_group
                self.right_click = self.stack

        generat_next(0)

    def spawn_card(self, front_img, card_name, x, y, face_up):
        card = Card(
            self.canva,
            self.box,
            x,
            y,
            self.back_img,
            front_img,
            card_name,
            group=self,
            in_spread=True,
            face_up=face_up,
        )
        if self.moving:
            self.dragging(True, [card])
        self.box.take_card(card_name, card)
        self.group_cards.append(card)

    def flip_all(self, event=None):
        if self.stacked:
            self.stack()
            return
        if self.flipping or self.stacking:
            return

        self.flipping = True
        self.canva.itemconfig(self.this_group, fill="#111111")
        cards = self.group_cards.copy()

        def flip_next(step):
            if step < len(cards):
                cards[step].flip_all()
                step += 1
                self.canva.after(50, lambda s=step: flip_next(s))
            else:
                self.flipping = False
                self.canva.after(
                    400, lambda: self.canva.itemconfig(self.this_group, fill="#333333")
                )

        flip_next(0)

    def delete_group(self, event=None):
        self.box.delete_card(self.group_cards.copy())
        self.canva.delete(self.this_group)

    def remove_card(self, card):
        self.group_cards.remove(card)
        if self.group_cards == []:
            self.canva.delete(self.this_group)
        elif self.this_group:
            x, y = self.canva.coords(self.group_cards[0].this_card)
            self.item_x = x - CARD_SIZE[0] / 2 - 35
            self.item_y = y - CARD_SIZE[1] / 2
            self.canva.coords(
                self.this_group,
                self.item_x,
                self.item_y,
                self.item_x + self.w,
                self.item_y + self.h,
            )

    def stack(self, event=None):
        if self.flipping or self.stacking:
            return

        self.stacking = True

        if self.stacked:
            pass
        else:
            pass

        return

        center_x = self.item_x + CARD_SIZE[0] / 2 + 35
        center_y = self.item_y + CARD_SIZE[1] / 2

        for i in range(len(self.group_cards)):
            if i < len(self.group_cards):
                card = self.group_cards[i]
                cur_x, cur_y = self.canva.coords(card.this_card)
                dx = (center_x - cur_x) / 8
                dy = (center_y - cur_y) / 8

                def step_move(step=0):
                    if step < 8:
                        self.canva.move(card.this_card, dx, dy)
                        self.canva.after(10, lambda: step_move(step + 1))
                    else:
                        self.canva.coords(card.this_card, center_x, center_y)
                        self.stacking = False

                step_move()

    # # 彩帶排列 (ribbon_wave)
    # def ribbon_wave(self):
    #     if not self.unused_card_name:
    #         return
    #     for i, card in enumerate(self.unused_card_name):
    #         offset = math.sin(i / 2) * 25
    #         self.canva.coords(card.this_card, card.item_x, card.item_y - offset)

    # # 根據滑鼠波動 (互動)
    # def update_wave(self, event):
    #     for i, card in enumerate(self.unused_card_name):
    #         dx = abs(event.x - card.item_x)
    #         offset = 20 * math.exp(-(dx**2) / 2000)
    #         self.canva.coords(card.this_card, card.item_x, card.item_y - offset)


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
        group=None,
        in_spread=False,
        face_up=False,
    ):
        self.back_img = back_img
        self.front_img = front_img
        self.face_up = face_up
        self.this_card = canva.create_image(
            x, y, image=self.front_img if self.face_up else self.back_img, tags="card"
        )
        super().__init__(canva, x, y, self.this_card)
        self.box = box
        self.group = group
        self.card_name = card_name
        self.flipping = False
        self.in_spread = in_spread

        self.left_click = self.flip
        self.middle_click = self.delete

    def dragging(self, state):
        if self.in_spread:
            self.in_spread = False
            self.group.group_cards.remove(self)  # type: ignore

    def move_card(self, dx, dy, state):
        if not self.in_spread:
            return

        if state:
            self.canva.coords(self.this_card, self.item_x + dx, self.item_y + dy)
        else:
            self.item_x += dx
            self.item_y += dy
            self.canva.coords(self.this_card, self.item_x, self.item_y)

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
            self.group.remove_card(self)  # type: ignore
            self.up()
            if not self.face_up:
                self.canva.after(200, self.flip)
            return

        self.flipping = True
        self.animate_scale(0, 16)

    def flip_all(self):
        self.flipping = True
        self.animate_scale(0, 32)

    def animate_scale(self, step, total_steps):
        shrink_steps = total_steps / 2
        if step < shrink_steps:
            scale = (shrink_steps - step) / shrink_steps
            img = self.scale_image(scale)
            self.img = img  # type: ignore
            self.canva.itemconfig(self.this_card, image=img)
        elif step == shrink_steps:
            self.face_up = not self.face_up
        elif step <= total_steps:
            scale = (step - shrink_steps) / shrink_steps
            img = self.scale_image(scale)
            self.img = img  # type: ignore
            self.canva.itemconfig(self.this_card, image=img)
        else:
            self.flipping = False
            return
        self.canva.after(10, lambda: self.animate_scale(step + 1, total_steps))

    def scale_image(self, scale):
        img = self.front_img if self.face_up else self.back_img
        pil = ImageTk.getimage(img)
        w, h = pil.size
        new_w = max(1, int(w * scale))
        resized = pil.resize((new_w, h))
        return ImageTk.PhotoImage(resized)

    def delete(self, event=None, count=10):
        star_effect(self.canva, self.item_x, self.item_y, count)
        self.box.return_card(self.card_name, self)
        if self.in_spread:
            self.group.remove_card(self)  # type: ignore
        self.canva.delete(self.this_card)

    # def update_wave(self, mouse_y):
    #     dy = abs(self.base_y - mouse_y)
    #     if dy < 100:
    #         offset = 15 * math.exp(-(dy**2) / 4000)
    #         self.target_y = self.base_y - offset
    #     else:
    #         self.target_y = self.base_y

    # def move_toward_target(self):
    #     current_x, current_y = self.canva.coords(self.this_card)
    #     diff = self.target_y - current_y
    #     if abs(diff) > 0.5:
    #         self.canva.move(self.this_card, 0, diff * self.wave_speed)


def star_effect(canva, x, y, count):
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

    # def _handle_click(self, event):
    #     if not self.ready or self.rising:
    #         return
    #     self.flip()

    # def _handle_left_press(self, event):
    #     global focused_card
    #     if not self.ready:
    #         return
    #     focused_card = self
    #     if self.is_ribbon and not self.touched:
    #         self.rising = True
    #         self.ribbon_rise()
    #         if not self.face_up:
    #             self.canva.after(300, self.flip)
    #     self.touched = True
    #     super()._handle_left_press(event)

    # def ribbon_rise(self):
    #     current_x, current_y = self.canva.coords(self.image_id)
    #     target_y = current_y - RIBBON_RISE_HEIGHT
    #     self._animate_rise(current_x, current_y, target_y, 0)

    # def _animate_rise(self, base_x, start_y, target_y, step):
    #     steps = 10
    #     if step < steps:
    #         progress = step / steps
    #         new_y = start_y + (target_y - start_y) * progress
    #         current_x, _ = self.canva.coords(self.image_id)
    #         self.canva.coords(self.image_id, current_x, new_y)
    #         self.canva.after(
    #             20, lambda: self._animate_rise(base_x, start_y, target_y, step + 1)
    #         )
    #     else:
    #         self.base_y = target_y
    #         self.rising = False

    # def delete(self, event=None):
    #     global focused_card
    #     if not self.ready or self.destroyed:
    #         return
    #     self.destroyed = True
    #     x, y = self.canva.coords(self.image_id)
    #     # star_effect(self.canva, x, y)
    #     self.canva.delete(self.image_id)
    #     self.box.used_cards.discard(self.front_img)
    #     focused_card = None


# def spread_wave():
#     for card in group.all_cards:
#         if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
#             current_x, current_y = canva.coords(card.image_id)
#             diff = card.target_y - current_y
#             if abs(diff) > 0.5:
#                 new_y = current_y + diff * 0.3
#                 canva.coords(card.image_id, current_x, new_y)
#     canva.after(16, spread_wave)


# def update_wave(event):
#     mouse_x = event.x
#     mouse_y = event.y
#     for card in group.all_cards:
#         if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
#             dy = abs(card.base_y - mouse_y)
#             if dy > WAVE_Y_THRESHOLD:
#                 card.target_y = card.base_y
#             else:
#                 dx = abs(card.base_x - mouse_x)
#                 if dx < WAVE_RANGE:
#                     offset = WAVE_HEIGHT * math.exp(
#                         -(dx**2) / (2 * (WAVE_RANGE / 2) ** 2)
#                     )
#                     card.target_y = card.base_y - offset
#                 else:
#                     card.target_y = card.base_y


# def reset_wave(event=None):
#     for card in group.all_cards:
#         if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
#             card.target_y = card.base_y


# def star_effect(canva, x, y, count=15):
#     stars = []
#     for _ in range(count):
#         dx, dy = random.randint(-40, 40), random.randint(-40, 40)
#         star = canva.create_text(
#             x,
#             y,
#             text="✦",
#             fill=random.choice(["#FFD700", "#FFCC33", "#FFFF99"]),
#             font=("Arial", 10),
#         )
#         stars.append(star)
#         move_star(canva, star, dx, dy, 0)
#     canva.after(1000, lambda: [canva.delete(s) for s in stars])


# def move_star(canva, star, dx, dy, step):
#     canva.move(star, dx / (10 + step * 2), dy / (10 + step * 2))
#     canva.after(20, lambda: move_star(canva, star, dx, dy, step + 1))

# def reset(event=None):
#     global focused_card
#     for card in group.all_cards:
#         card.destroyed = True
#     for item in canva.find_withtag("card"):
#         canva.delete(item)
#     for item in canva.find_withtag("ribbon_handle"):
#         canva.delete(item)
#     group.used_cards.clear()
#     group.all_cards.clear()
#     ribbon_spreads.clear()
#     focused_card = None


# def delete_all(event=None):
#     global focused_card
#     for item in canva.find_withtag("card"):
#         x, y = canva.coords(item)
#         star_effect(canva, x, y)
#         canva.delete(item)
#     for item in canva.find_withtag("ribbon_handle"):
#         canva.delete(item)
#     group.used_cards.clear()
#     group.all_cards.clear()
#     ribbon_spreads.clear()
#     focused_card = None


# def flip_all(event=None):
#     cards = [c for c in group.all_cards if c.ready and not c.destroyed]
#     if not cards:
#         return
#     all_face_up = all(c.face_up for c in cards)
#     target_state = not all_face_up
#     for card in cards:
#         if card.face_up != target_state:
#             card.flip_animated()


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

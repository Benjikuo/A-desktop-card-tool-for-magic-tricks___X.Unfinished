import tkinter as tk
from PIL import Image, ImageTk
import os, random, math, time

BG_COLOR = "#000000"
CARD_FOLDER = "image/card"
CARD_SIZE = (74, 111)
BOX_SIZE = (80, 120)
SPREAD_SPACING = 20
LIST_SPACING = 100
WAVE_WIDTH = 100
WAVE_HEIGHT = 15
NO_WAVE_RANGE = 60

focus_box = None
focus_group = None
focus_card = None


class Drag:

    def __init__(self, canva, x, y, item_id, w=None, h=None):
        self.canva = canva
        self.item_id = item_id
        self.item_x, self.item_y = x, y
        self.start_x, self.start_y = 0, 0
        self.dx, self.dy = 0, 0
        self.dragged = False
        self.draggable = True
        self.w = w
        self.h = h

        for btn in ("<Button-1>", "<Button-2>", "<Button-3>"):
            self.canva.tag_bind(self.item_id, btn, self._set_focus)

        self.canva.tag_bind(self.item_id, "<Button-1>", self._start_drag, add="+")
        self.canva.tag_bind(self.item_id, "<B1-Motion>", self._on_drag)
        self.canva.tag_bind(self.item_id, "<ButtonRelease-1>", self._stop_drag)
        self.canva.tag_bind(
            self.item_id, "<Button-2>", lambda e: self.middle_click(e), add="+"
        )
        self.canva.tag_bind(
            self.item_id, "<Button-3>", lambda e: self.right_click(e), add="+"
        )

    def _set_focus(self, event=None):
        global focus_box, focus_group, focus_card
        if isinstance(self, Box):
            focus_box = self
            focus_group = None
            focus_card = None
        elif isinstance(self, Group):
            focus_box = self.box
            focus_group = self
            focus_card = None
        elif isinstance(self, Card):
            focus_box = self.box
            focus_group = self.group
            focus_card = self

    def _start_drag(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.canva.tag_raise(self.item_id)

    def _on_drag(self, event):
        if not self.draggable:
            return

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
        if self.spreading or not self.unused_card_names:
            no_card(canva, self.item_x, self.item_y - 25)
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

        global focus_box, focus_group, focus_card
        focus_box = self
        focus_group = None
        focus_card = card

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
            from_group = self.unused_card_names.copy()

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
            no_card(canva, self.item_x, self.item_y - 25)
            self.spreading = False
            return

        group = Group(self.canva, self, self.back_img, available, sort, face_up)

        global focus_box, focus_group, focus_card
        focus_box = self
        focus_group = group
        focus_card = None

    def list_card_value(self, card_name, delete_used=True, face_up=True):
        if delete_used:
            from_group = self.all_cards.copy()
        else:
            from_group = self.unused_card_names.copy()

        if "joker" in card_name:
            available = [name for name in from_group if "joker" in name]
            available.sort()
        else:
            digits = "".join(ch for ch in card_name if ch.isdigit())
            if digits == "":
                return

            available = []
            for name in from_group:
                this_digits = "".join(ch for ch in name if ch.isdigit())
                if digits == this_digits and "joker" not in name:
                    available += [name]

            order = ["spade", "diamond", "club", "heart"]
            available = sorted(
                available, key=lambda n: order.index(next(s for s in order if s in n))
            )

        if not available:
            print("⚠️ All cards have been generated!")
            return

        n = len(available)
        screen_w = canva.winfo_width()
        screen_h = canva.winfo_height()
        total_width = CARD_SIZE[0] + (n - 1) * LIST_SPACING

        def generate_next(step, w):
            if available:
                card_name = available.pop(0)
                if card_name not in self.unused_card_names:
                    for c in self.used_card:
                        if c.card_name == card_name:
                            self.delete_card([c])
                            print("🟩 Card deleted:", card_name)
                            break

                x = (
                    (screen_w - total_width) / 2
                    + CARD_SIZE[0] / 2
                    + LIST_SPACING * step
                )
                y = screen_h / 2 + CARD_SIZE[1] / 2 - 95

                front_img = load_image(card_name, CARD_SIZE)
                card = Card(
                    self.canva,
                    self,
                    x,
                    y,
                    self.back_img,
                    front_img,
                    card_name,
                    face_up=face_up,
                )
                self.take_card(card_name, card)
                self.canva.after(50, lambda s=step + 1: generate_next(s, w))

        generate_next(0, total_width)


class Group(Drag):
    instances = []

    def __init__(self, canva, box, back_img, available, sort, face_up):
        n = len(available)
        screen_w = canva.winfo_width()
        screen_h = canva.winfo_height()

        total_width = CARD_SIZE[0] + (n - 1) * SPREAD_SPACING
        x = (screen_w - total_width) / 2 - CARD_SIZE[0] / 2 + 2
        y = screen_h / 2 - CARD_SIZE[1] / 2 + 136

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
        self.box = box
        super().__init__(canva, x, y, self.this_group, self.w, self.h)
        Group.instances.append(self)
        self.back_img = back_img
        self.spawn_x = self.item_x
        self.spawn_y = self.item_y
        self.face_up = face_up
        self.group_cards = []
        self.spawning = True
        self.moving = False
        self.flipping = False
        self.stacking = False
        self.stacked = False
        self.drag_box = None

        self.left_click = self.flip_all
        self.middle_click = self.delete_group
        self.right_click = self.stack

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
        def generate_next(step):
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
                self.canva.after(50, lambda s=step + 1: generate_next(s))
            else:
                self.box.spreading = False
                self.canva.itemconfig(self.this_group, fill="#222222")
                self.spawning = False

        generate_next(0)

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
        if self.flipping or self.stacking or self.spawning:
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
        if self.spawning:
            return

        self.canva.delete(self.drag_box)
        self.drag_box = None
        self.box.delete_card(self.group_cards.copy())
        self.canva.delete(self.this_group)
        Group.instances.remove(self)
        del self

        global focus_group, focus_card
        focus_group = None
        focus_card = None

    def remove_card(self, card):
        self.group_cards.remove(card)
        if self.group_cards == []:
            self.canva.delete(self.this_group)
        elif self.this_group:
            x, y = self.canva.coords(self.group_cards[0].this_card)
            self.item_x = x - CARD_SIZE[0] / 2 - 35
            self.canva.coords(
                self.this_group,
                self.item_x,
                self.item_y,
                self.item_x + self.w,
                self.item_y + self.h,
            )

    def stack(self, event=None):
        if self.flipping or self.stacking or self.spawning:
            return

        self.stacking = True
        self.draggable = False
        self.canva.itemconfig(self.this_group, fill="#111111")
        x0, y0 = self.canva.coords(self.group_cards[0].this_card)
        y0 = self.item_y + CARD_SIZE[1] / 2
        if self.stacked:
            for i, card in enumerate(self.group_cards):

                def move_to_spread(step, c, i, target_step=50):
                    tx = x0 + i * 20
                    ty = y0
                    if step < target_step:
                        c.item_x += (tx - c.item_x) / 8
                        c.item_y += (ty - c.item_y) / 8
                        c.canva.coords(c.this_card, c.item_x, c.item_y)
                        c.canva.after(8, lambda s=step + 1: move_to_spread(s, c, i))
                    else:
                        c.item_x = tx
                        c.item_y = ty
                        c.canva.coords(c.this_card, c.item_x, c.item_y)
                        if card == self.group_cards[-1]:
                            self.stacking = False
                            self.draggable = True
                            self.canva.itemconfig(self.this_group, fill="#333333")

                move_to_spread(0, card, i)
        else:
            for card in self.group_cards:

                def move_to_stack(step, c, target_step=50):
                    if step < target_step:
                        c.item_x -= (c.item_x - x0) / 8
                        c.item_y -= (c.item_y - y0) / 8
                        c.canva.coords(c.this_card, c.item_x, c.item_y)
                        c.canva.after(8, lambda s=step + 1: move_to_stack(s, c))
                    else:
                        c.item_x = x0
                        c.item_y = y0
                        c.canva.coords(c.this_card, c.item_x, c.item_y)
                        if card == self.group_cards[-1]:
                            self.stacking = False
                            self.draggable = True
                            self.canva.itemconfig(self.this_group, fill="#333333")

                move_to_stack(0, card)

        self.stacked = not self.stacked

    def update_wave(self, mouse_x, mouse_y):
        if self.moving or self.stacked or abs(mouse_y - self.item_y) > NO_WAVE_RANGE:
            return

        for card in self.group_cards:
            distance = abs(mouse_x - card.item_x + 26)
            if distance < WAVE_WIDTH:
                target_offset = max(
                    0, math.cos(distance / WAVE_WIDTH * math.pi) * WAVE_HEIGHT
                )
            else:
                target_offset = 0

            card.current_offset += (target_offset - card.current_offset) * 0.2
            card.canva.coords(
                card.this_card, card.item_x, card.item_y - card.current_offset
            )

    def reset_wave(self):
        if self.moving or self.stacked:
            return

        is_done = True
        for card in self.group_cards:
            target_offset = 0
            card.current_offset += (target_offset - card.current_offset) * 0.2
            card.canva.coords(
                card.this_card, card.item_x, card.item_y - card.current_offset
            )
            if abs(card.current_offset) > 0.1:
                is_done = False
            else:
                card.canva.coords(card.this_card, card.item_x, card.item_y)

        if not is_done:
            self.group_cards[0].canva.after(10, self.reset_wave)


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
        self.box = box
        self.group = group
        self.card_name = card_name
        super().__init__(canva, x, y, self.this_card)
        self.in_spread = in_spread
        self.flipping = False
        self.current_offset = 0

        self.left_click = self.flip
        self.middle_click = self.delete
        self.right_click = lambda event: self.box.list_card_value(self.card_name)

    def dragging(self, state):
        if self.in_spread:
            self.in_spread = False
            self.group.remove_card(self)  # type: ignore

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

    def flip_all(self, steps=32):
        self.flipping = True
        self.animate_scale(0, steps)

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
        global focus_card
        focus_card = None

        star_effect(self.canva, self.item_x, self.item_y, count)
        self.box.return_card(self.card_name, self)
        if self.in_spread:
            self.group.remove_card(self)  # type: ignore

        self.canva.delete(self.this_card)
        del self


def no_card(canva, x, y):
    text = canva.create_text(x, y, text="❌", fill="#FF7777", font=("Arial", 15))
    canva.tag_raise(text)

    def animate(step):
        if step < 20:
            canva.move(text, 0, -3)
        elif step > 30:
            canva.delete(text)
            return
        canva.after(10, lambda: animate(step + 1))

    animate(0)


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
    if step > 60:
        return
    canva.move(star, dx / (10 + step * 2), dy / (10 + step * 2))
    canva.after(10, lambda: move_star(canva, star, dx, dy, step + 1))


def on_motion(event):
    for g in Group.instances:
        g.update_wave(event.x, event.y)


def on_leave(event):
    for g in Group.instances:
        g.reset_wave()


def key_pressed(event):
    global focus_box, focus_group, focus_card
    key = event.keysym.lower()
    ctrl = (event.state & 0x4) != 0
    shift = (event.state & 0x1) != 0
    actions = {}

    if focus_box:
        actions |= {"e": focus_box.spawn_card, "r": focus_box.reset_position}
    if focus_card:
        actions |= {"d": focus_card.delete, "f": focus_card.flip}
    if ctrl:
        actions |= {"r": root.destroy}
        if focus_group:
            actions |= {
                "e": focus_group.stack,
                "d": focus_group.delete_group,
                "f": focus_group.flip_all,
            }
        if shift:
            actions |= {
                "d": delete_all_cards,
                "f": flip_all_cards,
            }

    func = actions.get(key)
    if func:
        func()
        return

    if not focus_box:
        return

    suit_map = {
        "w": "all",
        "s": "all",
        "z": "spade",
        "x": "diamond",
        "c": "club",
        "v": "heart",
    }
    if key in suit_map:
        focus_box.spawn_spread(
            group=suit_map[key],
            sort="random" if key == "w" else "standard",
            delete_used=ctrl,
            face_up=shift,
        )
        return

    value_map = {"a": "1", "0": "10", "j": "11", "q": "12", "k": "13", "l": "joker"}
    if key in value_map:
        key = value_map.get(key)
    focus_box.list_card_value(key)


def flip_all_cards():
    if not focus_box or not focus_box.used_card:
        return

    cards = focus_box.used_card.copy()
    all_face_up = all(card.face_up for card in cards)

    def flip_next(i, cards):
        if i < len(cards):
            if cards[i].face_up == all_face_up:
                cards[i].flip_all()
            focus_box.canva.after(50, lambda: flip_next(i + 1, cards))  # type: ignore

    flip_next(0, cards)


def delete_all_cards():
    if not focus_box or not focus_box.used_card:
        return

    cards = focus_box.used_card.copy()

    def delete_next(i, cards):
        if i < len(cards):
            cards[i].delete(count=5)
            focus_box.canva.after(50, lambda: delete_next(i + 1, cards))  # type: ignore

    delete_next(0, cards)


def load_image(name, size):
    place = os.path.join(CARD_FOLDER, name)
    return ImageTk.PhotoImage(Image.open(place).resize(size))


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

box = Box(canva, screen_w / 2, screen_h - 108, box_img, back_img, card_imgs_names)
focus_box = box

root.bind("<Motion>", on_motion)
root.bind("<Leave>", on_leave)
root.bind("<Key>", key_pressed)

root.mainloop()

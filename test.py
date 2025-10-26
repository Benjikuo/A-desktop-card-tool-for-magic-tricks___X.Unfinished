import tkinter as tk
import random
import math

BG_COLOR = "#0f0f0f"
CANVAS_W, CANVAS_H = 1280, 800
CARD_W, CARD_H = 74, 111
BOX_W, BOX_H = 80, 120
RIBBON_SPACING = 20
WAVE_RANGE = 60
WAVE_HEIGHT = 18
RIBBON_RISE_HEIGHT = 180

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

focused_card = None


class Draggable:
    def __init__(self, canvas, tag):
        self.canvas = canvas
        self.tag = tag
        self.drag_data = {"x": 0, "y": 0}
        self.canvas.tag_bind(self.tag, "<Button-1>", self._on_press)
        self.canvas.tag_bind(self.tag, "<B1-Motion>", self._on_drag)
        self.canvas.tag_bind(self.tag, "<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        self.canvas.tag_raise(self.tag)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def _on_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.canvas.move(self.tag, dx, dy)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def _on_release(self, event):
        pass


class Card(Draggable):
    _id_counter = 0

    def __init__(self, canvas, x, y, suit, rank, group=None):
        self.canvas = canvas
        self.suit = suit
        self.rank = rank
        self.face_up = False
        self.group = group
        self.tag = f"card_{Card._id_counter}"
        Card._id_counter += 1

        x0, y0 = x - CARD_W // 2, y - CARD_H // 2
        x1, y1 = x + CARD_W // 2, y + CARD_H // 2

        self.rect = canvas.create_rectangle(
            x0, y0, x1, y1, fill="#2a2a2a", outline="#888", width=2, tags=(self.tag,)
        )
        self.pip = canvas.create_text(
            x0 + 12,
            y0 + 12,
            text=f"{self.rank}\n{self.suit}",
            anchor="nw",
            fill="#d0d0d0",
            font=("Segoe UI", 10, "bold"),
            tags=(self.tag,),
        )
        self.center_label = canvas.create_text(
            (x0 + x1) // 2,
            (y0 + y1) // 2,
            text="🂠",
            fill="#aaaaaa",
            font=("Segoe UI Symbol", 20),
            tags=(self.tag,),
        )

        super().__init__(canvas, self.tag)

        canvas.tag_bind(self.tag, "<Double-Button-1>", self._flip)
        canvas.tag_bind(self.tag, "<Button-3>", self._toggle_select)
        canvas.tag_bind(self.tag, "<MouseWheel>", self._on_wheel)
        canvas.tag_bind(self.tag, "<Button-2>", self._rotate_15)

    def _toggle_select(self, event=None):
        global focused_card
        if focused_card is not None:
            focused_card._unfocus()
        focused_card = self
        self._focus()

    def _focus(self):
        self.canvas.itemconfig(self.rect, outline="#ffa500", width=3)

    def _unfocus(self):
        self.canvas.itemconfig(self.rect, outline="#888", width=2)

    def _flip(self, event=None):
        self.face_up = not self.face_up
        if self.face_up:
            self.canvas.itemconfig(self.rect, fill="#ffffff")
            self.canvas.itemconfig(
                self.center_label,
                text=f"{self.rank}{self.suit}",
                fill="#222222",
                font=("Segoe UI", 20, "bold"),
            )
            color = "#d00000" if self.suit in ("♥", "♦") else "#222"
            self.canvas.itemconfig(self.pip, fill=color)
        else:
            self.canvas.itemconfig(self.rect, fill="#2a2a2a")
            self.canvas.itemconfig(self.center_label, text="🂠", fill="#aaaaaa")
            self.canvas.itemconfig(self.pip, fill="#d0d0d0")

    def _on_wheel(self, event):
        scale = 1.1 if event.delta > 0 else 0.9
        self._scale_about_center(scale)

    def _scale_about_center(self, s):
        x0, y0, x1, y1 = self.canvas.bbox(self.tag)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        self.canvas.scale(self.tag, cx, cy, s, s)

    def _rotate_15(self, event=None):
        x0, y0, x1, y1 = self.canvas.bbox(self.rect)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for item in (self.rect, self.pip, self.center_label):
            self.canvas.tk.call(self.canvas._w, "rotate", item, cx, cy, 15)

    def delete(self):
        self.canvas.delete(self.tag)
        global focused_card
        if focused_card is self:
            focused_card = None

    def move_to(self, x, y):
        x0, y0, x1, y1 = self.canvas.bbox(self.tag)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        self.canvas.move(self.tag, x - cx, y - cy)


class CardGroup(Draggable):
    _id_counter = 0

    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.cards = []
        self.tag = f"group_{CardGroup._id_counter}"
        CardGroup._id_counter += 1
        self.handle = canvas.create_rectangle(
            x - 30,
            y - 15,
            x + 30,
            y + 15,
            fill="#333",
            outline="#aaa",
            tags=(self.tag,),
        )
        self.label = canvas.create_text(
            x,
            y,
            text="Group",
            fill="#eee",
            tags=(self.tag,),
            font=("Segoe UI", 10, "bold"),
        )
        super().__init__(canvas, self.tag)

        canvas.tag_bind(self.tag, "<Button-3>", self._toggle_pin)
        self.pinned = False

    def add(self, card: Card):
        if card not in self.cards:
            self.cards.append(card)
            card.group = self

    def remove(self, card: Card):
        if card in self.cards:
            self.cards.remove(card)
            card.group = None

    def fan(self, spacing=24):
        if not self.cards:
            return
        x0, y0, x1, y1 = self.canvas.bbox(self.tag)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        start_x = cx - (len(self.cards) - 1) * spacing / 2
        for i, c in enumerate(self.cards):
            c.move_to(start_x + i * spacing, cy + 90)

    def wave(self, spacing=RIBBON_SPACING):
        if not self.cards:
            return
        x0, y0, x1, y1 = self.canvas.bbox(self.tag)
        base_x = ((x0 + x1) / 2) - (len(self.cards) - 1) * spacing / 2
        base_y = (y0 + y1) / 2 + 120
        for i, c in enumerate(self.cards):
            x = base_x + i * spacing
            y = base_y - RIBBON_RISE_HEIGHT + WAVE_HEIGHT * math.sin(i * 0.7)
            c.move_to(x, y)

    def _toggle_pin(self, event=None):
        self.pinned = not self.pinned
        color = "#2a6" if self.pinned else "#333"
        self.canvas.itemconfig(self.handle, fill=color)


class CardBox(Draggable):
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.tag = "card_box"
        self.rect = canvas.create_rectangle(
            x - BOX_W // 2,
            y - BOX_H // 2,
            x + BOX_W // 2,
            y + BOX_H // 2,
            fill="#004477",
            outline="#88d",
            width=3,
            tags=(self.tag,),
        )
        self.text = canvas.create_text(
            x,
            y,
            text="BOX",
            fill="#eef",
            font=("Segoe UI", 12, "bold"),
            tags=(self.tag,),
        )
        super().__init__(canvas, self.tag)

        canvas.tag_bind(self.tag, "<Button-3>", self._spawn_random)
        canvas.tag_bind(self.tag, "<Double-Button-1>", self._spread_ribbon)

        self.pool = [(s, r) for s in SUITS for r in RANKS]
        random.shuffle(self.pool)

    def _spawn_random(self, event=None):
        self.spawn_random_card()

    def _spread_ribbon(self, event=None):
        ribbon_spread()

    def spawn_random_card(self):
        if not self.pool:
            self.pool = [(s, r) for s in SUITS for r in RANKS]
            random.shuffle(self.pool)
        s, r = self.pool.pop()
        x0, y0, x1, y1 = self.canvas.bbox(self.tag)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 150
        c = Card(self.canvas, cx, cy, s, r)
        all_cards.append(c)
        return c

    def spawn_cards_by_rank(self, n):
        r = RANKS[(n - 1) % 13]
        s = random.choice(SUITS)
        x0, y0, x1, y1 = self.canvas.bbox(self.tag)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 150
        c = Card(self.canvas, cx, cy, s, r)
        all_cards.append(c)
        return c


def ribbon_spread():
    if not all_cards:
        return
    all_cards_sorted = sorted(
        enumerate(all_cards),
        key=lambda t: (SUITS.index(t[1].suit), RANKS.index(t[1].rank), t[0]),
    )
    start_x = 100
    base_y = CANVAS_H // 2
    for i, (_, c) in enumerate(all_cards_sorted):
        x = start_x + i * RIBBON_SPACING
        y = base_y - RIBBON_RISE_HEIGHT + WAVE_HEIGHT * math.sin(i * 0.7)
        c.move_to(x, y)


def ribbon_spread_sorted():
    if not all_cards:
        return
    col = 0
    row = 0
    start_x = 120
    start_y = 140
    gap_x = 26
    gap_y = 36
    for s in SUITS:
        for r in RANKS:
            matches = [c for c in all_cards if c.suit == s and c.rank == r]
            for c in matches:
                x = start_x + col * gap_x
                y = start_y + row * gap_y
                c.move_to(x, y)
                col += 1
                if col > 25:
                    col = 0
                    row += 1


def ribbon_spread_by_suit(suit):
    subset = [c for c in all_cards if c.suit == suit]
    if not subset:
        return
    start_x = 120
    base_y = 220 + 80 * SUITS.index(suit)
    for i, c in enumerate(subset):
        x = start_x + i * 22
        y = base_y - 60 + 12 * math.sin(i * 0.8)
        c.move_to(x, y)


def reset_all():
    global focused_card
    for c in list(all_cards):
        c.delete()
    all_cards.clear()
    focused_card = None


def spawn_random_card(event=None):
    card_box.spawn_random_card()


def spread(event=None):
    ribbon_spread()


def spread_sorted(event=None):
    ribbon_spread_sorted()


def spread_spade(event=None):
    ribbon_spread_by_suit("♠")


def spread_heart(event=None):
    ribbon_spread_by_suit("♥")


def spread_diamond(event=None):
    ribbon_spread_by_suit("♦")


def spread_club(event=None):
    ribbon_spread_by_suit("♣")


def flip(event=None):
    if focused_card:
        focused_card._flip()


def delete_selected(event=None):
    if focused_card:
        all_cards.remove(focused_card)
        focused_card.delete()


def nudge(dx, dy):
    if focused_card:
        x0, y0, x1, y1 = canvas.bbox(focused_card.tag)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        focused_card.move_to(cx + dx, cy + dy)


def key_pressed(event):
    key = event.keysym.lower()
    ctrl = (event.state & 0x4) != 0

    if key in ("left", "a") and not ctrl:
        nudge(-5, 0)
        return
    if key in ("right", "d") and not ctrl:
        nudge(5, 0)
        return
    if key in ("up", "w") and not ctrl:
        nudge(0, -5)
        return
    if key in ("down", "s") and not ctrl:
        nudge(0, 5)
        return

    shortcuts = {
        "r": reset_all,
        "t": spawn_random_card,
        "y": spread,
        "u": spread_sorted,
        "1": lambda: card_box.spawn_cards_by_rank(1),
        "2": lambda: card_box.spawn_cards_by_rank(2),
        "3": lambda: card_box.spawn_cards_by_rank(3),
        "4": lambda: card_box.spawn_cards_by_rank(4),
        "5": lambda: card_box.spawn_cards_by_rank(5),
        "6": lambda: card_box.spawn_cards_by_rank(6),
        "7": lambda: card_box.spawn_cards_by_rank(7),
        "8": lambda: card_box.spawn_cards_by_rank(8),
        "9": lambda: card_box.spawn_cards_by_rank(9),
        "0": lambda: card_box.spawn_cards_by_rank(10),
        "minus": lambda: card_box.spawn_cards_by_rank(11),
        "equal": lambda: card_box.spawn_cards_by_rank(12),
        "backspace": lambda: card_box.spawn_cards_by_rank(13),
        "f": flip,
        "delete": delete_selected,
        "space": spread,
        "q": spread_spade,
        "w": spread_heart,
        "e": spread_diamond,
        "c": spread_club,
        "g": lambda: current_group.fan(26),
        "h": lambda: current_group.wave(22),
        "b": lambda: current_group.add(focused_card) if focused_card else None,
        "n": lambda: current_group.remove(focused_card) if focused_card else None,
    }

    action = shortcuts.get(key)
    if action:
        action()


root = tk.Tk()
root.title("Desktop Cards - Draggable/Hotkeys")
root.configure(bg=BG_COLOR)
canvas = tk.Canvas(
    root, width=CANVAS_W, height=CANVAS_H, bg=BG_COLOR, highlightthickness=0
)
canvas.pack(fill="both", expand=True)

try:
    canvas.tk.call(
        "namespace", "eval", "::tk::canvas", "proc", "rotate", "{w item cx cy ang} { }"
    )
except tk.TclError:
    pass

all_cards = []
card_box = CardBox(canvas, CANVAS_W // 2, CANVAS_H // 2)
current_group = CardGroup(canvas, 200, 80)

root.bind("<Key>", key_pressed)


def quick_demo_layout():
    for _ in range(7):
        card_box.spawn_random_card()
    ribbon_spread()


root.after(100, quick_demo_layout)
root.mainloop()

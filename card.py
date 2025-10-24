import tkinter as tk
from PIL import Image, ImageTk
import os, random, math

BG_COLOR = "#09FF00"
IMAGE_FOLDER = "image/card"
CARD_SIZE = (74, 111)
BOX_SIZE = (80, 120)
RIBBON_SPACING = 20  # 卡片間距
WAVE_RANGE = 60  # 波浪影響範圍(像素)
WAVE_HEIGHT = 15  # 波浪最大高度(像素)
WAVE_Y_THRESHOLD = 100  # Y軸距離閾值,超過此距離不觸發波浪
RIBBON_RISE_HEIGHT = 150  # 點擊時上升的高度

focused_card = None


class CardBox:
    def __init__(self, canvas, x, y, box_img, back_img, card_imgs):
        self.canvas = canvas
        self.x, self.y = x, y
        self.box_img = box_img
        self.back_img = back_img
        self.card_imgs = card_imgs.copy()
        self.used_cards = set()
        self.all_cards = []  # 追蹤所有生成的卡片

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

    def ribbon_spread(self):
        """緞帶展排：依序展開所有未使用的卡片，置中顯示"""
        available = [img for img in self.card_imgs if img not in self.used_cards]
        if not available:
            print("⚠️ 所有卡片都已生成完畢！")
            return

        # 隨機打亂順序
        shuffled = available.copy()
        random.shuffle(shuffled)

        # 計算總寬度和起始位置（水平置中，往下半張牌+30px+50px+1px）
        total_width = CARD_SIZE[0] + (len(shuffled) - 1) * RIBBON_SPACING
        screen_w = self.canvas.winfo_width()
        screen_h = self.canvas.winfo_height()
        start_x = (screen_w - total_width) // 2 + CARD_SIZE[0] // 2
        start_y = screen_h // 2 + CARD_SIZE[1] // 2 + 30 + 50 + 1  # 往下半張牌+81px

        # 依序生成卡片
        for i, img in enumerate(shuffled):
            x = start_x + i * RIBBON_SPACING
            y = start_y
            delay = i * 50  # 每張卡片延遲50ms出現
            self.canvas.after(
                delay, lambda img=img, x=x, y=y: self._spawn_ribbon_card(img, x, y)
            )

    def _spawn_ribbon_card(self, img, x, y):
        """生成緞帶展排的單張卡片"""
        self.used_cards.add(img)
        card = Card(
            self.canvas,
            x,
            y,
            self.back_img,
            img,
            self,
            skip_animation=True,
            is_ribbon=True,
        )
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
        self.canvas.tag_lower(self.image_id, "box")
        self.flipping = False
        self.ready = False
        self.destroyed = False  # 追蹤是否已被刪除
        self.is_ribbon = is_ribbon  # 是否為緞帶展排的卡片
        self.base_x = x  # 記錄原始X座標
        self.base_y = y  # 記錄原始Y座標
        self.target_y = y  # 目標Y座標(用於平滑過渡)
        self.touched = False  # 是否被碰觸過
        self.rising = False  # 是否正在上升動畫中

        self._drag_data = {"x": 0, "y": 0, "moved": False}
        self._press_pos = (0, 0)

        if skip_animation:
            self.ready = True
            self.bind_events()
        else:
            self.animate_up(0)

    def animate_up(self, step):
        """生成時上升動畫（輕微上升）"""
        if self.destroyed:  # 如果已被刪除,停止動畫
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
        self.canvas.tag_bind(self.image_id, "<Button-2>", self.destroy)

    def start_drag(self, event):
        global focused_card
        if not self.ready:
            return
        focused_card = self  # 設定為當前選中的卡片

        # 如果是緞帶卡片且還沒被碰觸,先上升再標記
        if self.is_ribbon and not self.touched:
            self.rising = True  # 標記正在上升
            self.ribbon_rise()
            if not self.face_up:
                self.canvas.after(300, self.flip_animated)

        self.touched = True  # 標記為已碰觸
        self._press_pos = (event.x, event.y)
        self._drag_data = {"x": event.x, "y": event.y, "moved": False}
        self.canvas.tag_raise(self.image_id)

    def ribbon_rise(self):
        """緞帶卡片被點擊時上升動畫"""
        current_x, current_y = self.canvas.coords(self.image_id)
        target_y = current_y - RIBBON_RISE_HEIGHT
        self._animate_rise(current_x, current_y, target_y, 0)

    def _animate_rise(self, base_x, start_y, target_y, step):
        """平滑上升動畫(原本速度)"""
        steps = 10  # 恢復原本步數
        if step < steps:
            progress = step / steps
            new_y = start_y + (target_y - start_y) * progress
            current_x, _ = self.canvas.coords(self.image_id)
            self.canvas.coords(self.image_id, current_x, new_y)
            self.canvas.after(
                20, lambda: self._animate_rise(base_x, start_y, target_y, step + 1)
            )  # 恢復原本間隔
        else:
            # 動畫完成,更新base_y並解除rising狀態
            self.base_y = target_y
            self.rising = False

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
        # 如果正在上升動畫中,不觸發翻面
        if self.rising:
            self._drag_data = {"x": 0, "y": 0, "moved": False}
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
        self.destroyed = True  # 標記已刪除
        x, y = self.canvas.coords(self.image_id)
        star_effect(self.canvas, x, y)
        self.canvas.delete(self.image_id)
        self.box.used_cards.discard(self.front_img)
        if focused_card == self:
            focused_card = None


# ✅ D 鍵：刪除當前選中的卡片
def delete(event=None):
    global focused_card
    if focused_card and focused_card.ready:
        focused_card.destroy()


# ✅ F 鍵：翻轉當前選中的卡片
def flip(event=None):
    if focused_card and focused_card.ready:
        focused_card.flip_animated()


# ✅ Ctrl + F：統一翻轉所有卡片
def flip_all(event=None):
    cards = [c for c in card_box.all_cards if c.ready and not c.destroyed]
    if not cards:
        return
    # 檢查是否全部都是正面
    all_face_up = all(c.face_up for c in cards)
    # 如果全是正面→翻背面,否則→翻正面
    target_state = not all_face_up
    for card in cards:
        if card.face_up != target_state:
            card.flip_animated()


# ✅ Ctrl + D：刪除所有卡片（帶星星特效）
def delete_all(event=None):
    global focused_card
    for item in canvas.find_withtag("card"):
        x, y = canvas.coords(item)
        star_effect(canvas, x, y)
        canvas.delete(item)
    card_box.used_cards.clear()
    card_box.all_cards.clear()
    focused_card = None


# ✅ Ctrl + R：重置所有卡片（無特效，回到初始狀態）
def reset(event=None):
    global focused_card
    # 先標記所有卡片為已刪除,停止動畫
    for card in card_box.all_cards:
        card.destroyed = True
    # 再刪除canvas上的item
    for item in canvas.find_withtag("card"):
        canvas.delete(item)
    card_box.used_cards.clear()
    card_box.all_cards.clear()
    focused_card = None


# ✅ Ctrl + S：緞帶展排
def spread(event=None):
    card_box.ribbon_spread()


# ✅ 波浪效果：滑鼠移動時更新緞帶卡片的目標位置
def update_wave(event):
    mouse_x = event.x
    mouse_y = event.y
    for card in card_box.all_cards:
        if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
            # 檢查Y軸距離,太遠就恢復平整
            dy = abs(card.base_y - mouse_y)
            if dy > WAVE_Y_THRESHOLD:
                card.target_y = card.base_y
            else:
                # 計算X軸距離
                dx = abs(card.base_x - mouse_x)
                if dx < WAVE_RANGE:
                    # 使用高斯函數計算偏移量
                    offset = WAVE_HEIGHT * math.exp(
                        -(dx**2) / (2 * (WAVE_RANGE / 2) ** 2)
                    )
                    card.target_y = card.base_y - offset  # 往上凸
                else:
                    card.target_y = card.base_y


# ✅ 平滑過渡動畫：讓卡片逐漸移動到目標位置
def smooth_wave_animation():
    for card in card_box.all_cards:
        if card.is_ribbon and not card.touched and card.ready and not card.destroyed:
            current_x, current_y = canvas.coords(card.image_id)
            # 每幀移動差距的30%(緩動效果)
            diff = card.target_y - current_y
            if abs(diff) > 0.5:  # 只有差距大於0.5px才移動
                new_y = current_y + diff * 0.3
                canvas.coords(card.image_id, current_x, new_y)
    # 持續更新動畫
    canvas.after(16, smooth_wave_animation)  # 約60 FPS


# ✅ 滑鼠離開canvas時恢復所有緞帶卡片到原位
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
    ctrl = (event.state & 0x4) != 0  # 偵測 Ctrl 是否按下

    # 無 Ctrl 的一般操作
    if not ctrl:
        if key == "w":
            perfect_spread()
        elif key == "e":
            set_card()
        elif key == "r":
            reset()
        elif key == "s":
            spread()
        elif key == "d":
            delete()
        elif key == "f":
            flip()
        elif key == "z":
            spread()
        elif key == "x":
            spread()
        elif key == "c":
            spread()
        elif key == "v":
            spread()

    # Ctrl 組合操作
    else:
        if key == "w":
            perfect_spread_all()
        elif key == "s":
            spread_all()
        elif key == "d":
            delete_all()
        elif key == "f":
            flip_all()


# w 全部排序緞帶展排
# e 精確選牌
# r 重置
# s 混亂緞帶展排
# d 刪除
# f 翻轉
# t 隨便拿一張
# g 全部閃牌記憶
# b 讀心術魔術 6張牌消失一張

# ctrl + s 全部混亂緞帶展排
# ctrl + d 全部刪除
# ctrl + f 全部翻轉

# z 黑桃排序緞帶展排
# x 菱形排序緞帶展排
# c 梅花排序緞帶展排
# v 愛心排序緞帶展排

# A 四張A
# 1 四張A
# 2 四張2
# ...
# J 四張J
# Q 四張Q
# K 四張K


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
card_imgs = [
    load_image(os.path.join(IMAGE_FOLDER, f), CARD_SIZE)
    for f in os.listdir(IMAGE_FOLDER)
    if f.endswith(".png") and f not in ("case.png", "back.png")
]

card_box = CardBox(canvas, screen_w / 2, screen_h / 2, box_img, back_img, card_imgs)

canvas.bind("<Motion>", update_wave)
canvas.bind("<Leave>", reset_wave)
smooth_wave_animation()

root.bind("<Key>", key_pressed)
root.mainloop()

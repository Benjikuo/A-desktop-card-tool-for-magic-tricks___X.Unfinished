# A-desktop-card-tool-for-magic-tricks
This is a program that allows a magician to select a random or specific card on a computer desktop.

<p>
  <img src="./image/showcase.gif" width="600">
</p>

## 🛠️ Why I Built This

I’ve always been fascinated by the blend of illusion and technology — this project brings both together.
It’s not just a card generator — it’s a stage for digital magic, letting magicians perform with precision and surprise, right from their screen.

🧩 Features

🪄 Interactive Card System – Click, drag, flip, and delete cards naturally on your desktop
🎴 Group Spread Animation – Generate and spread cards with smooth animations
🃏 Smart Deck Control – Spawn random or specific cards, manage used/unused cards automatically
✨ Star Effect – Beautiful particle animation when a card disappears
🌊 Wave Motion – Hover the mouse to make the card group ripple dynamically
🔁 Stack & Flip – Instantly pile cards together or reveal them all
💡 Value Listing – Show all cards of the same value with one click
⌨️ Keyboard Shortcuts – Fast access to every function for live magic shows
🎬 No-Window Mode – Seamlessly overlay on desktop for a clean performance look

📂 Project Structure

Desktop Card/
├── image/         # Card assets (fronts and backs)
├── card.py        # Core classes: Drag, Box, Group, Card
├── card_button.py    # Launcher / control window
├── card_box.png     # Card box image
├── back.png       # Card back image
├── LICENSE       # License file
└── README.md      # Project documentation

⚙️ Requirements

Before running, install dependencies:

pip install pillow

▶️ How to Run

Make sure your /image/card folder contains all 52 cards and a back image.

Launch the program:

python card_button.py


A small, frameless window will appear at the bottom center of the screen — click to spawn your deck and begin your performance.

🖱️ Mouse Actions
Button	Object	Action
Left Click	Box	Spawn a random card
Middle Click	Box	Reset box position
Right Click	Box	Spread group of cards
Left Click	Group	Flip all cards in group
Middle Click	Group	Delete group
Right Click	Group	Stack / Unstack cards
Left Click	Card	Flip the card
Middle Click	Card	Delete card
Right Click	Card	Show all cards of same value
⌨️ Hotkeys
Key	Action
E	Spawn single card
R	Reset box position
Ctrl + R	Exit program
D	Delete selected card
F	Flip selected card
Ctrl + E	Stack / Unstack all
Ctrl + D	Delete card group
Ctrl + F	Flip card group
Shift + D	Delete all cards
Shift + F	Flip all cards
W / S	Spread all cards (random order)
Z / X / C / V	Spread by suit (spade, diamond, club, heart)
A / J / Q / K / L / 0–9	Show all cards of the same value
Ctrl + (key)	Apply action to all used cards
Shift + (key)	Perform with all cards face-up
🎨 Visual Effects

✨ Star Effect – Card deletion leaves behind glowing particles
🌊 Wave Effect – Hover over cards to see them ripple smoothly
🎬 Card Rise – Cards float upward when drawn
🔄 Flip Animation – Realistic shrinking and expanding flip motion

🧠 Class Overview
Drag (base draggable class)
 ├── Box – controls deck and spawns cards
 ├── Group – manages card groups and wave effects
 └── Card – handles flipping, deleting, and animations

💡 Tips for Magicians

Use Ctrl and Shift modifiers creatively for live tricks.

Keep only one focus_box active for smoother performance.

Combine wave and star effects for visual “reveal” moments.

📜 License

This project is released under the MIT License.
You are free to modify and use it for learning, personal, or performance purposes.

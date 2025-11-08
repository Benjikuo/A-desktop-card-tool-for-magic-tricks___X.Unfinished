# A-desktop-card-tool-for-magic-tricks
This is a program that allows a magician to select a random or specific card on a computer desktop.

<p>
  <img src="./image/showcase.gif" width="850">
</p>

<br>

## 🛠️ Why I Built This
- There are times that I forget to bring my cards, which makes me wonder if I can do a magic trick on computer.
- It’s a good way to learn how Python classes work ... figuring out each one takes time, though (^_^)a.
- I like to fill my desktop with interesting programs. They look cool.

<br>

## 🧩 Features
- 🪄 **Interactive Cards** – Click, drag, flip, and delete cards naturally on your desktop
- 🃏 **Spread & Stack** – Instantly pile cards together or reveal them all
- ✨ **Star Effect** – Beautiful particle animation when a card disappears  
- 🌊 **Wave Motion** – Hover the mouse to make the card group ripple dynamically  
- 🎲 **Smart Deck Spawn** – Spawn cards in a random or specific order
- 📃 **Card Listing** – Show all the cards of the same suit or value
- ⌨️ **Keyboard Shortcuts** – Quickly access all features during live magic performances

<br>

## 📂 Project Structure  
```
Desktop Card/
├── image/
│   ├── button/           # Button graphics
│   ├── card/             # Card and box graphics
│   └── showcase.gif      # Demonstration gif
├── card.py               # Window and classes  (Drag, Box, Group, Card)
├── card_button.py        # Launch button
├── LICENSE               # MIT license
└── README.md             # Project documentation
```

<br>

## ⚙️ Requirements
Install dependencies before running:
```bash
pip install pillow
```

<br>

## ▶️ How to Run
1. Make sure the folder /image/card contains **54 card faces**, one **back image**, and one **box image**.
2. Make sure the folder /image/button contains the **three** button states (gray, orange, and white).
3. Launch the program:
   ```bash
   python card_button.py
   ```
4. Click the spade-shaped button at at the bottom left to toggle the main card window. 

<br>

## 💻 Keyboard and Mouse Controls
### [Keyboard]
**Basic Operations:**
| Key | Action |
|-----|--------|
| `E`        | Spawn a card |
| `R`        | Reset box position |
| `D`        | Delete a card |
| `F`        | Flip a card |
| `Ctrl + E` | Stack the card group |
| `Ctrl + R` | Close the window |
| `Ctrl + D` | Delete the card group |
| `Ctrl + F` | Flip the card group |
| `Ctrl + shift + D` | Delete all cards |
| `Ctrl + shift + F` | Flip all cards |

<br>

**Create a Card Spread:**
| Key | Action |
|-----|--------|
| `W` | Spawn an **unstored** card spread with all cards |
| `S` | Spawn a **stored** card spread with all cards |
| `Z` | Spawn a stored card spread with all **spade** cards |
| `X` | Spawn a stored card spread with all **diamond** cards |
| `C` | Spawn a stored card spread with all **club** cards |
| `V` | Spawn a stored card spread with all **heart** cards |
| `G` | Spawn a stored card spread with all **red** cards |
| `B` | Spawn a stored card spread with all **black** cards |

*(**+Ctrl:** delete used cards, **+Shift:** face-up)*

<br>

**Create a Magic Stack:**
| Key | Action |
|-----|--------|
| `Ctrl + 1` | Spawn a **Si Stebbins** stack |
| `Ctrl + 2` | Spawn a **Eight Kings** stack |
| `Ctrl + 3` | Spawn a **color mirror** stack |

*(**+Shift:** face-up)*

<br>

**Display Cards by Value:**
| Key | Action |
|-----|--------|
| `0`   | Spawn four **10s** |
| `1`   | Spawn four **Aces** |
| `2–9` | Spawn four cards of the corresponding number |
| `A`   | Spawn four **Aces** |
| `J`   | Spawn four **Jacks** |
| `Q`   | Spawn four **Queens** |
| `K`   | Spawn four **Kings** |
| `L`   | Spawn two **Jokers** |

---

### [Mouse]
**Drag:**  
Right-click and drag to move an item.

<br>

**Click:**
| button \ item | Card                 | Spread Bar                  | Box |
|---------------|----------------------|-----------------------------|-----|
| left          | Flip a card          | Flip cards in card spread   | Spawn a card |
| middle        | Delete a card        | Delete cards in card spread | Reset box position |
| right         | Spawn four of a kind | Stack cards in card spread  | Spawn a card spread |

<br>

## 📋 Class Overview
**Drag** (base draggable class)  
 ├── **Box** (controls card spawning)  
 ├── **Group** (manages card groups)  
 └── **Card** (handles card behaviors)  

<br>

## 💡 Tips for Magicians
- Use the card spread to let the spectator pick a random card.
- Keep the cards visible on screen to help magician remember the spectator’s card or your prediction.
- Through the stack system, the magician can identify the spectator’s card or determine its position in the deck.

<br>

## 📜 License
This project is released under the MIT License.  
You are free to modify and use it for learning, personal, or performance purposes.  

**Making this program work felt like a miracle to me — now it’s your turn to make the magic happen.**


# Yes/No Othello

A goofy take on Othello/Reversi where every turn is affected by the [yesno.wtf](https://yesno.wtf) API.  
The board still follows classic 8×8 Othello rules, but the stone you are allowed to place depends on a random YES/NO/MAYBE result fetched from the API. Each piece now renders its `YES`/`NO` text directly on top (white text on black stones, black text on white stones) so you can instantly tell which side the API assigned you.

## Requirements

- Python 3.12+
- `pygame-ce`
- `numpy`
- `requests`
- `gif_pygame`

Install dependencies:

```bash
pip install -r requirements.txt
# or manually:
pip install pygame-ce numpy requests gif_pygame
```

## Running the game

```bash
python game/Yes_No_Othello.py
```

You will be prompted to choose a mode:

- `0` – Human vs. Human (local hot-seat)
- `1` – Human vs. Random AI
- `2` – Human vs. Minimax AI (greedy simulation based on the current API stone)

After selecting the opponent, you can choose whether to enable the **GIF popup mode** by answering `True`/`False`. When enabled, the yesno.wtf GIF is streamed as an animation overlay before every move; click (or press any key) to dismiss the popup and continue the game.

The window displays the board on the left and a status panel on the right with the current score, active turn, stone enforced by the API, and live messages about passes or special events.

## Rules and twists

- Turns alternate as in standard Othello. Legal moves must still capture at least one opponent stone.
- At the start of a turn, the game contacts the yesno.wtf API.
  - `yes`: you must place a YES stone (black). If it matches your side you get a normal turn; if not, you place the opponent stone and cannot flip any captured pieces.
  - `no`: same as above but with NO stones (white).
  - `maybe`: you place your own stone, flip normally, **and** every adjacent opponent stone is forcibly flipped afterward. The entire board briefly flashes to highlight the effect.
- If the API request fails, the game randomly picks YES or NO.
- A player without legal moves automatically passes. Two consecutive passes or a full board ends the game.
- The winner is whoever has more stones when the game ends; equal counts produce a draw.
- Optional GIF popup mode plays the yesno.wtf reaction GIF (looping animation) before each placement, giving you a moment to appreciate the API’s judgment. Click to close the popup and proceed.

## Controls

- **Mouse click** on a board cell to place a stone when it is your turn.
- **Mouse click / any key** while the GIF popup is visible to return to the board.
- **Close window** to quit early; the winner (if any) prints to the terminal.

Enjoy the chaos! The combination of API-driven stone assignments and the MAYBE blast makes each playthrough unpredictable.

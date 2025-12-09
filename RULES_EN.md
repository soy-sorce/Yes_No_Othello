# Yes/No Othello – Rule Overview

This document describes the rules of **Yes/No Othello**, an 8×8 Othello/Reversi variant whose turns are driven by the [yesno.wtf](https://yesno.wtf) API. Every turn, the API decides which stone you are allowed to place, so the familiar mechanics can suddenly favor or hinder you.

## Setup
- Standard 8×8 board with the same initial four stones as classic Othello (black at d5/e4, white at d4/e5).
- Two stone colors are used: black (`YES`) and white (`NO`). Each stone has its `YES`/`NO` label printed on top (white text on black stones, black text on white stones) so you can always tell which side belongs to which answer.
- Players alternate turns; you may only play a move that flips at least one opponent stone.
- The game ends when the board is full or both players pass consecutively. The player with more stones wins; equal counts produce a draw.

## Turn Sequence
1. At the start of a turn the game calls yesno.wtf and receives `yes`, `no`, or `maybe`. If the request fails, a random `yes`/`no` is chosen instead.
2. The API result determines which stone can be placed and what special effects occur.
3. The current player clicks a legal square and places the stone enforced by the API.
4. If no legal moves exist, the player automatically passes and the turn goes to the opponent.

## API Results
- `yes`: You must place a YES stone (black). If the current player is also black, the move behaves like normal Othello and flips captured stones. If the current player is white, you still place the YES stone but cannot flip anything because it is not your color.
- `no`: Same logic but with the NO stone (white). Matching colors flip normally; mismatched colors simply place the opponent’s stone without flips.
- `maybe`: You place your own color, flip normally, and then **every adjacent opponent stone** (all 8 directions) is forcibly flipped to your color. The board briefly flashes to highlight the effect.

## Endgame and Victory
- The game ends when both players pass in a row or the board has no empty cells.
- Count the stones; the higher total wins. A tie is a draw.

## Controls
- Click a board cell during your turn to attempt a move.
- If **GIF popup mode** is enabled, a yesno.wtf GIF appears before each placement; click or press any key to close it.
- Closing the window quits the game immediately and prints the winner (if any) to the terminal.

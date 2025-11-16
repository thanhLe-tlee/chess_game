# Chess Game

A fully-featured chess game built with Python and Pygame, supporting local and online multiplayer modes with AI opponents.

## Features

### Game Modes
- **Online Multiplayer** - Play against opponents over a network with random color assignment
- **Local 2 Player** - Play with a friend on the same computer
- **Play vs Computer** - Challenge an AI opponent (Easy/Hard difficulty)
- **Computer vs Computer** - Watch AI play against itself

### Key Features
- ✅ Complete chess rules (castling, en passant, pawn promotion, check/checkmate, stalemate, draw by repetition)
- ⏱️ Chess timers (10 minutes per player)
- 🎨 Move highlighting (last move, selected piece, valid moves)
- 🎵 Sound effects for moves and game events
- 🎬 Smooth piece animations
- ⚔️ Rematch functionality in online games

## Installation

1. Clone the repository:
```bash
git clone https://github.com/thanhLe-tlee/chess_game.git
cd chess_game
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start Local Game
```bash
python chessMain.py
```

### Start Online Game
1. Start the server:
```bash
python server.py
```

2. Both players run `python chessMain.py` and select "PLAY ONLINE (Network)"

### Controls
- **Mouse** - Select and move pieces
- **P** - Pause (local modes)
- **Z** - Undo move (local modes)
- **ESC** - Cancel rematch (online mode)

## Project Structure

```
chess_game/
├── chessMain.py          # Main game loop and UI
├── chess_engine.py       # Chess logic and rules
├── smartMoveFinder.py    # AI implementation
├── network.py            # Network client
├── server.py             # Multiplayer server
├── images/ & images1/    # Chess piece graphics
└── SFX/                  # Sound effects
```

## Credits

Developed by **Le Quang Thanh (2252749)** & **Doan The Anh (2252019)**

Part of HCMUT Game Programming course (Assignment 4).

## License

This project is for educational purposes.

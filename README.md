# Chess Game

A fully-featured chess game built with Python and Pygame, supporting local and online multiplayer modes, AI opponents, and comprehensive game features.

## Features

### Game Modes
- **Online Multiplayer (Network)** - Play against opponents over a network
- **Local 2 Player** - Play with a friend on the same computer
- **Play vs Computer** - Challenge an AI opponent (Easy/Hard difficulty)
- **Computer vs Computer** - Watch AI play against itself

### Gameplay Features
- ✅ Full chess rules implementation including:
  - Castling (King-side and Queen-side)
  - En passant capture
  - Pawn promotion (choose Queen, Rook, Bishop, or Knight)
  - Check and checkmate detection
  - Stalemate detection
  - Draw by threefold repetition
- ⏱️ Chess timers (10 minutes per player)
- 🎨 Move highlighting (last move, selected piece, valid moves)
- 🎵 Sound effects for moves, captures, checks, and game events
- 🎬 Smooth piece animations
- ⚔️ Rematch functionality in online games
- 🎲 Random color assignment for online matches

### Visual Features
- Clean, modern UI with hover effects
- Timer display panel
- Game over menu with results
- Pause menu (local games)
- Countdown before game start
- Board orientation (flipped for black player in online games)

## Requirements

```
pygame
```

See `requirements.txt` for full dependencies.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/thanhLe-tlee/chess_game.git
cd chess_game
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting a Game

Run the main game:
```bash
python chessMain.py
```

### Online Multiplayer

1. Start the server:
```bash
python server.py
```

2. Players launch the game and select "PLAY ONLINE (Network)"
3. Both players connect to the server
4. Colors are randomly assigned
5. Game starts with a 3-second countdown

### Server Configuration

Configure the server using environment variables:
```bash
# Set custom host and port
set CHESS_SERVER_HOST=192.168.1.100
set CHESS_SERVER_PORT=5000
python server.py
```

Default settings:
- Host: `0.0.0.0` (accepts connections from any IP)
- Port: `5000`

## Controls

### Keyboard
- **Mouse Click** - Select and move pieces
- **P** - Pause game (local modes)
- **Z** - Undo last move (local modes)
- **R** - Return to main menu (local modes)
- **ESC** - Cancel rematch request (online mode)

### Game Over Options
- **REMATCH** - Start a new game with the same opponent (online mode)
- **QUIT TO MENU** - Return to main menu

## File Structure

```
chess_game/
├── chessMain.py          # Main game loop and UI
├── chess_engine.py       # Chess logic and game state
├── smartMoveFinder.py    # AI move calculation
├── network.py            # Network client for online play
├── server.py             # Multiplayer server
├── requirements.txt      # Python dependencies
├── images/               # Chess piece images (set 1)
├── images1/              # Chess piece images (set 2)
├── SFX/                  # Sound effects
└── README.md            # This file
```

## Game Architecture

### Core Components

**chessMain.py**
- Main game loop
- UI rendering and event handling
- Menu systems
- Game mode coordination

**chess_engine.py**
- Chess board representation
- Move generation and validation
- Game state management
- Check/checkmate/stalemate detection

**smartMoveFinder.py**
- AI move evaluation
- Minimax algorithm with alpha-beta pruning
- Position scoring

**network.py**
- Client-side networking
- Server communication
- Game state synchronization

**server.py**
- Multiplayer server
- Connection management
- Game session handling
- Rematch coordination

## AI Difficulty

### Easy Mode
- Uses basic minimax algorithm (depth 2)
- Evaluates material and position
- Suitable for beginners

### Hard Mode
- Advanced minimax with alpha-beta pruning (depth 3+)
- Better position evaluation
- More challenging opponent

## Online Game Flow

1. **Connection Phase**
   - Players connect to server
   - Random color assignment
   - Wait for both players

2. **Game Phase**
   - Synchronized game start countdown
   - Turn-based gameplay
   - Real-time move synchronization
   - Timer countdown

3. **Game Over**
   - Results display
   - Rematch option (20-second timeout)
   - Synchronized rematch start

## Known Issues & Limitations

- Server requires manual restart between game sessions
- Network connection lost if client disconnects abruptly
- No spectator mode
- No move history display

## Future Enhancements

- [ ] Move history panel
- [ ] Save/load game functionality
- [ ] Multiple difficulty levels for AI
- [ ] Opening book for AI
- [ ] Player profiles and statistics
- [ ] Game replay feature
- [ ] Chat functionality in online games
- [ ] Tournament mode

## Credits

Developed by **Le Quang Thanh (2252749)** & **Doan The Anh (2252019)**

Developed as part of HCMUT Game Programming course (Assignment 4).

## License

This project is for educational purposes.

## Contributing

Feel free to fork and submit pull requests for improvements!

## Support

For issues or questions, please open an issue on GitHub.

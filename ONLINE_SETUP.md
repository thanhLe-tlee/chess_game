# Online Chess Game Setup Guide

## Overview
Your chess game now supports online multiplayer! Players can connect over the internet to play against each other.

## Quick Start (Local Network Testing)

### 1. Start the Server
```bash
python chess_server.py
```
The server will start and display:
```
Chess Server started on 0.0.0.0:5555
Waiting for connections...
```

### 2. Start the Game Client (on each player's computer)
```bash
python chessMain.py
```
- Select "PLAY ONLINE (Network)" from the menu
- The first player will be assigned WHITE
- The second player will be assigned BLACK
- The game starts when both players are connected!

## Internet Setup (Play Over the Internet)

### Server Setup (Host's Computer)

#### Step 1: Configure the Server
The server is already configured to accept connections from any IP (`0.0.0.0`).

#### Step 2: Port Forwarding
You need to configure your router to forward port 5555 to your computer:

1. Find your local IP address:
   - Windows: Open Command Prompt, type `ipconfig`
   - Look for "IPv4 Address" (e.g., 192.168.1.100)

2. Access your router settings:
   - Usually at http://192.168.1.1 or http://192.168.0.1
   - Login with router admin credentials

3. Add port forwarding rule:
   - External Port: 5555
   - Internal Port: 5555
   - Internal IP: Your computer's local IP (from step 1)
   - Protocol: TCP

#### Step 3: Configure Firewall
Allow Python through Windows Firewall:
1. Windows Security → Firewall & network protection
2. Advanced settings → Inbound Rules
3. New Rule → Port → TCP → Specific port: 5555
4. Allow the connection

#### Step 4: Get Your Public IP
- Visit https://www.whatismyip.com/
- Copy your public IP address (e.g., 203.0.113.45)
- Share this IP with your opponents

#### Step 5: Start the Server
```bash
python chess_server.py
```

### Client Setup (Players' Computers)

#### Step 1: Edit network.py
Open `network.py` and change the server IP address:

```python
self.server = "203.0.113.45"  # Replace with actual server IP
```

#### Step 2: Start the Game
```bash
python chessMain.py
```
Select "PLAY ONLINE (Network)" from the menu.

## Architecture

### Server (`chess_server.py`)
- Manages multiple games simultaneously
- Handles matchmaking (pairs players automatically)
- Synchronizes game state between players
- Runs on port 5555 by default

### Client (`network.py`)
- Connects to the server
- Sends moves to server
- Receives opponent's moves
- Handles connection errors

### Game Flow
1. **Player 1 connects** → Server assigns WHITE, creates new game, waits for opponent
2. **Player 2 connects** → Server assigns BLACK, matches with Player 1
3. **Game starts** → Players take turns making moves
4. **Move made** → Client sends game state to server → Server updates → Other client receives update
5. **Game ends** → Players can disconnect

## Troubleshooting

### Connection Failed
- **Check server IP**: Make sure clients are using the correct server IP
- **Check firewall**: Ensure port 5555 is allowed
- **Check port forwarding**: Verify router configuration
- **Test locally first**: Use `127.0.0.1` for local testing

### Waiting for Opponent
- The first player waits for a second player to join
- Game starts only when both players are connected

### Lag or Delays
- Check internet connection speed
- High latency can cause move delays
- Consider hosting server closer to players

### Game State Out of Sync
- Both players need the same game version
- If issues persist, restart both clients and server

## Security Notes
⚠️ **Important**: This is a basic implementation for educational purposes.

For production use, consider:
- Adding authentication
- Encrypting communications (SSL/TLS)
- Implementing reconnection logic
- Adding anti-cheat measures
- Rate limiting
- Input validation

## Advanced Configuration

### Change Server Port
Edit both files:

**chess_server.py:**
```python
server = ChessServer(host="0.0.0.0", port=YOUR_PORT)
```

**network.py:**
```python
self.port = YOUR_PORT
```

### Multiple Games
The server automatically handles multiple games:
- Games 0, 2, 4, ... (even numbered games)
- Games 1, 3, 5, ... (odd numbered games)
- Each game has 2 players (white and black)

## Technical Details

### Protocol
- Uses TCP sockets for reliable communication
- Data serialized with Python's `pickle` module
- Entire game state sent between client/server

### Threading
- Server uses threading to handle multiple clients
- Each client connection runs in its own thread
- Thread-safe operations with locks

### Matchmaking
- Simple FIFO (First In, First Out) matchmaking
- First player waits, second player joins
- Automatic color assignment (first=white, second=black)

## Support

For issues or questions:
1. Check that both server and client are running
2. Verify network configuration (IP, port, firewall)
3. Test with local connections first
4. Check server console for error messages

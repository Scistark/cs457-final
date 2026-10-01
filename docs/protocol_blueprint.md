# Connect 4  Protocol Blueprint

## Message Summary
| Message | Direction | Purpose |
|---|---|---|
| CONNECT | C → S | Client connects to server to join game|
| LOBBY_WAIT | S → C | Server tells client that their opponent has not arrived |
| GAME_START | S → C | Both clients get message informing them game has started |
| MOVE | C → S | Player whos turn it is selects the column to fill in |
| STATE_UPDATE | S → both | Server Cbecks if valid, and updates both clients with new placment |
| ERROR | S → C | Server sends retry message if client was invalid or data was currupted |
| DISCONNECT | C → S | Client tells server it intends on leaving |
| GAME_OVER | S → both |Server updates clients with a win/loss tie |

## Message Schemas

### CONNECT (client → server)
Client sends this to join a game.

* Wire:
```
{"msg_type":"CONNECT","player_id":"Alice","payload":{},"timestamp":1727000000}\n
```
* JSON Structure:
```json
{
  "msg_type": "CONNECT",   // string
  "player_id": "Alice",    // string, player's name
  "payload": {},           // empty
  "timestamp": 1727000000  // int
}
```

### LOBBY_WAIT (server → client)
Tells player 1 we're waiting on player 2.

* Wire:
```
{"msg_type":"LOBBY_WAIT","player_id":"SERVER","payload":{"message":"Waiting for Player 2"},"timestamp":1727000001}\n
```
* JSON Structure:
```json
{
  "msg_type": "LOBBY_WAIT",
  "player_id": "SERVER",
  "payload": {
    "message": "Waiting for Player 2"   // string
  },
  "timestamp": 1727000001
}
```

### GAME_START (server → client)
Game starts. Each player is told if they're X or O.

* Wire:
```
{"msg_type":"GAME_START","player_id":"SERVER","payload":{"your_number":1,"your_piece":"X","opponent":"Bob","first_turn":"Alice"},"timestamp":1727000010}\n
```
* JSON Structure:
```json
{
  "msg_type": "GAME_START",
  "player_id": "SERVER",
  "payload": {
    "your_number": 1,        // int, 1 or 2
    "your_piece": "X",       // string, "X" or "O"
    "opponent": "Bob",       // string
    "first_turn": "Alice"    // string, player 1 goes first
  },
  "timestamp": 1727000010
}
```

### MOVE (client → server)
Player picks a column. The server figures out which row it lands in.

* Wire:
```
{"msg_type":"MOVE","player_id":"Alice","payload":{"col":3},"timestamp":1727000015}\n
```
* JSON Structure:
```json
{
  "msg_type": "MOVE",
  "player_id": "Alice",
  "payload": {
    "col": 3        // int
  },
  "timestamp": 1727000015
}
```

### STATE_UPDATE (server → client)
Sent after every good move so both players see the same board.

* Wire:
```
{"msg_type":"STATE_UPDATE","player_id":"SERVER","payload":{"board":[[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,1,0,0,0]],"last_move":{"player_id":"Alice","row":5,"col":3},"active_player":"Bob"},"timestamp":1727000016}\n
```
* JSON Structure:
```json
{
  "msg_type": "STATE_UPDATE",
  "player_id": "SERVER",
  "payload": {
    "board": [[0,0,0,0,0,0,0], ...],   //int array
    "last_move": {
      "player_id": "Alice",            // string
      "row": 5,                        // int
      "col": 3                         // int
    },
    "active_player": "Bob"             // string
  },
  "timestamp": 1727000016
}
```

### ERROR (server → client)
Player did something wrong. Board doesn't change.

* Wire:
```
{"msg_type":"ERROR","player_id":"SERVER","payload":{"code":"NOT_YOUR_TURN","message":"Wait for Bob"},"timestamp":1727000017}\n
```
* JSON Structure:
```json
{
  "msg_type": "ERROR",
  "player_id": "SERVER",
  "payload": {
    "code": "NOT_YOUR_TURN",   // string, see list
    "message": "Wait for Bob"  // string
  },
  "timestamp": 1727000017
}
```
* Error codes: `NOT_YOUR_TURN`, `INVALID_COLUMN` (not 0-6), `COLUMN_FULL`, `MALFORMED_MESSAGE` (bad json/missing field), `ROOM_FULL` (3rd player)

### DISCONNECT (client → server)
Player quits. If mid-game, the other player wins by forfeit.

* Wire:
```
{"msg_type":"DISCONNECT","player_id":"Bob","payload":{"reason":"quit"},"timestamp":1727000030}\n
```
* JSON Structure:
```json
{
  "msg_type": "DISCONNECT",
  "player_id": "Bob",
  "payload": {
    "reason": "quit"   // string
  },
  "timestamp": 1727000030
}
```

### GAME_OVER (server → client)
Game's done. Says who won or if it's a draw, then the server resets.

* Wire:
```
{"msg_type":"GAME_OVER","player_id":"SERVER","payload":{"result":"WIN","winner":"Alice","board":[[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[1,1,1,1,2,2,2]]},"timestamp":1727000050}\n
```
* JSON Structure:
```json
{
  "msg_type": "GAME_OVER",
  "player_id": "SERVER",
  "payload": {
    "result": "WIN",        // string, win/draw
    "winner": "Alice",      // string, or null on draw
    "board": [[...]]        // 6x7 int array
  },
  "timestamp": 1727000050
}
```

## Framing & Wire Format

* Transport: TCP
* Serialization: JSON, UTF-8
* Framing Rule: Every message is one JSON object on one line, ending with \n.

One recv() might have multiple messages or only part of one . The \n marks where each message ends.

###example
```
{"msg_type":"CONNECT","player_id":"Alice","payload":{},"timestamp":1727000000}\n{"msg_type":"MOVE","player_id":"Alice","payload":{"col":3},"timestamp":1727000015}\n
```
this would be one message as it ends in \n

### Receiver logic
1. every time a recv() comes in, it is added to a buffer
2. if the buffer detects a /n it will turn that portion into a json object
3. leftover the leftovers wait in the buffer until another /n comes through signaling that the whole json object has been recived

## Connection Termination
### Graceful disconnect
- Client sends DISCONNECT before leaving. If a game is in progress, the other player wins.
- TCP FIN: client closes normally, so recv() gets 0 bytes (EOF). Server checks if not data and treats it as a disconnect. Without this check the loop runs forever.

### Abrupt disconnect
- client crashes or the network drops, so there's no clean close.
- Server catches these errors so it doesn't crash:
  - ConnectionResetError: client died
  - BrokenPipeError: tried to send to a closed client

### What the server does For any disconnect
- Other player wins (if mid-game)
- Close the socket
- Reset and wait for new players
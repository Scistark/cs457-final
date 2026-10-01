# Connect 4 FSM

```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> WAITING_FOR_PLAYERS: server starts
    WAITING_FOR_PLAYERS --> GAME_START: 2 players join
    GAME_START --> PLAYER_TURN: assign P1 X and P2 O
    PLAYER_TURN --> PLAYER_TURN: out of turn, send ERROR
    PLAYER_TURN --> EVALUATE_MOVE: move received
    EVALUATE_MOVE --> PLAYER_TURN: invalid move, send ERROR
    EVALUATE_MOVE --> PLAYER_TURN: no win, swap turn
    EVALUATE_MOVE --> GAME_OVER: win or draw
    PLAYER_TURN --> GAME_OVER: disconnect, opponent wins
    GAME_OVER --> CLEANUP: send results
    CLEANUP --> WAITING_FOR_PLAYERS: reset for next game
```

## States
- INIT: server starts
- WAITING_FOR_PLAYERS: waits for 2 players to connect
- GAME_START: assigns Player 1 X and Player 2 O
- PLAYER_TURN: waits for the current player's move
- EVALUATE_MOVE: checks the move, places the piece, checks for a win or draw
- GAME_OVER: sends the result to both players
- CLEANUP: closes sockets and resets the board
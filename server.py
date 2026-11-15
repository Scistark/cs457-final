"""Connect 4 server - CS 457 Sprint 3.

One thread per client. A single lock protects the board, turn, scores,
and FSM state so two threads can never process moves at the same time.
Messages are newline-delimited JSON (see docs/protocol_blueprint.md).
"""
import argparse
import json
import socket
import threading
import time

ROWS, COLS = 6, 7

# Shared game state (always accessed while holding `lock`)
lock = threading.Lock()
state = "INIT"
players = []        # [{"sock": socket, "name": str, "num": 1 or 2}]
board = []
current_turn = 1
scores = {}         # player name -> wins


def set_state(new_state):
    """Move the FSM to a new state and log the transition."""
    global state
    print(f"[FSM] {state} -> {new_state}")
    state = new_state


def send(sock, msg_type, payload):
    """Send one framed JSON message. Ignore errors from dead sockets."""
    msg = {"msg_type": msg_type, "player_id": "SERVER",
           "payload": payload, "timestamp": int(time.time())}
    try:
        sock.sendall((json.dumps(msg) + "\n").encode())
    except OSError:
        pass


def broadcast(msg_type, payload):
    """Send the same message to every connected player."""
    for p in players:
        send(p["sock"], msg_type, payload)


def error(sock, code, message):
    send(sock, "ERROR", {"code": code, "message": message})


# ---------- Game logic ----------

def drop_piece(col, piece):
    """Drop a piece into a column. Return the row it lands in, or None if full."""
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == 0:
            board[row][col] = piece
            return row
    return None


def check_win(row, col, piece):
    """Check for 4 in a row through (row, col) in all four directions."""
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        count = 1
        for sign in (1, -1):
            r, c = row + dr * sign, col + dc * sign
            while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == piece:
                count += 1
                r, c = r + dr * sign, c + dc * sign
        if count >= 4:
            return True
    return False


def end_game(winner):
    """Send GAME_OVER, close both sockets, and reset for the next game.

    `winner` is a player dict, or None for a draw. Caller holds the lock.
    """
    set_state("GAME_OVER")
    if winner:
        scores[winner["name"]] += 1
    broadcast("GAME_OVER", {
        "result": "WIN" if winner else "DRAW",
        "winner": winner["name"] if winner else None,
        "board": board,
        "scores": scores,
    })

    set_state("CLEANUP")
    for p in players:
        try:
            p["sock"].shutdown(socket.SHUT_RDWR)  # wakes that client's thread
        except OSError:
            pass
    players.clear()
    set_state("WAITING_FOR_PLAYERS")


# ---------- Message handlers ----------

def on_connect(sock, name):
    """Add a player. Start the game once two players have joined."""
    global board, current_turn
    with lock:
        if len(players) >= 2:
            error(sock, "ROOM_FULL", "Game already has 2 players")
            return None

        player = {"sock": sock, "name": name, "num": len(players) + 1}
        players.append(player)
        scores.setdefault(name, 0)
        print(f"[SERVER] {name} joined as Player {player['num']}")

        if len(players) == 1:
            send(sock, "LOBBY_WAIT", {"message": "Waiting for Player 2"})
            return player

        # Two players: start the game
        set_state("GAME_START")
        board = [[0] * COLS for _ in range(ROWS)]
        current_turn = 1
        p1, p2 = players
        for me, opp in ((p1, p2), (p2, p1)):
            send(me["sock"], "GAME_START", {
                "your_number": me["num"],
                "your_piece": "X" if me["num"] == 1 else "O",
                "opponent": opp["name"],
                "first_turn": p1["name"],
            })
        set_state("PLAYER_TURN")
        return player


def on_move(player, payload):
    """Validate and apply a MOVE, then send STATE_UPDATE or GAME_OVER."""
    global current_turn
    with lock:
        if state != "PLAYER_TURN":
            return
        if player["num"] != current_turn:
            waiting_on = players[current_turn - 1]["name"]
            error(player["sock"], "NOT_YOUR_TURN", f"Wait for {waiting_on}")
            return

        col = payload.get("col") if isinstance(payload, dict) else None
        if not isinstance(col, int) or not 0 <= col < COLS:
            error(player["sock"], "INVALID_COLUMN", "Column must be 0-6")
            return

        set_state("EVALUATE_MOVE")
        row = drop_piece(col, player["num"])
        if row is None:
            error(player["sock"], "COLUMN_FULL", f"Column {col} is full")
            set_state("PLAYER_TURN")
            return

        if check_win(row, col, player["num"]):
            end_game(player)
            return
        if all(board[0][c] for c in range(COLS)):   # top row full = draw
            end_game(None)
            return

        current_turn = 3 - current_turn   # swap 1 <-> 2
        set_state("PLAYER_TURN")
        broadcast("STATE_UPDATE", {
            "board": board,
            "last_move": {"player_id": player["name"], "row": row, "col": col},
            "active_player": players[current_turn - 1]["name"],
        })


def on_disconnect(player):
    """Remove a player. If mid-game, the opponent wins by forfeit."""
    with lock:
        if player not in players:      # already cleaned up by end_game
            return
        print(f"[SERVER] {player['name']} disconnected")
        if len(players) == 2:
            other = players[0] if players[1] is player else players[1]
            end_game(other)
        else:
            players.remove(player)


# ---------- Per-client thread ----------

def handle_client(sock):
    """Read newline-framed JSON from one client and dispatch each message."""
    buffer = ""
    player = None
    try:
        while True:
            data = sock.recv(1024)
            if not data:               # client closed the connection
                break
            buffer += data.decode()

            # A recv may hold several messages or only part of one
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                try:
                    msg = json.loads(line)
                    msg_type, payload = msg["msg_type"], msg["payload"]
                except (ValueError, KeyError, TypeError):
                    error(sock, "MALFORMED_MESSAGE", "Bad JSON or missing field")
                    continue

                if msg_type == "CONNECT" and player is None:
                    player = on_connect(sock, str(msg["player_id"]))
                    if player is None:     # room full
                        return
                elif msg_type == "MOVE" and player:
                    on_move(player, payload)
                elif msg_type == "DISCONNECT":
                    return
    except (ConnectionResetError, BrokenPipeError, OSError):
        pass                           # abrupt disconnect
    finally:
        if player:
            on_disconnect(player)
        sock.close()


def main():
    parser = argparse.ArgumentParser(description="Connect 4 server")
    parser.add_argument("-p", "--port", type=int, required=True,
                        help="port to listen on")
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", args.port))
    server.listen()
    print(f"[SERVER] Listening on 0.0.0.0:{args.port}")
    set_state("WAITING_FOR_PLAYERS")

    try:
        while True:
            sock, addr = server.accept()
            print(f"[SERVER] Connection from {addr[0]}:{addr[1]}")
            threading.Thread(target=handle_client, args=(sock,),
                             daemon=True).start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down")
    finally:
        server.close()


if __name__ == "__main__":
    main()

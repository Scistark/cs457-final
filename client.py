"""Connect 4 client - CS 457 Sprint 3.

Connects to the server by DNS hostname, then reads newline-delimited
JSON messages and prompts for a column when it is this player's turn.
"""
import argparse
import json
import socket
import sys
import time

ROWS, COLS = 6, 7
PIECES = {0: ".", 1: "X", 2: "O"}


def send(sock, msg_type, name, payload):
    """Send one framed JSON message."""
    msg = {"msg_type": msg_type, "player_id": name,
           "payload": payload, "timestamp": int(time.time())}
    sock.sendall((json.dumps(msg) + "\n").encode())


def print_board(board):
    print()
    for row in board:
        print(" ".join(PIECES[cell] for cell in row))
    print(" ".join(str(c) for c in range(COLS)))
    print()


def ask_move(sock, name):
    """Prompt for a column and send MOVE. Return False if the player quits."""
    while True:
        choice = input(">>> Your Turn - pick a column 0-6 (q to quit): ").strip()
        if choice.lower() == "q":
            send(sock, "DISCONNECT", name, {"reason": "quit"})
            return False
        if choice.isdigit():
            send(sock, "MOVE", name, {"col": int(choice)})
            return True
        print("Please enter a number 0-6.")


def handle(sock, name, msg):
    """Handle one server message. Return False when the client should exit."""
    msg_type, p = msg["msg_type"], msg["payload"]

    if msg_type == "LOBBY_WAIT":
        print(p["message"] + "...")

    elif msg_type == "GAME_START":
        print(f"Game started! You are {p['your_piece']} vs {p['opponent']}.")
        print_board([[0] * COLS for _ in range(ROWS)])
        if p["first_turn"] == name:
            return ask_move(sock, name)
        print(f"Waiting for {p['opponent']}...")

    elif msg_type == "STATE_UPDATE":
        last = p["last_move"]
        print(f"{last['player_id']} dropped a piece in column {last['col']}.")
        print_board(p["board"])
        if p["active_player"] == name:
            return ask_move(sock, name)
        print(f"Waiting for {p['active_player']}...")

    elif msg_type == "ERROR":
        print(f"[ERROR] {p['message']}")
        if p["code"] in ("INVALID_COLUMN", "COLUMN_FULL"):
            return ask_move(sock, name)    # still our turn, try again
        if p["code"] == "ROOM_FULL":
            return False

    elif msg_type == "GAME_OVER":
        print_board(p["board"])
        if p["result"] == "DRAW":
            print("Game over: it's a draw!")
        elif p["winner"] == name:
            print("Game over: you win!")
        else:
            print(f"Game over: {p['winner']} wins.")
        print("Scores: " + ", ".join(f"{n}: {s}" for n, s in p["scores"].items()))
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Connect 4 client")
    parser.add_argument("-i", "--hostname", required=True,
                        help="server DNS hostname, e.g. server.schneckloth.edu")
    parser.add_argument("-p", "--port", type=int, required=True,
                        help="server port")
    args = parser.parse_args()

    # Resolve the hostname through DNS; fail cleanly if it can't be resolved
    try:
        server_ip = socket.gethostbyname(args.hostname)
    except socket.gaierror:
        print(f"[ERROR] Unable to resolve DNS hostname '{args.hostname}'.")
        print("Please check your Cisco router DNS configuration "
              "('ip dns server' / 'ip host') or verify domain spelling.")
        sys.exit(1)

    name = input("Enter your name: ").strip() or "Player"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, args.port))
    except OSError as e:
        print(f"[ERROR] Could not connect to {server_ip}:{args.port} ({e})")
        sys.exit(1)
    print(f"Connected to {args.hostname} ({server_ip}:{args.port})")
    send(sock, "CONNECT", name, {})

    buffer = ""
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("[INFO] Server closed the connection.")
                break
            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not handle(sock, name, json.loads(line)):
                    return
    except KeyboardInterrupt:
        try:
            send(sock, "DISCONNECT", name, {"reason": "quit"})
        except OSError:
            pass
    except (ConnectionResetError, BrokenPipeError):
        print("[ERROR] Lost connection to server.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()

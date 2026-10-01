# AI Prompts

## Strategy
I will upload my protocol_blueprint.md and fsm_specification.md with every prompt and tell it to follow them exactly. I ask for one small function at a time and check the output against my blueprint before using it.

## System Prompt
```
You are helping me build a Connect 4 game in Python using TCP sockets.
Follow my attached protocol_blueprint.md exactly.

Rules:
- Use only the Python standard library.
- Every message has exactly these fields: msg_type, player_id, payload, timestamp.
- Only use these message types: CONNECT, LOBBY_WAIT, GAME_START, MOVE, STATE_UPDATE, ERROR, DISCONNECT, GAME_OVER.
- MOVE payload only has col 0-6 The server finds the row.
- Do not add any fields or message types that are not in my blueprint.
- If something is confusing, ask me.
```

## Parser / Serializer Prompt
```
write two functions
1. encode_message(msg_type, player_id, payload) that returns the message as JSON bytes ending in a newline.
2. A receive function that adds incoming bytes to a buffer, splits on newline, parses each full line as JSON, and keeps any leftover partial message in the buffer.
If recv returns 0 bytes, treat it as a disconnect.
```

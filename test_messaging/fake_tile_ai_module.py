# Sends tile-drive commands (north/south/east/west) to the motor loop.
# Accepts WASD keys mapped to cardinal directions, or a multi-char sequence
# like "wwad" to queue several moves in a row. Not an AI, just a test driver.

from PiMessager import PiMessager
import sys

KEY_TO_DIRECTION = {
    "W": "north",
    "S": "south",
    "A": "west",
    "D": "east",
}

address = sys.argv[1] if len(sys.argv) > 1 else "tcp://localhost:5556"
messager = PiMessager(address=address)


while True:
    raw = input("Enter tile moves (WASD, e.g. 'wwad') or STOP: ").strip().upper()
    if not raw:
        continue
    if raw == "STOP":
        messager.send_message("STOP")
        continue
    for ch in raw:
        direction = KEY_TO_DIRECTION.get(ch)
        if direction is None:
            print(f"Skipping unrecognized key: {ch}")
            continue
        messager.send_message(direction)

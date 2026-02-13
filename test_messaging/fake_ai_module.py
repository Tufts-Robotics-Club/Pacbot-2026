# Just takes in WASD and spits out a direction. Not really an AI, but it works for testing.
from PiMessager import PiMessager
import sys

address = sys.argv[1] if len(sys.argv) > 1 else "tcp://localhost:5556"
messager = PiMessager(address=address)


while True:
    command = input("Enter a command (WASD): ").strip().upper()
    if command in ['W', 'A', 'S', 'D']:
        messager.send_message(command)
    else:
        messager.send_message("STOP")
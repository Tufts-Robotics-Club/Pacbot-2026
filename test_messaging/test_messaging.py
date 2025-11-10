from PiMessager import PiMessager
import sys

# Get address from command line argument if provided
address = sys.argv[1] if len(sys.argv) > 1 else "tcp://localhost:5555"

messager = PiMessager(address=address)

messager.send_message("Hello, Pi!")
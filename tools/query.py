"""Stub – forwards to entropy_table.commands.query."""
import sys
from entropy_table.commands.query import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

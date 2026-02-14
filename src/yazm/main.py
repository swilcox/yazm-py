import sys
from .zmachine import ZMachine


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <story-file>")
        sys.exit(1)
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    zm = ZMachine(data)
    zm.run()


if __name__ == "__main__":
    main()

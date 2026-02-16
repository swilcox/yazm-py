import argparse
from .zmachine import ZMachine


def main():
    parser = argparse.ArgumentParser(description="yazm - Yet Another Z-Machine")
    parser.add_argument("story_file", help="path to a Z-machine story file")
    parser.add_argument(
        "--no-highlight",
        action="store_true",
        help="disable bold cyan highlighting of object names",
    )
    args = parser.parse_args()

    with open(args.story_file, 'rb') as f:
        data = f.read()
    zm = ZMachine(data)
    zm.options.highlight_objects = not args.no_highlight
    zm.ui.init()
    try:
        zm.run()
    finally:
        zm.ui.reset()


if __name__ == "__main__":
    main()

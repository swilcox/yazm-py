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
    parser.add_argument(
        "--plain",
        action="store_true",
        help="disable all ANSI formatting for clean piped/diffable output",
    )
    args = parser.parse_args()

    with open(args.story_file, "rb") as f:
        data = f.read()
    zm = ZMachine(data)
    if args.plain:
        from .zui_std import ZUIStd

        zm.ui = ZUIStd(plain=True)
        zm.options.highlight_objects = False
    else:
        zm.options.highlight_objects = not args.no_highlight
        zm.ui.init()
    try:
        zm.run()
    finally:
        zm.ui.reset()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from config_parser import ParserError, MazeConfig, load_config


def main() -> None:
    try:
        config: MazeConfig = load_config()
        # this was just to test if the instance was coming through
        print(config.width)
    except ParserError as e:
        print(f"Error detected: {e}")


if __name__ == "__main__":
    main()

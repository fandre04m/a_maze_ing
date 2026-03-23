#!/usr/bin/env python3
from config_parser import ParserError, load_config


def main() -> None:
    try:
        load_config()
    except ParserError as e:
        print(f"Error detected: {e}")


if __name__ == "__main__":
    main()

from typing import cast, Dict, Union, Tuple


class ParserError(Exception):
    pass


class ConversionError(ParserError):
    pass


class ValidatorError(ParserError):
    pass


def _validator(
    config: Dict[str, Union[str, int, bool, tuple[int, int]]]
) -> None:
    width = cast(int, config["WIDTH"])
    height = cast(int, config["HEIGHT"])
    if width < 1 or height < 1:
        raise ValidatorError("WIDTH and HEIGHT minimum size is 1")
    if width * height < 2:
        raise ValidatorError(
            "WIDTH * HEIGHT must be at least 2 for ENTRY != EXIT"
        )
    if width > 100 or height > 100:
        raise ValidatorError(
            "Both WIDTH and HEIGHT have to be 100 or smaller"
        )
    entry_x, entry_y = cast(tuple, config["ENTRY"])
    exit_x, exit_y = cast(tuple, config["EXIT"])
    if entry_x == exit_x and entry_y == exit_y:
        raise ValidatorError(
            "ENTRY and EXIT cannot overlap"
        )
    if not (0 <= entry_x <= width) or not (0 <= entry_y <= height):
        raise ValidatorError(
            f"ENTRY{config["ENTRY"]} is out of bounds"
        )


def converter_validator(
    raw_config: Dict[str, str]
) -> Dict[str, Union[str, int, bool, tuple[int, int]]]:
    mandatory_keys = (
        "WIDTH",
        "HEIGHT",
        "ENTRY",
        "EXIT",
        "OUTPUT_FILE",
        "PERFECT"
    )
    # Check if all settings required are present in the raw data
    missing = [key for key in mandatory_keys if key not in raw_config]
    if missing:
        raise ConversionError(
            "Missing mandatory configurations in 'config.txt' - '"
            f"{'\', \''.join(missing)}'\n"
            "Mandatory: 'WIDTH', 'HEIGHT', 'ENTRY', "
            "'EXIT', 'OUTPUT_FILE', 'PERFECT'"
        )
    converted_config: Dict[str, Union[str, int, bool, tuple[int, int]]] = {}
    # Convert WIDTH and HEIGHT to integers
    try:
        converted_config["WIDTH"] = int(raw_config["WIDTH"])
        converted_config["HEIGHT"] = int(raw_config["HEIGHT"])
    except ValueError:
        raise ConversionError(
            "Both WIDTH and HEIGHT must be integers"
        )
    # Convert ENTRY and EXIT to tuples containing integers x and y

    def coord_converter(key: str) -> Tuple[int, int]:
        try:
            x, y = raw_config[key].split(",")
            return int(x), int(y)
        except ValueError:
            raise ConversionError(
                f"{key}={raw_config[key]} is invalid - "
                "Expects format 'x,y' with integers"
            )
    converted_config["ENTRY"] = coord_converter("ENTRY")
    converted_config["EXIT"] = coord_converter("EXIT")
    # OUTPUT_FILE is already str, just pass through, validate later
    converted_config["OUTPUT_FILE"] = raw_config["OUTPUT_FILE"]
    # Convert PERFECT to boolean
    if raw_config["PERFECT"].lower() == "true":
        converted_config["PERFECT"] = True
    elif raw_config["PERFECT"].lower() == "false":
        converted_config["PERFECT"] = False
    else:
        raise ConversionError(
            f"PERFECT={raw_config["PERFECT"]} is invalid - "
            "Expects 'True' or 'False'"
        )
    _validator(converted_config)
    return converted_config


def load_config() -> None:
    try:
        with open("config.txt") as config:
            raw_config: Dict[str, str] = {}
            for num, line in enumerate(config, start=1):
                # Remove leading and ending line whitespaces
                line = line.strip()
                # Ignore blank lines and comments
                if not line or line.startswith("#"):
                    continue
                # Enforce KEY=VALUE format
                if "=" not in line:
                    raise ParserError(
                        f"Line {num} '{line}' has invalid format "
                        "(expected KEY=VALUE)"
                    )
                key, value = line.split("=", 1)
                # Normalize keys and values
                key = key.strip().upper()
                value = value.strip()
                # Check if duplicate
                if key in raw_config:
                    raise ParserError(
                        f"Line {num} '{line}' is a duplicate setting"
                    )
                raw_config[key] = value
    except FileNotFoundError as e:
        raise ParserError(
            "File not found 'config.txt'"
        ) from e
    except PermissionError as e:
        raise ParserError(
            "Not enough permissions to open 'config.txt'"
        ) from e
    valid_config: Dict[
        str, Union[str, int, bool, tuple[int, int]]
    ] = converter_validator(raw_config)
    print(valid_config)

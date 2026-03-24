from typing import cast, Dict, Union, Tuple


class ParserError(Exception):
    """Base exception for configuration parsing errors."""
    pass


class ConversionError(ParserError):
    """Raised when configuration values cannot be converted."""
    pass


class ValidatorError(ParserError):
    """Raised when configuration values fail validation checks."""
    pass


class MazeConfig:
    """
    Represents a validated maze configuration.

    Attributes:
        width: Maze width.
        height: Maze height.
        entry: Entry coordinates (x, y).
        exit: Exit coordinates (x, y).
        output: Output file name.
        perfect: Whether the maze is perfect.
    """
    def __init__(
        self,
        config: Dict[str, Union[str, int, bool, tuple[int, int]]]
    ) -> None:
        """
        Initialize a MazeConfig instance from a validated config dictionary.

        Args:
            config: Dictionary containing validated configuration values.
        """
        self.width = config["WIDTH"]
        self.height = config["HEIGHT"]
        self.entry = config["ENTRY"]
        self.exit = config["EXIT"]
        self.output = config["OUTPUT_FILE"]
        self.perfect = config["PERFECT"]


def config_validator(
    config: Dict[str, Union[str, int, bool, tuple[int, int]]]
) -> None:
    """
    Validate the converted configuration values.

    Checks dimensions, entry/exit constraints, and output file format.

    Args:
        config: Dictionary containing converted configuration values.

    Raises:
        ValidatorError: If any validation rule is violated.
    """
    # Check if maze is minimum of 1*2 (Subject to change)
    width = cast(int, config["WIDTH"])
    height = cast(int, config["HEIGHT"])
    if width < 1 or height < 1:
        raise ValidatorError("WIDTH and HEIGHT minimum size is 1")
    if width * height < 2:
        raise ValidatorError(
            "WIDTH * HEIGHT must be at least 2 for ENTRY != EXIT"
        )
    # Check if maze is not over 100*100 (Subject to change or removing)
    if width > 100 or height > 100:
        raise ValidatorError(
            "Both WIDTH and HEIGHT have to be 100 or smaller"
        )
    # Check if ENTRY and EXIT overlap
    entry_x, entry_y = cast(tuple, config["ENTRY"])
    exit_x, exit_y = cast(tuple, config["EXIT"])
    if entry_x == exit_x and entry_y == exit_y:
        raise ValidatorError(
            f"ENTRY={config["ENTRY"]} and EXIT={config["EXIT"]} "
            "are overlapping"
        )
    # Check if ENTRY or EXIT are out of bounds
    if not (0 <= entry_x <= width) or not (0 <= entry_y <= height):
        raise ValidatorError(
            f"ENTRY={config["ENTRY"]} is out of bounds"
        )
    # Check if OUTPUT_FILE is a valid format
    file_name = cast(str, config["OUTPUT_FILE"])
    if not file_name.endswith(".txt") or len(file_name) <= 4:
        raise ValidatorError(
            f"OUTPUT_FILE={config["OUTPUT_FILE"]} not valid file format - "
            "Expects 'example.txt'"
        )


def config_converter(
    raw_config: Dict[str, str]
) -> Dict[str, Union[str, int, bool, tuple[int, int]]]:
    """
    Convert raw string configuration values into typed values.

    Performs type conversions and basic validation before returning
    a structured configuration dictionary.

    Args:
        raw_config: Dictionary of raw configuration strings.

    Returns:
        A dictionary with properly typed configuration values.

    Raises:
        ConversionError: If a value cannot be converted.
        ValidatorError: If validation fails after conversion.
    """
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
    config_validator(converted_config)
    return converted_config


def load_config() -> MazeConfig:
    """
    Load, parse, convert, and validate the configuration file.

    Reads 'config.txt', processes its contents, and returns a validated
    MazeConfig instance.

    Returns:
        A MazeConfig object containing validated configuration data.

    Raises:
        ParserError: If the file cannot be read or has invalid syntax.
        ConversionError: If conversion of values fails.
        ValidatorError: If validation of values fails.
    """
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
    ] = config_converter(raw_config)
    maze_config: MazeConfig = MazeConfig(valid_config)
    return maze_config

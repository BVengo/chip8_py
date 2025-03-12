from argparse import ArgumentParser
import os

from chip8_py import Emulator


def init_argparse() -> ArgumentParser:
    parser = ArgumentParser(description="Run a CHIP-8 program.")

    # Add a positional argument to accept a single file
    parser.add_argument(
        "file",  # Positional argument name
        metavar="FILE",  # Displayed in the usage as FILE
        type=str,  # Expect a string (the file path)
        help="The CHIP-8 program file to run.",
    )

    return parser


def validate_args(args) -> bool:
    if args.file is None:
        print("Please provide a CHIP-8 program file.")
        return False

    return True


def validate_file(file_path: str) -> bool:
    if not file_path.endswith(".ch8"):
        print("Invalid file type. Please provide a CHIP-8 (.ch8) program file.")
        return False

    if not os.path.exists(file_path):
        print("File not found. Please provide a valid CHIP-8 program file.")
        return False

    return True


def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    if not validate_args(args):
        parser.print_usage()
        return

    if not validate_file(args.file):
        return

    emulator = Emulator()
    emulator.load_rom(args.file)
    emulator.run()


if __name__ == "__main__":
    main()

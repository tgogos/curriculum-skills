import pyfiglet

def print_colored_text(text: str, color_code: str) -> None:
    print(f"\033[{color_code}m{text}\033[0m")

def print_logo():
   logo = pyfiglet.figlet_format("SKILLCRAWL")
   print(logo)

def print_horizontal_line(length: int) -> None:
    print('=' * length)

def print_loading_line(length: int) -> None:
    print_colored_text('=' * length + '|] Loading...[|' + '=' * length, 33)

def print_horizontal_small_line(length: int) -> None:
    print('-' * length)

def print_green_line(length: int) -> None:
    print_colored_text('=' * length, 32)

def print_yellow_line(length: int) -> None:
    print_colored_text('=' * length, 33)

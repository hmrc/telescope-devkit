import fire
from rich.console import Console
from rich.markdown import Markdown


def get_full_class_name(obj: object) -> str:
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__

    return module + "." + obj.__class__.__name__


def display(lines: [], out) -> None:
    text = "\n".join(lines) + "\n"
    out.write(text)


def cli(target, name):
    fire.core.Display = display
    return fire.Fire(target, name=name)


def get_console():
    console = Console()

    return console


def print_exception(e: Exception) -> None:
    get_console().print(f"[red]ERROR: {e} ({get_full_class_name(e)})[/red]")


def print_markdown(content):
    console = Console()
    markdown = Markdown(content)
    console.print(markdown)

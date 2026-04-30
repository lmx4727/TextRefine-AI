from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, get_args, get_origin, get_type_hints

import click

echo = click.echo
Exit = click.exceptions.Exit


@dataclass(frozen=True)
class OptionInfo:
    default: Any
    param_decls: tuple[str, ...]
    help: str | None = None


def Option(default: Any = None, *param_decls: str, help: str | None = None) -> OptionInfo:
    return OptionInfo(default=default, param_decls=param_decls, help=help)


class Typer:
    def __init__(self, help: str | None = None, no_args_is_help: bool = False) -> None:
        self.click_command = click.Group(help=help, no_args_is_help=no_args_is_help)

    def command(self, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            command_name = name or func.__name__.replace("_", "-")
            command = click.Command(command_name, callback=func)
            for param in reversed(_option_params(func)):
                command.params.insert(0, param)
            self.click_command.add_command(command)
            return func

        return decorator

    def __call__(self) -> None:
        self.click_command()


def _option_params(func: Callable[..., Any]) -> list[click.Option]:
    signature = inspect.signature(func)
    hints = get_type_hints(func)
    params: list[click.Option] = []
    for name, parameter in signature.parameters.items():
        default = parameter.default
        if not isinstance(default, OptionInfo):
            continue
        declarations = default.param_decls or (f"--{name.replace('_', '-')}",)
        declarations = (*declarations, name)
        params.append(
            click.Option(
                declarations,
                default=default.default,
                required=default.default is ...,
                help=default.help,
                type=_click_type_for(hints.get(name)),
            )
        )
    return params


def _click_type_for(annotation: Any) -> click.ParamType | type:
    if annotation is None:
        return str
    origin = get_origin(annotation)
    if origin is not None:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if args:
            return _click_type_for(args[0])
    if annotation is Path:
        return click.Path(path_type=Path)
    if annotation is int:
        return int
    return str

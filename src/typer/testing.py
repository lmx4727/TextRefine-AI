from __future__ import annotations

from typing import Any

from click.testing import CliRunner as ClickCliRunner


class CliRunner(ClickCliRunner):
    def invoke(self, cli: Any, args: Any = None, **kwargs: Any):
        click_command = getattr(cli, "click_command", cli)
        return super().invoke(click_command, args=args, **kwargs)

from telemetry.telescope_devkit import APP_NAME
from telemetry.telescope_devkit.cli import get_console
from telemetry.telescope_devkit.git import TelescopeDevkitGitRepo
from telemetry.telescope_devkit.git import TelescopeDevkitGitRepoException

console = get_console()


class DevkitCli(object):
    @staticmethod
    def update(debug: bool = False) -> int:
        console.print(
            f"Going to update [bold blue]{APP_NAME}[/bold blue] to the latest version available..."
        )
        try:
            repo = TelescopeDevkitGitRepo(debug=debug)
            console.print(f"Current version: [yellow]{repo.current_version}[/yellow]")
            repo.update()
            console.print(f"New version: [yellow]{repo.current_version}[/yellow]")
            console.print(f"Update completed.")

            return 0
        except TelescopeDevkitGitRepoException as e:
            console.print(f"[red]ERROR: {e}")

            return 1
        pass

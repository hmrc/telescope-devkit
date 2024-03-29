from rich.table import Table

from telemetry.telescope_devkit.migration.checks import *


class MigrationChecklist(object):
    _checklist = []
    _console = get_console()

    def __init__(self):
        create_migration_checklist_logger()

    def _list(self, title: str) -> None:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("❯  " + title, justify="left")
        for c in self._checklist:
            table.add_row("☐  " + c.description)
        self._console.print(table)

    def _check(self, title: str) -> int:
        sts = Sts()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column(
            f"  ❯   {title} ([bold]{sts.account_name}[/bold])", justify="left"
        )
        checks = {"pass": 0, "fail": 0}
        for c in self._checklist:
            self._console.print(f"\n[yellow]☐ Check: {c.description}[/yellow]")
            if c.requires_manual_intervention():
                c.check_interactively()
            else:
                c.check()
            if c.is_successful():
                check_status = "[green]✔[/green]"
                self._console.print(f"{check_status} Pass")
                checks["pass"] += 1
            else:
                check_status = "[red]x[/red]"
                self._console.print(f"{check_status} Fail")
                checks["fail"] += 1
            table.add_row(f"[ {check_status} ] {c.description}")

        self._console.print("")
        self._console.print(table)

        self._console.print("\n[yellow]Status report:[/yellow]")
        self._console.print(f"* Environment: [bold]{sts.account_name}[/bold]")
        now = datetime.datetime.now()
        self._console.print(f"* Checklist performed on { now.ctime()}")
        self._console.print(
            f"* Checks: {checks['pass']} successful, {checks['fail']} failed."
        )
        if checks["fail"] > 0:
            self._console.print("* Outcome: [red]Environment is not healthy.[/red]\n")
            return_code = 1
        else:
            self._console.print("* Outcome: [green]Environment is healthy.[/green]\n")
            return_code = 0

        return return_code


class Phase1Cli(MigrationChecklist):
    def __init__(self):
        super().__init__()
        self._checklist = [
            TerraformBuild(),
            EcsStatusChecks(),
            KafkaConsumption(),
            ElasticSearchIngest(),
            NwtPublicWebUis(),
            WebopsPublicWebUis(),
        ]

    def list(self):
        """Display Phase 1 checks"""
        self._list("Phase 1 checklist")

    def check(self) -> int:
        """Execute Phase 1 checks"""
        return self._check("Phase 1 checklist")


class Phase1MetricsCli(MigrationChecklist):
    def __init__(self):
        super().__init__()
        self._checklist = [
            ClickhouseMetricsChecks(),
        ]

    def list(self):
        """Display Phase 1 Metrics checks"""
        self._list("Phase 1 Metrics checklist")

    def check(self) -> int:
        """Execute Phase 1 checks"""
        return self._check("Phase 1 Metrics checklist")


class Phase1SnapshotCli(MigrationChecklist):
    def __init__(self):
        super().__init__()
        self._checklist = [
            ClickhouseSnapshotGeneration(),
        ]

    def list(self):
        """Display Phase 1 Snapshot Generation"""
        self._list("Phase 1 Snapshot Generation")

    def check(self) -> int:
        """Execute Phase 1 Snapshot Generation"""
        return self._check("Phase 1 Snapshot Generation")


class Phase2PreCutoverCli(MigrationChecklist):
    def __init__(self):
        super().__init__()
        self._checklist = [
            TerraformBuild(),
            EcsStatusChecks(),
            KafkaConsumption(),
            ElasticSearchIngest(),
            NwtPublicWebUis(),
            WebopsPublicWebUis(),
            LogsDataIsValid(),
            MetricsDataIsValid(),
            SensuChecksAreRunningInWebops(),
        ]

    def list(self):
        """Display Phase 2 checks"""
        self._list("Phase 2 pre-cutover checklist")

    def check(self) -> int:
        """Execute Phase 2 checks"""
        return self._check("Phase 2 pre-cutover checklist")


class Phase2PostCutoverCli(MigrationChecklist):
    def __init__(self):
        super().__init__()
        self._checklist = [
            KafkaConsumption(),
            NwtPublicWebUisRedirectFromWebops(),
            SensuChecksAreRunningInWebops(),
        ]

    def list(self):
        """Display Phase 2 checks"""
        self._list("Phase 2 post-cutover checklist")

    def check(self) -> int:
        """Execute Phase 2 checks"""
        return self._check("Phase 2 post-cutover checklist")


class Phase3Cli(MigrationChecklist):
    def __init__(self):
        super().__init__()
        self._checklist = [
            NwtPublicWebUisRedirectFromWebops(),
            WebopsEc2InstancesHaveBeenDecommissioned(),
            SensuChecksAreRunningInWebops(),
        ]

    def list(self):
        """Display Phase 3 checks"""
        self._list("Phase 3 checklist")

    def check(self) -> int:
        """Execute Phase 3 checks"""
        return self._check("Phase 3 checklist")

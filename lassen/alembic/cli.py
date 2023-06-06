import shutil
from contextlib import contextmanager
from logging.config import fileConfig
from pathlib import Path
from tempfile import TemporaryDirectory

import click
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from lassen.alembic.io import (
    get_migration_path,
    get_sqlalchemy_base_subclasses,
    guess_package_name,
)
from lassen.alembic.runner import run_migrations_offline, run_migrations_online
from lassen.assets import get_asset_path


class AlembicManager:
    def __init__(self, package_name: str):
        self.config = Config(get_asset_path("alembic.ini"))
        self.package_name = package_name

    def upgrade(self, revision: str):
        with self.make_script_directory():
            with self.patch_migrations(self.config):
                command.upgrade(self.config, revision)

    def downgrade(self, revision: str):
        with self.make_script_directory():
            with self.patch_migrations(self.config):
                command.downgrade(self.config, revision)

    def revision(self, message=None, autogenerate=False):
        with self.make_script_directory():
            with self.patch_migrations(self.config):
                command.revision(
                    self.config, message=message, autogenerate=autogenerate
                )

    @contextmanager
    def make_script_directory(self):
        with TemporaryDirectory() as dir:
            # Copy over the script.py.mako file
            script_path = Path(dir) / "script.py.mako"
            shutil.copy(get_asset_path("script.py.mako"), script_path)

            # Update the script location in-place
            self.config.set_main_option("script_location", dir)

            # Alembic will create new migrations in the dir/versions directory
            # So we want this to two-way sync
            migration_path = Path(dir) / "versions"
            migration_path.symlink_to(get_migration_path(self.package_name))

            yield dir

    @contextmanager
    def patch_migrations(self, config: Config, offline_mode=False):
        # Interpret the config file for Python logging.
        # This line sets up loggers basically.
        fileConfig(str(config.config_file_name))

        # Exhaust the iterator to ensure that all sqlalchemy modules are mounted.
        found_models = list(get_sqlalchemy_base_subclasses(self.package_name))
        print(f"Auto-detected models: {found_models}")

        def run_migration(self):
            if offline_mode:
                run_migrations_offline()
            else:
                run_migrations_online()

        run_env_original = getattr(ScriptDirectory, "run_env")
        setattr(ScriptDirectory, "run_env", run_migration)

        yield

        # Restore
        setattr(ScriptDirectory, "run_env", run_env_original)


@click.group()
def main():
    pass


@main.command()
@click.argument("revision", default="head")
def upgrade(revision: str):
    package_name = guess_package_name()
    alembic_manager = AlembicManager(package_name)
    alembic_manager.upgrade(revision=revision)


@main.command()
@click.argument("revision", default="base")
def downgrade(revision: str):
    package_name = guess_package_name()
    alembic_manager = AlembicManager(package_name)
    alembic_manager.downgrade(revision=revision)


@main.command()
@click.option("--message", default=None)
@click.option("--autogenerate", is_flag=True, default=False)
def revision(message: str, autogenerate: bool):
    package_name = guess_package_name()
    alembic_manager = AlembicManager(package_name)
    alembic_manager.revision(message=message, autogenerate=autogenerate)

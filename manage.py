import os
import sys

from django.core.management import execute_from_command_line


def main() -> None:
    """Run the Django management command given on the command line."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
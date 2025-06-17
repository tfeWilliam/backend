#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from hairbnb_backend.settings import BASE_DIR


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hairbnb_backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,  # Timeout pour éviter les erreurs en cas de concurrence
                'foreign_keys': True  # Activer les clés étrangères
            },
        }
    }


if __name__ == '__main__':
    main()

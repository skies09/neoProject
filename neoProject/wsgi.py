"""
WSGI config for neoProject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neoProject.settings")

# If Render’s Start Command was overridden and skips `migrate`, schema can stay on varchar(8).
# Default: run migrate once per process when ENV=PROD. Set RUN_MIGRATE_ON_BOOT=false to disable.
_flag = os.environ.get("RUN_MIGRATE_ON_BOOT")
if _flag is None:
    _flag = "true" if os.environ.get("ENV") == "PROD" else "false"
if _flag.lower() in ("1", "true", "yes"):
    import django

    django.setup()
    from django.core.management import call_command

    call_command("migrate", "--noinput", verbosity=0)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

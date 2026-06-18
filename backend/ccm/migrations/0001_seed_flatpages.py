from django.conf import settings
from django.db import migrations

# URLs of the flatpages that back the admin-configurable banner and footer.
# These are looked up by the ccm_globals context processor; they are never
# served at their own URL (no FlatpageFallbackMiddleware).
BANNER_URL = '/banner/'
FOOTER_URL = '/footer/'

SEED_PAGES = (
    (BANNER_URL, 'Site Banner'),
    (FOOTER_URL, 'Site Footer'),
)


def seed_flatpages(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    FlatPage = apps.get_model('flatpages', 'FlatPage')

    site, _ = Site.objects.get_or_create(id=getattr(settings, 'SITE_ID', 1))
    for url, title in SEED_PAGES:
        page, _ = FlatPage.objects.get_or_create(
            url=url,
            defaults={'title': title, 'content': ''},
        )
        page.sites.add(site)


def remove_flatpages(apps, schema_editor):
    FlatPage = apps.get_model('flatpages', 'FlatPage')
    FlatPage.objects.filter(url__in=[BANNER_URL, FOOTER_URL]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '__first__'),
        ('flatpages', '__first__'),
    ]

    operations = [
        migrations.RunPython(seed_flatpages, remove_flatpages),
    ]

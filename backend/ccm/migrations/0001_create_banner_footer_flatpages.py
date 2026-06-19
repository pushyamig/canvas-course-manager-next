from django.db import migrations


def create_default_banner_footer(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    FlatPage = apps.get_model('flatpages', 'FlatPage')

    site, _ = Site.objects.get_or_create(
        id=1,
        defaults={
            'domain': 'example.com',
            'name': 'example.com',
        },
    )

    banner_page, _ = FlatPage.objects.get_or_create(
        url='/banner/',
        defaults={
            'title': 'Banner',
            'content': '',
            'enable_comments': False,
            'registration_required': False,
            'template_name': '',
        },
    )
    banner_page.sites.add(site)

    footer_page, _ = FlatPage.objects.get_or_create(
        url='/footer/',
        defaults={
            'title': 'Footer',
            'content': '',
            'enable_comments': False,
            'registration_required': False,
            'template_name': '',
        },
    )
    footer_page.sites.add(site)


def delete_default_banner_footer(apps, schema_editor):
    FlatPage = apps.get_model('flatpages', 'FlatPage')
    FlatPage.objects.filter(url__in=['/banner/', '/footer/']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('flatpages', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_banner_footer, delete_default_banner_footer),
    ]

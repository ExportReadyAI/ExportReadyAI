# Generated manually to remove estimated_duration_minutes column

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('educational_materials', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE modules DROP COLUMN IF EXISTS estimated_duration_minutes;",
            reverse_sql="ALTER TABLE modules ADD COLUMN estimated_duration_minutes INTEGER;",
        ),
    ]


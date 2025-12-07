# Generated manually to remove old columns from simplified models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('educational_materials', '0002_remove_estimated_duration_minutes'),
    ]

    operations = [
        # Remove learning_path_id from modules table
        migrations.RunSQL(
            sql="ALTER TABLE modules DROP COLUMN IF EXISTS learning_path_id CASCADE;",
            reverse_sql="ALTER TABLE modules ADD COLUMN learning_path_id INTEGER;",
        ),
        # Remove any other old columns that might exist
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    -- Remove learning_path_id if it exists
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='modules' AND column_name='learning_path_id') THEN
                        ALTER TABLE modules DROP COLUMN learning_path_id CASCADE;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]


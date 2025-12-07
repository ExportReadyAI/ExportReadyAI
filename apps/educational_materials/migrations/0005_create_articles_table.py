# Generated manually to create articles table if it doesn't exist

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('educational_materials', '0004_cleanup_all_old_columns'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS articles (
                    id BIGSERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    video_url VARCHAR(500),
                    file_url VARCHAR(500),
                    order_index INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    module_id BIGINT NOT NULL REFERENCES modules(id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS articles_module__e6c6ae_idx ON articles(module_id, order_index);
            """,
            reverse_sql="DROP TABLE IF EXISTS articles CASCADE;",
        ),
    ]


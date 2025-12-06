# Generated manually to remove all old/irrelevant columns

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('educational_materials', '0003_remove_old_columns'),
    ]

    operations = [
        # Remove all old columns from modules table
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    -- Remove learning_path_id if it exists
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='modules' AND column_name='learning_path_id') THEN
                        ALTER TABLE modules DROP COLUMN learning_path_id CASCADE;
                    END IF;
                    
                    -- Remove estimated_duration_minutes if it exists
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='modules' AND column_name='estimated_duration_minutes') THEN
                        ALTER TABLE modules DROP COLUMN estimated_duration_minutes;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Remove all old columns from articles table (if it was called 'lessons' before)
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    -- Remove content_type if it exists (old lesson field)
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='articles' AND column_name='content_type') THEN
                        ALTER TABLE articles DROP COLUMN content_type;
                    END IF;
                    
                    -- Remove content_body if it exists (should be 'content' now)
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='articles' AND column_name='content_body') THEN
                        ALTER TABLE articles DROP COLUMN content_body;
                    END IF;
                    
                    -- Remove duration_minutes if it exists
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='articles' AND column_name='duration_minutes') THEN
                        ALTER TABLE articles DROP COLUMN duration_minutes;
                    END IF;
                    
                    -- Remove is_mandatory if it exists
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='articles' AND column_name='is_mandatory') THEN
                        ALTER TABLE articles DROP COLUMN is_mandatory;
                    END IF;
                    
                    -- Remove prerequisite_lesson_id if it exists
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='articles' AND column_name='prerequisite_lesson_id') THEN
                        ALTER TABLE articles DROP COLUMN prerequisite_lesson_id;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]


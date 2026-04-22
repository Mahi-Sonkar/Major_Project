# Generated migration for evaluation fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0002_answer_uploaded_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='examsubmission',
            name='evaluated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='examsubmission',
            name='evaluation_error',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='evaluation_data',
            field=models.JSONField(blank=True, null=True, help_text='Detailed AI evaluation data'),
        ),
    ]

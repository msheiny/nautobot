# Generated by Django 3.2.15 on 2022-09-12 17:38

from django.db import migrations, models

import nautobot.core.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0050_customfield_grouping"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="task_queues",
            field=nautobot.core.models.fields.JSONArrayField(
                base_field=models.CharField(max_length=100, blank=True), blank=True, default=list
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="task_queues_override",
            field=models.BooleanField(default=False),
        ),
    ]

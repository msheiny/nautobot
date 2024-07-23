# Generated by Django 4.2.14 on 2024-07-18 16:08

import uuid

import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion

import nautobot.core.models.fields
import nautobot.extras.models.mixins
import nautobot.extras.utils


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("ipam", "0047_alter_ipaddress_role_alter_ipaddress_status_and_more"),
        ("dcim", "0062_module_data_migration"),
        ("extras", "0113_saved_views"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="CloudAccount",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("account_number", models.CharField(max_length=255)),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cloud_accounts",
                        to="dcim.manufacturer",
                    ),
                ),
                (
                    "secrets_group",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="extras.secretsgroup",
                    ),
                ),
                ("tags", nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "ordering": ["name"],
            },
            bases=(
                nautobot.extras.models.mixins.DynamicGroupMixin,
                nautobot.extras.models.mixins.NotesMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="CloudNetwork",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("extra_config", models.JSONField(blank=True, null=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                (
                    "cloud_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cloud_networks",
                        to="cloud.cloudaccount",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
            bases=(
                nautobot.extras.models.mixins.DynamicGroupMixin,
                nautobot.extras.models.mixins.NotesMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="CloudResourceType",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("config_schema", models.JSONField(blank=True, null=True)),
                (
                    "content_types",
                    models.ManyToManyField(
                        limit_choices_to=nautobot.extras.utils.FeatureQuery("cloud_resource_types"),
                        related_name="cloud_resource_types",
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cloud_resource_types",
                        to="dcim.manufacturer",
                    ),
                ),
                ("tags", nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "ordering": ["name"],
            },
            bases=(
                nautobot.extras.models.mixins.DynamicGroupMixin,
                nautobot.extras.models.mixins.NotesMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="CloudService",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("extra_config", models.JSONField(blank=True, null=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                (
                    "cloud_account",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cloud_services",
                        to="cloud.cloudaccount",
                    ),
                ),
                (
                    "cloud_network",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cloud_services",
                        to="cloud.cloudnetwork",
                    ),
                ),
                (
                    "cloud_resource_type",
                    nautobot.core.models.fields.ForeignKeyLimitedByContentTypes(
                        on_delete=django.db.models.deletion.PROTECT, to="cloud.cloudresourcetype"
                    ),
                ),
                ("tags", nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "ordering": ["name"],
            },
            bases=(
                nautobot.extras.models.mixins.DynamicGroupMixin,
                nautobot.extras.models.mixins.NotesMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="CloudNetworkPrefixAssignment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                (
                    "cloud_network",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prefix_assignments",
                        to="cloud.cloudnetwork",
                    ),
                ),
                (
                    "prefix",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cloud_network_assignments",
                        to="ipam.prefix",
                    ),
                ),
            ],
            options={
                "ordering": ["cloud_network", "prefix"],
                "unique_together": {("cloud_network", "prefix")},
            },
        ),
        migrations.AddField(
            model_name="cloudnetwork",
            name="cloud_resource_type",
            field=nautobot.core.models.fields.ForeignKeyLimitedByContentTypes(
                on_delete=django.db.models.deletion.PROTECT, to="cloud.cloudresourcetype"
            ),
        ),
        migrations.AddField(
            model_name="cloudnetwork",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="children",
                to="cloud.cloudnetwork",
            ),
        ),
        migrations.AddField(
            model_name="cloudnetwork",
            name="prefixes",
            field=models.ManyToManyField(
                blank=True,
                related_name="cloud_networks",
                through="cloud.CloudNetworkPrefixAssignment",
                to="ipam.prefix",
            ),
        ),
        migrations.AddField(
            model_name="cloudnetwork",
            name="tags",
            field=nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag"),
        ),
    ]

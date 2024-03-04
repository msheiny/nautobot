# Generated by Django 3.1.7 on 2021-04-01 06:35
import uuid

import django.core.serializers.json
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions
import taggit.managers

import nautobot.core.models.fields
import nautobot.extras.models.statuses
import nautobot.ipam.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
        ("extras", "0001_initial_part_1"),
        ("dcim", "0002_initial_part_2"),
    ]

    operations = [
        migrations.CreateModel(
            name="Aggregate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("network", nautobot.ipam.fields.VarbinaryIPField(db_index=True, max_length=16)),
                ("broadcast", nautobot.ipam.fields.VarbinaryIPField(db_index=True, max_length=16)),
                ("prefix_length", models.IntegerField(db_index=True)),
                ("date_added", models.DateField(blank=True, null=True)),
                ("description", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "ordering": ("network", "broadcast", "pk"),
            },
        ),
        migrations.CreateModel(
            name="IPAddress",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("host", nautobot.ipam.fields.VarbinaryIPField(db_index=True, max_length=16)),
                ("broadcast", nautobot.ipam.fields.VarbinaryIPField(db_index=True, max_length=16)),
                ("prefix_length", models.IntegerField(db_index=True)),
                ("role", models.CharField(blank=True, max_length=50)),
                ("assigned_object_id", models.UUIDField(blank=True, null=True)),
                (
                    "dns_name",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid",
                                message="Only alphanumeric characters, hyphens, periods, and underscores are allowed in DNS names",
                                regex="^[0-9A-Za-z._-]+$",
                            )
                        ],
                    ),
                ),
                ("description", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "verbose_name": "IP address",
                "verbose_name_plural": "IP addresses",
                "ordering": ("host", "prefix_length"),
            },
        ),
        migrations.CreateModel(
            name="Prefix",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("network", nautobot.ipam.fields.VarbinaryIPField(db_index=True, max_length=16)),
                ("broadcast", nautobot.ipam.fields.VarbinaryIPField(db_index=True, max_length=16)),
                ("prefix_length", models.IntegerField(db_index=True)),
                ("is_pool", models.BooleanField(default=False)),
                ("description", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "verbose_name_plural": "prefixes",
                "ordering": (
                    django.db.models.expressions.OrderBy(django.db.models.expressions.F("vrf__name"), nulls_first=True),
                    "network",
                    "prefix_length",
                ),
            },
        ),
        migrations.CreateModel(
            name="RIR",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("is_private", models.BooleanField(default=False)),
                ("description", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "verbose_name": "RIR",
                "verbose_name_plural": "RIRs",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("weight", nautobot.core.models.fields.PositiveSmallIntegerField(default=1000)),
                ("description", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "ordering": ["weight", "name"],
            },
        ),
        migrations.CreateModel(
            name="RouteTarget",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=21, unique=True)),
                ("description", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="VRF",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=100)),
                ("rd", models.CharField(blank=True, max_length=21, null=True, unique=True)),
                ("enforce_unique", models.BooleanField(default=True)),
                ("description", models.CharField(blank=True, max_length=200)),
                (
                    "export_targets",
                    models.ManyToManyField(blank=True, related_name="exporting_vrfs", to="ipam.RouteTarget"),
                ),
                (
                    "import_targets",
                    models.ManyToManyField(blank=True, related_name="importing_vrfs", to="ipam.RouteTarget"),
                ),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
                (
                    "tenant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vrfs",
                        to="tenancy.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "VRF",
                "verbose_name_plural": "VRFs",
                "ordering": ("name", "rd"),
            },
        ),
        migrations.CreateModel(
            name="VLANGroup",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(max_length=100)),
                ("description", models.CharField(blank=True, max_length=200)),
                (
                    "site",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vlan_groups",
                        to="dcim.site",
                    ),
                ),
            ],
            options={
                "verbose_name": "VLAN group",
                "verbose_name_plural": "VLAN groups",
                "ordering": ("site", "name"),
            },
        ),
        migrations.CreateModel(
            name="VLAN",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                (
                    "vid",
                    nautobot.core.models.fields.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(4094),
                        ]
                    ),
                ),
                ("name", models.CharField(max_length=64)),
                ("description", models.CharField(blank=True, max_length=200)),
                (
                    "group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vlans",
                        to="ipam.vlangroup",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="vlans",
                        to="ipam.role",
                    ),
                ),
                (
                    "site",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vlans",
                        to="dcim.site",
                    ),
                ),
                (
                    "status",
                    nautobot.extras.models.statuses.StatusField(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ipam_vlan_related",
                        to="extras.status",
                    ),
                ),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
                (
                    "tenant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vlans",
                        to="tenancy.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "VLAN",
                "verbose_name_plural": "VLANs",
                "ordering": ("site", "group", "vid"),
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=100)),
                ("protocol", models.CharField(max_length=50)),
                (
                    "ports",
                    nautobot.core.models.fields.JSONArrayField(
                        base_field=models.PositiveIntegerField(
                            validators=[
                                django.core.validators.MinValueValidator(1),
                                django.core.validators.MaxValueValidator(65535),
                            ]
                        )
                    ),
                ),
                ("description", models.CharField(blank=True, max_length=200)),
                (
                    "device",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="services",
                        to="dcim.device",
                    ),
                ),
                ("ipaddresses", models.ManyToManyField(blank=True, related_name="services", to="ipam.IPAddress")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "ordering": ("protocol", "ports"),
            },
        ),
    ]

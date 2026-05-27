from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_cleaneddataset_pipeline_history_savedpipeline'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Add created_by to Team (default=1 for any existing rows, table is empty so safe)
        migrations.AddField(
            model_name='team',
            name='created_by',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='owned_teams',
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),

        # 2. Shrink Team.name max_length from 255 → 100
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=100),
        ),

        # 3. Update TeamMembership.team FK — add related_name='memberships'
        migrations.AlterField(
            model_name='teammembership',
            name='team',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='memberships',
                to='app.team',
            ),
        ),

        # 4. Update TeamMembership.user FK — add related_name='team_memberships'
        migrations.AlterField(
            model_name='teammembership',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='team_memberships',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # 5. Shrink TeamMembership.role max_length from 20 → 10
        migrations.AlterField(
            model_name='teammembership',
            name='role',
            field=models.CharField(
                choices=[('admin', 'Admin'), ('member', 'Member')],
                default='member',
                max_length=10,
            ),
        ),

        # 6. Change UploadedFile.team on_delete from CASCADE → SET_NULL
        migrations.AlterField(
            model_name='uploadedfile',
            name='team',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='app.team',
            ),
        ),
    ]

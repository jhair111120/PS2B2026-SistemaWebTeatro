from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_usuario_is_2fa_enabled_usuario_totp_secret_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='admin_notif_reservas',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='admin_notif_ventas',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='admin_notif_soporte',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='admin_notif_reportes',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='ConfiguracionSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reserva_bloqueo_minutos', models.PositiveSmallIntegerField(default=15)),
            ],
            options={
                'verbose_name': 'Configuración del sistema',
                'verbose_name_plural': 'Configuración del sistema',
                'db_table': 'configuracion_sistema',
                'managed': True,
            },
        ),
    ]

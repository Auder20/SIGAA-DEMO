# Generated migration for demo refactoring

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('liquidacion', '0006_auto_20251120_1046'),
        ('afiliados', '0009_auto_20251120_1046'),
    ]

    operations = [
        # Rename DatosAdemacor to DatosOrganizacion
        migrations.RenameModel(
            old_name='DatosAdemacor',
            new_name='DatosOrganizacion',
        ),
        
        # Update the descripcion field default value
        migrations.AlterField(
            model_name='datosorganizacion',
            name='descripcion',
            field=models.CharField(default='organizacion', help_text='Tipo de datos - constante: organizacion', max_length=50),
        ),
    ]

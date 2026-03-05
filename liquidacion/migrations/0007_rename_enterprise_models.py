# Generated migration for demo refactoring

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('afiliados', '0010_rename_enterprise_models'),
        ('liquidacion', '0006_auto_20251120_1046'),
    ]

    operations = [
        # Rename SueldoAdemacor to SueldoOrganizacion
        migrations.RenameModel(
            old_name='SueldoAdemacor',
            new_name='SueldoOrganizacion',
        ),
        
        # Rename AporteAdemacor to AporteOrganizacion
        migrations.RenameModel(
            old_name='AporteAdemacor',
            new_name='AporteOrganizacion',
        ),
        
        # Rename BonificacionPagoAdemacor to BonificacionPagoOrganizacion
        migrations.RenameModel(
            old_name='BonificacionPagoAdemacor',
            new_name='BonificacionPagoOrganizacion',
        ),
        
        # Update foreign key references in SueldoOrganizacion
        migrations.RenameField(
            model_name='sueldoorganizacion',
            old_name='afiliado_ademacor',
            new_name='afiliado_organizacion',
        ),
        
        # Update foreign key references in AporteOrganizacion
        migrations.RenameField(
            model_name='aporteorganizacion',
            old_name='sueldo_ademacor',
            new_name='sueldo_organizacion',
        ),
        
        # Update foreign key references in BonificacionPagoOrganizacion
        migrations.RenameField(
            model_name='bonificacionpagoorganizacion',
            old_name='sueldo_ademacor',
            new_name='sueldo_organizacion',
        ),
    ]

from django.db.backends.mysql import base


class DatabaseWrapper(base.DatabaseWrapper):
    """Backend MySQL que permite versiones anteriores a MySQL 8."""
    
    def check_database_version_supported(self):
        # Deshabilitar verificación de versión para permitir MySQL 5.7
        pass

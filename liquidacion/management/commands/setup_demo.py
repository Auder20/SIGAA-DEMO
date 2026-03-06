from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import random
from faker import Faker
from datetime import datetime, timedelta

from afiliados.models import Afiliado, DatosOrganizacion
from liquidacion.models import (
    TablaSalarial, Sueldo, Aporte, SueldoOrganizacion, 
    AporteOrganizacion, ParametroLiquidacion, BonificacionPago
)
from users.models import User
from reportes.models import ReporteAportesTotales

User = get_user_model()
fake = Faker('es_CO')


class Command(BaseCommand):
    help = 'Configura el sistema SIGAA para demostración con datos ficticios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los datos existentes antes de crear los datos de demo',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando configuración de demo SIGAA...')
        
        with transaction.atomic():
            if options['reset']:
                self.reset_data()
            
            # 1. Crear parámetros por defecto
            self.create_parameters()
            
            # 2. Crear usuarios demo
            self.create_demo_users()
            
            # 3. Crear tabla salarial
            self.create_tabla_salarial()
            
            # 4. Crear afiliados ficticios
            self.create_affiliates()
            
            # 5. Crear sueldos y aportes
            self.create_salaries_and_contributions()
            
            # 6. Crear reportes de ejemplo
            self.create_sample_reports()
            
        self.stdout.write(
            self.style.SUCCESS('✅ Sistema SIGAA configurado exitosamente para demostración')
        )
        self.print_demo_info()

    def reset_data(self):
        """Elimina todos los datos existentes"""
        self.stdout.write('🗑️  Eliminando datos existentes...')
        
        ReporteAportesTotales.objects.all().delete()
        Aporte.objects.all().delete()
        AporteOrganizacion.objects.all().delete()
        BonificacionPago.objects.all().delete()
        Sueldo.objects.all().delete()
        SueldoOrganizacion.objects.all().delete()
        DatosOrganizacion.objects.all().delete()
        Afiliado.objects.all().delete()
        TablaSalarial.objects.all().delete()
        ParametroLiquidacion.objects.all().delete()
        
        # Eliminar usuarios no superuser
        User.objects.filter(is_superuser=False).delete()

    def create_parameters(self):
        """Crea parámetros configurables por defecto"""
        self.stdout.write('⚙️  Creando parámetros del sistema...')
        
        parameters = [
            # Aportes
            {
                'codigo': 'aporte_institucional',
                'nombre': 'Aporte Institucional',
                'tipo': 'APORTE',
                'valor_numerico': Decimal('1.00'),
            },
            {
                'codigo': 'aporte_fondo',
                'nombre': 'Aporte al Fondo',
                'tipo': 'APORTE',
                'valor_numerico': Decimal('0.20'),
            },
            # Bonificaciones
            {
                'codigo': 'bonif_anticiguedad_5',
                'nombre': 'Bonificación Antigüedad 5 años',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('5.00'),
            },
            {
                'codigo': 'bonif_anticiguedad_10',
                'nombre': 'Bonificación Antigüedad 10 años',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('10.00'),
            },
            {
                'codigo': 'bonif_anticiguedad_15',
                'nombre': 'Bonificación Antigüedad 15 años',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('15.00'),
            },
            {
                'codigo': 'bonif_educacion_maestria',
                'nombre': 'Bonificación Maestría',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('8.00'),
            },
            {
                'codigo': 'bonif_educacion_doctorado',
                'nombre': 'Bonificación Doctorado',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('12.00'),
            },
            {
                'codigo': 'bonif_cargo_rector',
                'nombre': 'Bonificación Cargo Rector',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('25.00'),
            },
            {
                'codigo': 'bonif_cargo_decano',
                'nombre': 'Bonificación Cargo Decano',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('20.00'),
            },
            {
                'codigo': 'bonif_cargo_director',
                'nombre': 'Bonificación Cargo Director',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('15.00'),
            },
            {
                'codigo': 'bonif_cargo_coordinador',
                'nombre': 'Bonificación Cargo Coordinador',
                'tipo': 'BONIF',
                'valor_numerico': Decimal('10.00'),
            },
        ]
        
        for param_data in parameters:
            ParametroLiquidacion.objects.get_or_create(
                codigo=param_data['codigo'],
                defaults=param_data
            )

    def create_demo_users(self):
        """Crea usuarios de demostración"""
        self.stdout.write('👥 Creando usuarios de demo...')
        
        users_data = [
            {
                'email': 'admin@demo.com',
                'username': 'admin_demo',
                'password': 'admin123',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True,
                'rol': 'admin',
            },
            {
                'email': 'analista@demo.com',
                'username': 'analista_demo',
                'password': 'analista123',
                'first_name': 'Ana',
                'last_name': 'López',
                'is_staff': True,
                'is_superuser': False,
                'rol': 'analista',
            },
            {
                'email': 'consultor@demo.com',
                'username': 'consultor_demo',
                'password': 'consultor123',
                'first_name': 'Carlos',
                'last_name': 'Oultante',
                'is_staff': False,
                'is_superuser': False,
                'rol': 'consultor',
            },
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'   ✅ Usuario creado: {user.username}')
                self.stdout.write(f'   ✅ Usuario creado: {user.email}')

    def create_tabla_salarial(self):
        """Crea tabla salarial para el año 2025"""
        self.stdout.write('💰 Creando tabla salarial 2025...')
        
        salarios_base = {
            'A': 1300000,
            'B': 1400000,
            '1': 1500000,
            '2': 1600000,
            '3': 1700000,
            '4': 1800000,
            '5': 1900000,
            '6': 2000000,
            '7': 2100000,
            '8': 2200000,
            '9': 2300000,
            '10': 2400000,
            '11': 2500000,
            '12': 2600000,
            '13': 2700000,
            '14': 2800000,
        }
        
        for grado, salario in salarios_base.items():
            TablaSalarial.objects.get_or_create(
                anio=2025,
                grado=grado,
                defaults={'salario_base': Decimal(str(salario))}
            )

    def create_affiliates(self):
        """Crea afiliados ficticios"""
        self.stdout.write('👨‍🏫 Creando afiliados ficticios...')
        
        # Lista de municipios colombianos
        municipios = [
            'Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena',
            'Cúcuta', 'Ibagué', 'Soledad', 'Bucaramanga', 'Soacha',
            'Santa Marta', 'Villavicencio', 'Manizales', 'Pereira',
            'Armenia', 'Neiva', 'Popayán', 'Valledupar', 'Montería',
            'Sincelejo', 'Tunja', 'Riohacha', 'Quibdó', 'Florencia'
        ]
        
        # Lista de cargos
        cargos = [
            'Rector', 'Decano', 'Director', 'Coordinador', 'Docente',
            'Vicerrector', 'Secretario Académico', 'Jefe de Departamento',
            'Asistente Administrativo', 'Consejero', 'Tutor'
        ]
        
        # Lista de títulos
        titulos_pregrado = [
            'Licenciatura en Matemáticas', 'Licenciatura en Español',
            'Licenciatura en Ciencias Sociales', 'Licenciatura en Biología',
            'Ingeniería de Sistemas', 'Administración de Empresas',
            'Psicología', 'Trabajo Social', 'Contaduría Pública'
        ]
        
        titulos_posgrado = [
            'Maestría en Educación', 'Maestría en Administración',
            'Maestría en Tecnología Educativa', 'Doctorado en Educación',
            'Especialización en Pedagogía', 'Especialización en Gestión',
            None, None  # Algunos sin posgrado
        ]
        
        # Crear 75 afiliados
        for i in range(75):
            # Generar cédula única
            while True:
                cedula = str(random.randint(10000000, 99999999))
                if not Afiliado.objects.filter(cedula=cedula).exists():
                    break
            
            # Generar fecha de nacimiento (entre 25 y 65 años)
            edad = random.randint(25, 65)
            fecha_nacimiento = datetime.now() - timedelta(days=edad * 365)
            
            # Generar fecha de ingreso (entre 1 y 30 años de antigüedad)
            anos_servicio = random.randint(1, 30)
            fecha_ingreso = datetime.now() - timedelta(days=anos_servicio * 365)
            
            # Seleccionar grado de escalafón
            grado = random.choice(['A', 'B'] + [str(i) for i in range(1, 15)])
            
            # Seleccionar título de posgrado
            titulo_posgrado = random.choice(titulos_posgrado)
            
            afiliado = Afiliado.objects.create(
                cedula=cedula,
                nombre_completo=fake.name(),
                municipio=random.choice(municipios),
                ciudad_de_nacimiento=random.choice(municipios),
                fecha_nacimiento=fecha_nacimiento.date(),
                edad=edad,
                estado_civil=random.choice(['soltero', 'casado', 'divorciado', 'viudo']),
                nombre_conyuge=fake.name() if random.random() > 0.3 else '',
                nombre_hijos=', '.join([fake.first_name() for _ in range(random.randint(0, 3))]) if random.random() > 0.4 else '',
                direccion=fake.address(),
                telefono=fake.phone_number(),
                email=fake.email(),
                grado_escalafon=grado,
                cargo_desempenado=random.choice(cargos),
                fecha_ingreso=fecha_ingreso.date(),
                anos_servicio=anos_servicio,
                titulo_pregrado=random.choice(titulos_pregrado),
                titulo_posgrado=titulo_posgrado,
                estudios_posgrado=fake.sentence() if titulo_posgrado else '',
                otros_titulos=fake.sentence() if random.random() > 0.7 else '',
                activo=random.random() > 0.05,  # 95% activos
            )
            
            # Crear algunos afiliados de organización externa (30% del total)
            if i < 25:  # Primeros 25 como organización externa
                DatosOrganizacion.objects.create(
                    cedula=cedula + '_ORG',  # Diferenciar con sufijo
                    nombre_completo=fake.name(),
                    municipio=random.choice(municipios),
                    ciudad_de_nacimiento=random.choice(municipios),
                    fecha_nacimiento=fecha_nacimiento.date(),
                    edad=edad,
                    estado_civil=random.choice(['soltero', 'casado', 'divorciado', 'viudo']),
                    nombre_conyuge=fake.name() if random.random() > 0.3 else '',
                    nombre_hijos=', '.join([fake.first_name() for _ in range(random.randint(0, 3))]) if random.random() > 0.4 else '',
                    direccion=fake.address(),
                    telefono=fake.phone_number(),
                    email=fake.email(),
                    grado_escalafon=grado,
                    cargo_desempenado=random.choice(cargos),
                    fecha_ingreso=fecha_ingreso.date(),
                    anos_servicio=anos_servicio,
                    titulo_pregrado=random.choice(titulos_pregrado),
                    titulo_posgrado=titulo_posgrado,
                    estudios_posgrado=fake.sentence() if titulo_posgrado else '',
                    otros_titulos=fake.sentence() if random.random() > 0.7 else '',
                    descripcion='organizacion',
                    activo=True,
                )

    def create_salaries_and_contributions(self):
        """Crea sueldos y aportes para los afiliados"""
        self.stdout.write('💵 Creando sueldos y aportes...')
        
        # Procesar afiliados regulares
        for afiliado in Afiliado.objects.filter(activo=True)[:60]:  # Primeros 60 activos
            try:
                sueldo, created = afiliado.crear_o_actualizar_sueldo(2025)
                if created:
                    self.stdout.write(f'   ✅ Sueldo creado: {afiliado.nombre_completo}')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Error creando sueldo para {afiliado.nombre_completo}: {e}')
        
        # Procesar afiliados de organización externa
        for afiliado_org in DatosOrganizacion.objects.filter(activo=True)[:20]:  # Primeros 20 activos
            try:
                sueldo, created = afiliado_org.crear_o_actualizar_sueldo(2025)
                if created:
                    self.stdout.write(f'   ✅ Sueldo organización creado: {afiliado_org.nombre_completo}')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Error creando sueldo organización para {afiliado_org.nombre_completo}: {e}')

    def create_sample_reports(self):
        """Crea reportes de ejemplo"""
        self.stdout.write('📊 Creando reportes de ejemplo...')
        
        # Crear reportes de demo
        reportes_data = [
            {
                'anio': 2025,
                'mes': 1,
                'cantidad_afiliados': 60,
                'cantidad_aportes_ademacor': 75,
                'cantidad_aportes_famecor': 25,
                'total_ademacor': Decimal('1500000'),
                'total_famecor': Decimal('300000'),
                'total_general': Decimal('1800000'),
            },
            {
                'anio': 2025,
                'mes': 2,
                'cantidad_afiliados': 62,
                'cantidad_aportes_ademacor': 78,
                'cantidad_aportes_famecor': 26,
                'total_ademacor': Decimal('1560000'),
                'total_famecor': Decimal('312000'),
                'total_general': Decimal('1872000'),
            },
            {
                'anio': 2025,
                'mes': 3,
                'cantidad_afiliados': 65,
                'cantidad_aportes_ademacor': 80,
                'cantidad_aportes_famecor': 27,
                'total_ademacor': Decimal('1600000'),
                'total_famecor': Decimal('320000'),
                'total_general': Decimal('1920000'),
            },
        ]
        
        for report_data in reportes_data:
            ReporteAportesTotales.objects.get_or_create(
                anio=report_data['anio'],
                mes=report_data['mes'],
                defaults=report_data
            )

    def print_demo_info(self):
        """Imprime información de acceso para la demo"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('🎯 INFORMACIÓN DE ACCESO - DEMO SIGAA')
        self.stdout.write('='*60)
        self.stdout.write('\n📧 USUARIOS DE DEMOSTRACIÓN:')
        self.stdout.write('\n🔑 ADMINISTRADOR:')
        self.stdout.write('   Email: admin@demo.com')
        self.stdout.write('   Password: admin123')
        self.stdout.write('   Permisos: Superusuario')
        
        self.stdout.write('\n🔑 ANALISTA:')
        self.stdout.write('   Email: analista@demo.com')
        self.stdout.write('   Password: analista123')
        self.stdout.write('   Permisos: Staff')
        
        self.stdout.write('\n🔑 CONSULTOR:')
        self.stdout.write('   Email: consultor@demo.com')
        self.stdout.write('   Password: consultor123')
        self.stdout.write('   Permisos: Usuario regular')
        
        self.stdout.write('\n📊 DATOS CREADOS:')
        self.stdout.write(f'   • Afiliados: {Afiliado.objects.count()}')
        self.stdout.write(f'   • Afiliados Organización: {DatosOrganizacion.objects.count()}')
        self.stdout.write(f'   • Sueldos calculados: {Sueldo.objects.count()}')
        self.stdout.write(f'   • Sueldos Organización: {SueldoOrganizacion.objects.count()}')
        self.stdout.write(f'   • Aportes generados: {Aporte.objects.count()}')
        self.stdout.write(f'   • Reportes: {ReporteAportesTotales.objects.count()}')
        
        self.stdout.write('\n🚀 Para iniciar el servidor:')
        self.stdout.write('   python manage.py runserver')
        
        self.stdout.write('\n📝 Para ejecutar nuevamente:')
        self.stdout.write('   python manage.py setup_demo')
        self.stdout.write('   python manage.py setup_demo --reset  # (para limpiar y regenerar)')
        
        self.stdout.write('\n' + '='*60)

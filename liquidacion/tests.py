from django.test import TestCase
from afiliados.models import Afiliado
from .models import Sueldo, Aporte


class SueldoAporteSignalTest(TestCase):
    def setUp(self):
        self.af = Afiliado.objects.create(cedula='12345', nombre_completo='Test User')

    def test_aportes_created_on_sueldo_create(self):
        s = Sueldo.objects.create(afiliado=self.af, anio=2025, sueldo_neto=1000)
        aportes = list(Aporte.objects.filter(sueldo=s))
        self.assertEqual(len(aportes), 2)
        names = sorted([a.nombre for a in aportes])
        self.assertEqual(names, ['ADEMACOR', 'FAMICOR'])
        adem = Aporte.objects.get(sueldo=s, nombre='ADEMACOR')
        fam = Aporte.objects.get(sueldo=s, nombre='FAMICOR')
        self.assertAlmostEqual(float(adem.valor), 10.0)
        self.assertAlmostEqual(float(fam.valor), 2.0)
from django.test import TestCase

# Create your tests here.

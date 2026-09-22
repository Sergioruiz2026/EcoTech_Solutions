import unittest
from datetime import date

from modelos.empleado import Empleado
from modelos.gerente import Gerente
from modelos.proyecto import Proyecto
from modelos.registro_tiempo import RegistroTiempo


class TestRegistroTiempo(unittest.TestCase):
    def test_jornada_mayor_a_12_deja_horas_extras_por_aprobar(self):
        empleado = Empleado(
            "Ana Soto",
            "ana@ecotech.cl",
            900000,
            "Dirección 123",
            "+56 9 1234 5678",
            date(2024, 1, 1),
        )
        proyecto = Proyecto("Proyecto Uno", "Descripcion", date(2026, 1, 1))
        gerente = Gerente(
            "Gerente Uno",
            "gerente@ecotech.cl",
            1200000,
            "Operaciones",
            "Dirección 456",
            "+56 9 8765 4321",
            date(2023, 1, 1),
        )

        registro = RegistroTiempo(
            date(2026, 3, 10),
            13.0,
            "Turno extendido",
            empleado,
            proyecto,
        )

        gerente.aprobar_horas(registro)

        self.assertEqual(registro.horas_aprobadas, 12.0)
        self.assertEqual(registro.horas_extras, 1.0)
        self.assertEqual(registro.horas_extras_por_aprobar, 1.0)
        self.assertEqual(registro.horas_pendientes, 1.0)
        self.assertFalse(registro.aprobado)


if __name__ == "__main__":
    unittest.main()

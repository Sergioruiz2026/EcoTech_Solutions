import unittest
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from unittest.mock import patch

from main import consultar_empleado, mostrar_empleados
from modelos.empleado import Empleado
from modelos.usuario import Usuario


class RepoEmpleadosFalso:
    def __init__(self, empleados):
        self.empleados = empleados

    def listar(self):
        return self.empleados

    def buscar_por_id(self, id_empleado):
        return next((empleado for empleado in self.empleados
                     if empleado.id == id_empleado), None)


class TestMainMasking(unittest.TestCase):
    def setUp(self):
        self.empleado = Empleado(
            "Ana Soto",
            "ana.soto@ecotech.cl",
            1500000,
            "Direccion 1",
            "+56 9 1234 5678",
            date(2024, 1, 1),
            id_empleado=1,
        )
        self.repo = RepoEmpleadosFalso([self.empleado])

    def test_mostrar_empleados_enmascara_correo_para_operador(self):
        operador = Usuario("ana", "Abcdef12", "operador", empleado=self.empleado)
        salida = StringIO()

        with redirect_stdout(salida):
            mostrar_empleados(self.repo, operador)

        texto = salida.getvalue()
        self.assertIn("a******o@ecotech.cl", texto)
        self.assertNotIn("ana.soto@ecotech.cl", texto)

    def test_consultar_empleado_enmascara_correo_para_operador(self):
        operador = Usuario("ana", "Abcdef12", "operador", empleado=self.empleado)
        salida = StringIO()

        with patch("builtins.input", return_value="1"), redirect_stdout(salida):
            consultar_empleado(self.repo, operador)

        texto = salida.getvalue()
        self.assertIn("a******o@ecotech.cl", texto)
        self.assertNotIn("ana.soto@ecotech.cl", texto)

    def test_mostrar_empleados_muestra_correo_para_gerente(self):
        gerente = Usuario("gerente", "Abcdef12", "gerente", empleado=self.empleado)
        salida = StringIO()

        with redirect_stdout(salida):
            mostrar_empleados(self.repo, gerente)

        self.assertIn("ana.soto@ecotech.cl", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
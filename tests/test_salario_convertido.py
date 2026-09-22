import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from main import consultar_salario_convertido
from modelos.empleado import Empleado
from modelos.usuario import Usuario


class RepoEmpleadosFalso:
    def __init__(self, empleado):
        self.empleado = empleado

    def buscar_por_id(self, identificador):
        return self.empleado if identificador == self.empleado.id else None


class RepoConsultasFalso:
    def __init__(self):
        self.ultima_consulta = None

    def crear(self, *argumentos):
        self.ultima_consulta = argumentos


class TestSalarioConvertido(unittest.TestCase):
    def setUp(self):
        self.empleado = Empleado(
            "Ana Soto", "ana@ecotech.cl", 900000, id_empleado=7)
        self.repo_empleados = RepoEmpleadosFalso(self.empleado)
        self.repo_consultas = RepoConsultasFalso()

    def test_gerente_ve_conversion_y_se_guarda(self):
        gerente = Usuario("gerente1", "ClaveSegura1", "gerente")
        with patch("main.input", side_effect=["7", "USD"]), \
                patch(
                    "main.ClienteApisExternas.consultar_tipo_cambio",
                    return_value={
                        "origen": "CLP", "destino": "USD",
                        "tipo_cambio": 0.0011}), \
                redirect_stdout(StringIO()) as salida:
            consultar_salario_convertido(
                gerente, self.repo_empleados, self.repo_consultas)

        self.assertIn("990.00 USD", salida.getvalue())
        self.assertEqual(
            self.repo_consultas.ultima_consulta[1], "salario_convertido")
        self.assertAlmostEqual(
            self.repo_consultas.ultima_consulta[3]["salario_convertido"],
            990.0)

    def test_operador_no_puede_consultar_salario(self):
        operador = Usuario("operador1", "ClaveSegura1", "operador")
        with patch("main.ClienteApisExternas.consultar_tipo_cambio") as consultar:
            consultar_salario_convertido(
                operador, self.repo_empleados, self.repo_consultas)

        consultar.assert_not_called()
        self.assertIsNone(self.repo_consultas.ultima_consulta)


if __name__ == "__main__":
    unittest.main()

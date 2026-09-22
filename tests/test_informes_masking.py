import unittest
from datetime import date
from io import BytesIO
from zipfile import ZipFile

from informes.informe_pdf import InformePDF
from informes.informe_excel import InformeExcel
from modelos.empleado import Empleado
from modelos.gerente import Gerente
from modelos.usuario import Usuario


class TestInformesMasking(unittest.TestCase):

    @staticmethod
    def _dato_empleado(nombre, salario):
        empleado = Empleado(
            nombre,
            f"{nombre.lower().replace(' ', '.')}@ecotech.cl",
            salario,
            "Direccion 1",
            "+56 9 1234 5678",
            date(2024, 1, 1),
            id_empleado=1,
        )
        return empleado

    def test_informe_pdf_mascara_salario_para_usuario_estandar(self):
        empleado = self._dato_empleado("Ana Soto", 1500000)
        usuario = Usuario("ana", "Abcdef12", "operador", empleado=empleado)
        datos = {"departamentos": [], "empleados": [empleado], "proyectos": [], "registros_horas": []}

        texto = InformePDF("Informe general EcoTech").generar_reporte(datos, usuario=usuario)

        self.assertIn("Ana Soto", texto)
        self.assertIn("Salario: $ *******", texto)
        self.assertIn("Correo: a******o@ecotech.cl", texto)
        self.assertNotIn("$ 1,500,000", texto)
        self.assertNotIn("ana.soto@ecotech.cl", texto)

    def test_informe_excel_muestra_salario_real_para_gerente(self):
        empleado = self._dato_empleado("Luis Perez", 1500000)
        gerente = Gerente(
            "Gerente Uno",
            "gerente@ecotech.cl",
            2200000,
            "Operaciones",
            "Direccion 2",
            "+56 9 8765 4321",
            date(2023, 1, 1),
            id_empleado=2,
        )
        usuario = Usuario("gerente", "Abcdef12", "gerente", empleado=gerente)
        datos = {"departamentos": [], "empleados": [empleado], "proyectos": [], "registros_horas": []}

        contenido = InformeExcel("Informe general EcoTech").generar_archivo(datos, usuario=usuario)

        with ZipFile(BytesIO(contenido), "r") as paquete:
            xml = paquete.read("xl/worksheets/sheet1.xml").decode("utf-8", "replace")

        self.assertIn("$ 1,500,000", xml)
        self.assertNotIn("$ *******", xml)
        self.assertIn("luis.perez@ecotech.cl", xml)
        self.assertTrue("*" not in xml or "luis.perez@ecotech.cl" in xml)


if __name__ == '__main__':
    unittest.main()

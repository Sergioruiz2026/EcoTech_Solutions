from datetime import date
from io import BytesIO
from zipfile import ZipFile

from informes.informe_pdf import InformePDF
from informes.informe_excel import InformeExcel
from modelos.empleado import Empleado
from modelos.gerente import Gerente
from modelos.usuario import Usuario


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


def test_informe_pdf_mascara_salario_para_usuario_estandar():
    empleado = _dato_empleado("Ana Soto", 1500000)
    usuario = Usuario("ana", "Abcdef12", "operador", empleado=empleado)
    datos = {"departamentos": [], "empleados": [empleado], "proyectos": [], "registros_horas": []}

    texto = InformePDF("Informe general EcoTech").generar_reporte(datos, usuario=usuario)

    assert "Ana Soto" in texto
    assert "Salario: $ *******" in texto
    assert "Correo: a******o@ecotech.cl" in texto
    assert "$ 1,500,000" not in texto
    assert "ana.soto@ecotech.cl" not in texto


def test_informe_excel_muestra_salario_real_para_gerente():
    empleado = _dato_empleado("Luis Perez", 1500000)
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

    assert "$ 1,500,000" in xml
    assert "$ *******" not in xml
    assert "luis.perez@ecotech.cl" in xml
    assert "*" not in xml or "luis.perez@ecotech.cl" in xml

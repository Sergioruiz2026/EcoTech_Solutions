"""InformeExcel: libro XLSX con todos los datos operativos."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

from informes.informe import Informe
from seguridad.validaciones import formatear_correo_informe, formatear_salario_informe


class InformeExcel(Informe):
    EXTENSION = "xlsx"
    TIPO = "Excel"

    @staticmethod
    def _filas(datos, usuario=None):
        filas = [["Tipo", "ID", "Nombre", "Correo", "Departamento", "Descripcion",
                  "Fecha inicio", "Fecha", "Horas", "Horas aprobadas", "Estado",
                  "Empleado", "Proyecto", "Salario"]]
        filas.extend([[
            "Departamento", departamento.id, departamento.nombre, "", "", "", "", "", "", "", "", "", "", ""
        ] for departamento in datos["departamentos"]])
        filas.extend([[
            "Empleado", empleado.id, empleado.nombre,
            formatear_correo_informe(empleado.correo, usuario),
            empleado.departamento.nombre if empleado.departamento else "", "", "", "", "", "", "", "", "",
            formatear_salario_informe(empleado.obtener_salario(), usuario)
        ] for empleado in datos["empleados"]])
        filas.extend([[
            "Proyecto", proyecto.id, proyecto.nombre, "", "", proyecto.descripcion,
            str(proyecto.fecha_inicio), "", "", "", "", "", "", ""
        ] for proyecto in datos["proyectos"]])
        filas.extend([[
            "Registro de horas", registro.id, "", "", "", registro.descripcion, "",
            str(registro.fecha), registro.horas, registro.horas_aprobadas, registro.estado,
            registro.empleado.nombre, registro.proyecto.nombre, ""
        ] for registro in datos["registros_horas"]])
        return filas

    def generar_reporte(self, datos, usuario=None):
        return "\n".join(";".join(str(valor) for valor in fila)
                         for fila in self._filas(datos, usuario=usuario))

    def generar_archivo(self, datos, usuario=None):
        """Construye un libro XLSX válido sin depender de librerías externas."""
        filas = self._filas(datos, usuario=usuario)

        def celda(valor, indice):
            if isinstance(valor, (int, float)):
                return f'<c r="{indice}" t="n"><v>{valor}</v></c>'
            texto = escape(str(valor))
            return f'<c r="{indice}" t="inlineStr"><is><t>{texto}</t></is></c>'

        filas_xml = []
        for numero_fila, fila in enumerate(filas, 1):
            celdas = []
            for numero_columna, valor in enumerate(fila):
                letra = ""
                columna = numero_columna + 1
                while columna:
                    columna, resto = divmod(columna - 1, 26)
                    letra = chr(65 + resto) + letra
                celdas.append(celda(valor, f"{letra}{numero_fila}"))
            filas_xml.append(f'<row r="{numero_fila}">' + "".join(celdas) + "</row>")

        hoja = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData>' + "".join(filas_xml) + "</sheetData></worksheet>")
        archivos = {
            "[Content_Types].xml": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                '</Types>'),
            "_rels/.rels": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                '</Relationships>'),
            "xl/workbook.xml": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Informe" sheetId="1" r:id="rId1"/></sheets></workbook>'),
            "xl/_rels/workbook.xml.rels": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '</Relationships>'),
            "xl/worksheets/sheet1.xml": hoja,
        }
        salida = BytesIO()
        with ZipFile(salida, "w", ZIP_DEFLATED) as libro:
            for nombre, contenido in archivos.items():
                libro.writestr(nombre, contenido)
        return salida.getvalue()
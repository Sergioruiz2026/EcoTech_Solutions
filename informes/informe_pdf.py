"""InformePDF: presentación legible de todos los datos operativos."""

from informes.informe import Informe
from seguridad.validaciones import formatear_correo_informe, formatear_salario_informe


class InformePDF(Informe):

    EXTENSION = "pdf"
    TIPO = "PDF"

    def generar_reporte(self, datos, usuario=None):
        lineas = [self.encabezado(), ""]
        departamentos = datos["departamentos"]
        empleados = datos["empleados"]
        proyectos = datos["proyectos"]
        registros = datos["registros_horas"]
        lineas.append(f"Departamentos ({len(departamentos)})")
        for departamento in departamentos:
            lineas.append(f"  {departamento.id}: {departamento.nombre}")
        lineas.append("")
        lineas.append(f"Empleados ({len(empleados)})")
        for empleado in empleados:
            departamento = empleado.departamento.nombre if empleado.departamento else "Sin departamento"
            salario = formatear_salario_informe(empleado.obtener_salario(), usuario)
            correo = formatear_correo_informe(empleado.correo, usuario)
            lineas.append(
                f"  {empleado.id}: {empleado.nombre} | Correo: {correo} | "
                f"{departamento} | Salario: {salario}"
            )
        lineas.append("")
        lineas.append(f"Proyectos ({len(proyectos)})")
        for proyecto in proyectos:
            lineas.append(f"  {proyecto.id}: {proyecto.nombre} | inicio {proyecto.fecha_inicio}")
        lineas.append("")
        lineas.append(f"Registros de horas ({len(registros)})")
        lineas.append("-" * 52)

        aprobadas = 0.0
        extras = 0.0
        for registro in registros:
            aprobadas += registro.horas_aprobadas
            extras += registro.horas_extras_por_aprobar
            if registro.estado == "parcial":
                estado = (f"parcial {registro.horas_aprobadas:g}/"
                          f"{registro.horas:g} h ({registro.horas_extras_por_aprobar:g} h extra por aprobar)")
            else:
                estado = "OK" if registro.estado == "aprobado" else "pendiente"
            lineas.append(f"  {registro.fecha}  {registro.horas:>5} h  "
                          f"{registro.empleado.nombre} | {registro.proyecto.nombre}  [{estado}]")

        lineas.append("-" * 52)
        total_horas = sum(registro.horas for registro in registros)
        lineas.append(f"  TOTAL registrado: {total_horas:g} horas ({extras:g} h extras)")
        lineas.append(f"  TOTAL aprobado:   {aprobadas:g} horas ({max(0.0, extras - aprobadas):g} h extra por aprobar)")

        return "\n".join(lineas)

    def generar_archivo(self, datos, usuario=None):
        """Construye un PDF válido con una página de texto."""
        texto = self.generar_reporte(datos, usuario=usuario)
        lineas = texto.splitlines() or [""]
        contenido = ["BT", "/F1 10 Tf", "50 780 Td", "14 TL"]
        for linea in lineas:
            seguro = (linea.replace("\\", "\\\\")
                      .replace("(", "\\(").replace(")", "\\)"))
            contenido.append(f"({seguro.encode('latin-1', 'replace').decode('latin-1')}) Tj")
            contenido.append("0 -14 Td")
        contenido.append("ET")
        flujo = "\n".join(contenido).encode("latin-1")

        objetos = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(flujo)).encode() + b" >>\nstream\n"
            + flujo + b"\nendstream",
        ]
        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for numero, objeto in enumerate(objetos, 1):
            offsets.append(len(pdf))
            pdf.extend(f"{numero} 0 obj\n".encode())
            pdf.extend(objeto)
            pdf.extend(b"\nendobj\n")
        inicio_xref = len(pdf)
        pdf.extend(f"xref\n0 {len(objetos) + 1}\n".encode())
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode())
        pdf.extend(
            f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
            f"startxref\n{inicio_xref}\n%%EOF\n".encode())
        return bytes(pdf)
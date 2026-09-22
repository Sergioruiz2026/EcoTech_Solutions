"""
Clase Empleado: representa la ficha laboral de un trabajador de EcoTech.
Requerimientos que resuelve: R1 (identificador unico) y R5 (proteccion salarial).
"""

from datetime import date

from seguridad import validaciones as v


class Empleado:

    def __init__(self, nombre, correo, salario, direccion="", telefono="",
                 fecha_contrato=None, id_empleado=None):

        # Toda entrada pasa por el modulo de validacion antes de existir
        self.id = id_empleado
        self.nombre = v.validar_nombre(nombre, "El nombre del empleado")
        self.correo = v.validar_correo(correo, "El correo")
        self.direccion = v.validar_descripcion(direccion, "La direccion")
        self.telefono = v.validar_telefono(telefono, "El telefono")
        self.fecha_contrato = v.validar_fecha(
            fecha_contrato or date.today(), "La fecha de contrato")

        self.__salario = v.validar_decimal(salario, "El salario", minimo=0)

        self.departamento = None
        self.proyectos = []
        self.registros_tiempo = []

    # ---------- Acceso controlado al salario (R5) ----------

    def obtener_salario(self):
        return self.__salario

    def actualizar_salario(self, nuevo_salario):
        self.__salario = v.validar_decimal(nuevo_salario, "El salario", minimo=0)

    # ---------- Registros de tiempo ----------

    def registrar_horas(self, registro):
        self.registros_tiempo.append(registro)

    def total_horas(self):
        return sum(registro.horas for registro in self.registros_tiempo)

    # ---------- Representacion ----------

    def __str__(self):
        return f"[{type(self).__name__}] {self.nombre} <{self.correo}>"
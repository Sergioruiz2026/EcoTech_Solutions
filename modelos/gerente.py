"""
Clase Gerente: especializacion de Empleado.
Requerimiento que resuelve: R7 (aprobacion de jornadas).
"""

from modelos.empleado import Empleado
from modelos.registro_tiempo import RegistroTiempo
from seguridad import validaciones as v


class Gerente(Empleado):

    # Unica fuente de verdad: la jornada normal definida en RegistroTiempo
    HORAS_MAXIMAS_APROBABLES = RegistroTiempo.HORAS_JORNADA_NORMAL

    def __init__(self, nombre, correo, salario, area, direccion="", telefono="",
                 fecha_contrato=None, id_empleado=None):

        super().__init__(nombre, correo, salario, direccion, telefono,
                         fecha_contrato, id_empleado)

        self.area = v.validar_titulo(area, "El area del gerente")

    # ---------- Regla de negocio (R7) ----------

    def aprobar_horas(self, registro):
        """Aprueba solo la jornada normal y deja el excedente como extra pendiente.

        Las primeras 12 horas se aprueban como jornada normal; el resto queda
        registrado como horas extras pendientes de aprobacion.
        """
        registro.horas_aprobadas = min(registro.horas, self.HORAS_MAXIMAS_APROBABLES)
        registro.aprobado = registro.horas_aprobadas >= registro.horas
        return registro.aprobado

    # ---------- Representacion ----------

    def __str__(self):
        return f"{super().__str__()} - Area: {self.area}"
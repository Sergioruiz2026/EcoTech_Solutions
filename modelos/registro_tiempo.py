"""
Clase RegistroTiempo: una jornada trabajada por un empleado en un proyecto.
Requerimiento que resuelve: R4 (registro y validacion de horas).
"""

from datetime import date

from seguridad import validaciones as v


class RegistroTiempo:

    HORAS_JORNADA_NORMAL = 12
    HORAS_MINIMAS = 0
    HORAS_MAXIMAS = 24

    def __init__(self, fecha, horas, descripcion, empleado, proyecto,
                 id_registro=None):

        self.id = id_registro
        self.fecha = v.validar_fecha(fecha or date.today(), "La fecha del registro")
        self.horas = horas
        self.descripcion = v.validar_descripcion(descripcion)
        self.empleado = empleado
        self.proyecto = proyecto
        self.aprobado = False
        self.horas_aprobadas = 0.0

        self.validar_horas()

        empleado.registrar_horas(self)
        proyecto.registros_tiempo.append(self)

    # ---------- Validacion (R4) ----------

    def validar_horas(self):
        """Delega en el modulo de validacion y deja el valor ya convertido."""
        self.horas = v.validar_decimal(
            self.horas, "Las horas trabajadas",
            minimo=self.HORAS_MINIMAS + 0.01, maximo=self.HORAS_MAXIMAS)
        return True

    @property
    def horas_normales(self):
        return min(self.horas, self.HORAS_JORNADA_NORMAL)

    @property
    def horas_extras(self):
        return max(0, self.horas - self.HORAS_JORNADA_NORMAL)

    @property
    def horas_extras_por_aprobar(self):
        """Mismo valor que horas_extras, con el nombre que usan los informes."""
        return self.horas_extras

    # ---------- Estado de aprobacion (R7) ----------

    @property
    def horas_pendientes(self):
        return round(self.horas - self.horas_aprobadas, 2)

    @property
    def estado(self):
        if self.horas_aprobadas >= self.horas:
            return "aprobado"
        if self.horas_aprobadas > 0:
            return "parcial"
        return "pendiente"

    # ---------- Representacion ----------

    def __str__(self):
        if self.estado == "parcial":
            detalle = (
                f"parcial: {self.horas_aprobadas:g} h aprobadas, "
                f"{self.horas_pendientes:g} h pendientes "
                f"({self.horas_extras_por_aprobar:g} h extras por aprobar)"
            )
        else:
            detalle = self.estado
        return (f"{self.fecha} | {self.horas} h | {self.empleado.nombre} "
                f"en {self.proyecto.nombre} | {self.descripcion} [{detalle}]")
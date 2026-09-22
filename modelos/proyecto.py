"""
Clase Proyecto: iniciativa de EcoTech con un equipo asignado.
Requerimiento que resuelve: R3 (asignacion y desasignacion de empleados).
"""

from datetime import date

from seguridad import validaciones as v


class Proyecto:

    def __init__(self, nombre, descripcion="", fecha_inicio=None, id_proyecto=None):

        self.id = id_proyecto
        self.nombre = v.validar_titulo(nombre, "El nombre del proyecto")
        self.descripcion = v.validar_descripcion(descripcion)
        self.fecha_inicio = v.validar_fecha(
            fecha_inicio or date.today(), "La fecha de inicio")

        self.equipo = []
        self.registros_tiempo = []

    # ---------- Gestion del equipo (R3) ----------

    def asignar_empleado(self, empleado):
        if empleado in self.equipo:
            return False

        self.equipo.append(empleado)
        empleado.proyectos.append(self)
        return True

    def desasignar_empleado(self, empleado):
        if empleado not in self.equipo:
            return False

        self.equipo.remove(empleado)
        empleado.proyectos.remove(self)
        return True

    # ---------- Edicion ----------

    def editar_proyecto(self, nombre=None, descripcion=None, fecha_inicio=None):
        if nombre is not None:
            self.nombre = v.validar_titulo(nombre, "El nombre del proyecto")

        if descripcion is not None:
            self.descripcion = v.validar_descripcion(descripcion)

        if fecha_inicio is not None:
            self.fecha_inicio = v.validar_fecha(fecha_inicio, "La fecha de inicio")

    def total_horas(self):
        return sum(registro.horas for registro in self.registros_tiempo)

    # ---------- Representacion ----------

    def __str__(self):
        return f"Proyecto {self.nombre} ({len(self.equipo)} en el equipo)"
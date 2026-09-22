"""
Clase Departamento: unidad organizativa de EcoTech.
Requerimiento que resuelve: R2 (pertenencia unica con reasignacion).
"""

from modelos.gerente import Gerente
from seguridad import validaciones as v


class Departamento:

    def __init__(self, nombre, id_departamento=None):

        self.id = id_departamento
        self.nombre = v.validar_titulo(nombre, "El nombre del departamento")
        self.empleados = []

    # ---------- Gestion del personal (R2) ----------

    def asignar_empleado(self, empleado):
        if empleado in self.empleados:
            return False

        if empleado.departamento is not None:
            empleado.departamento.quitar_empleado(empleado)

        self.empleados.append(empleado)
        empleado.departamento = self
        return True

    def quitar_empleado(self, empleado):
        if empleado not in self.empleados:
            return False

        self.empleados.remove(empleado)
        empleado.departamento = None
        return True

    def reasignar_empleado(self, empleado, nuevo_departamento):
        return nuevo_departamento.asignar_empleado(empleado)

    # ---------- Jefatura derivada, sin segunda relacion ----------

    def obtener_gerente(self):
        for empleado in self.empleados:
            if isinstance(empleado, Gerente):
                return empleado
        return None

    # ---------- Representacion ----------

    def __str__(self):
        return f"Departamento {self.nombre} ({len(self.empleados)} empleados)"
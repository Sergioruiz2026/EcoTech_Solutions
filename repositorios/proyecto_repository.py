"""
RepositorioProyecto: persistencia de Proyecto y de la relacion muchos a muchos
con Empleado, resuelta mediante la tabla intermedia empleados_proyectos.
"""

from datetime import date

from modelos.proyecto import Proyecto
from repositorios.repositorio_base import RepositorioBase


class RepositorioProyecto(RepositorioBase):

    SELECT_BASE = "SELECT id, nombre, descripcion, fecha_inicio FROM proyectos"

    # ---------- CRUD del proyecto ----------

    def crear(self, proyecto):
        cursor = self._escribir(
            "INSERT INTO proyectos (nombre, descripcion, fecha_inicio) "
            "VALUES (?, ?, ?)",
            (proyecto.nombre, proyecto.descripcion, str(proyecto.fecha_inicio)),
            error="No se pudo crear el proyecto.",
            error_integridad=f"Ya existe un proyecto llamado '{proyecto.nombre}'.")

        proyecto.id = cursor.lastrowid
        return proyecto

    def listar(self):
        filas = self._leer_todos(f"{self.SELECT_BASE} ORDER BY id")
        return [self.__fila_a_proyecto(fila) for fila in filas]

    def buscar_por_id(self, id_proyecto):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE id = ?", (id_proyecto,))
        return self.__fila_a_proyecto(fila) if fila else None

    def buscar_por_nombre(self, nombre):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE nombre = ?", (nombre,))
        return self.__fila_a_proyecto(fila) if fila else None

    def actualizar(self, proyecto):
        cursor = self._escribir(
            "UPDATE proyectos SET nombre = ?, descripcion = ?, fecha_inicio = ? "
            "WHERE id = ?",
            (proyecto.nombre, proyecto.descripcion,
             str(proyecto.fecha_inicio), proyecto.id),
            error="No se pudo actualizar el proyecto.",
            error_integridad="Ya existe otro proyecto con ese nombre.")

        return cursor.rowcount > 0

    def eliminar(self, id_proyecto):
        cursor = self._escribir(
            "DELETE FROM proyectos WHERE id = ?",
            (id_proyecto,),
            error="No se pudo eliminar el proyecto.",
            error_integridad="No se puede eliminar el proyecto.")

        return cursor.rowcount > 0

    # ---------- Relacion muchos a muchos ----------

    def asignar_empleado(self, id_proyecto, id_empleado):
        cursor = self._escribir(
            "INSERT OR IGNORE INTO empleados_proyectos (id_empleado, id_proyecto) "
            "VALUES (?, ?)",
            (id_empleado, id_proyecto),
            error="No se pudo asignar el empleado al proyecto.",
            error_integridad="El empleado o el proyecto indicado no existe.")

        return cursor.rowcount > 0

    def desasignar_empleado(self, id_proyecto, id_empleado):
        cursor = self._escribir(
            "DELETE FROM empleados_proyectos "
            "WHERE id_empleado = ? AND id_proyecto = ?",
            (id_empleado, id_proyecto),
            error="No se pudo desasignar el empleado del proyecto.")

        return cursor.rowcount > 0

    def listar_por_empleado(self, id_empleado):
        filas = self._leer_todos(
            """SELECT p.id, p.nombre, p.descripcion, p.fecha_inicio
                 FROM proyectos p
                 JOIN empleados_proyectos ep ON ep.id_proyecto = p.id
                WHERE ep.id_empleado = ?
             ORDER BY p.nombre""",
            (id_empleado,))

        return [self.__fila_a_proyecto(fila) for fila in filas]

    # ---------- Fabrica ----------

    @staticmethod
    def __fila_a_proyecto(fila):
        return Proyecto(nombre=fila["nombre"],
                        descripcion=fila["descripcion"] or "",
                        fecha_inicio=date.fromisoformat(fila["fecha_inicio"]),
                        id_proyecto=fila["id"])
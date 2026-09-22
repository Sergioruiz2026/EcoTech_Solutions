"""
RepositorioDepartamento: persistencia de la clase Departamento.
"""

from modelos.departamento import Departamento
from repositorios.repositorio_base import RepositorioBase


class RepositorioDepartamento(RepositorioBase):

    SELECT_BASE = "SELECT id, nombre FROM departamentos"

    # ---------- Create ----------

    def crear(self, departamento):
        cursor = self._escribir(
            "INSERT INTO departamentos (nombre) VALUES (?)",
            (departamento.nombre,),
            error="No se pudo crear el departamento.",
            error_integridad=f"Ya existe un departamento llamado '{departamento.nombre}'.")

        departamento.id = cursor.lastrowid
        return departamento

    # ---------- Read ----------

    def listar(self):
        filas = self._leer_todos(f"{self.SELECT_BASE} ORDER BY nombre")
        return [self.__fila_a_departamento(fila) for fila in filas]

    def buscar_por_id(self, id_departamento):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE id = ?", (id_departamento,))
        return self.__fila_a_departamento(fila) if fila else None

    def buscar_por_nombre(self, nombre):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE nombre = ?", (nombre,))
        return self.__fila_a_departamento(fila) if fila else None

    # ---------- Update ----------

    def actualizar(self, departamento):
        cursor = self._escribir(
            "UPDATE departamentos SET nombre = ? WHERE id = ?",
            (departamento.nombre, departamento.id),
            error="No se pudo actualizar el departamento.",
            error_integridad="Ya existe otro departamento con ese nombre.")

        return cursor.rowcount > 0

    # ---------- Delete ----------

    def eliminar(self, id_departamento):
        cursor = self._escribir(
            "DELETE FROM departamentos WHERE id = ?",
            (id_departamento,),
            error="No se pudo eliminar el departamento.",
            error_integridad="No se puede eliminar: hay empleados asignados a el.")

        return cursor.rowcount > 0

    # ---------- Fabrica ----------

    @staticmethod
    def __fila_a_departamento(fila):
        return Departamento(nombre=fila["nombre"], id_departamento=fila["id"])
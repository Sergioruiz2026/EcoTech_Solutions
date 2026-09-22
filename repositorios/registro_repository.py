"""
RepositorioRegistroTiempo: persistencia de las jornadas trabajadas.
Necesita los repositorios de empleados y proyectos para reconstruir
los objetos que cada registro referencia.
"""

from datetime import date

from modelos.registro_tiempo import RegistroTiempo
from repositorios.repositorio_base import RepositorioBase


class RepositorioRegistroTiempo(RepositorioBase):

    SELECT_BASE = """
        SELECT r.id, r.fecha, r.horas, r.descripcion, r.aprobado,
               r.horas_aprobadas, r.id_empleado, r.id_proyecto
        FROM registros_tiempo r
    """

    def __init__(self, base_datos, repo_empleados, repo_proyectos):
        super().__init__(base_datos)
        self.repo_empleados = repo_empleados
        self.repo_proyectos = repo_proyectos

    # ---------- Create ----------

    def crear(self, registro):
        cursor = self._escribir(
            """INSERT INTO registros_tiempo
                   (fecha, horas, descripcion, aprobado, horas_aprobadas,
                    id_empleado, id_proyecto)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(registro.fecha),
             registro.horas,
             registro.descripcion,
             1 if registro.aprobado else 0,
             registro.horas_aprobadas,
             registro.empleado.id,
             registro.proyecto.id),
            error="No se pudo guardar el registro de tiempo.",
            error_integridad="El empleado o el proyecto indicado no existe.")

        registro.id = cursor.lastrowid
        return registro

    # ---------- Read ----------

    def listar(self):
        filas = self._leer_todos(f"{self.SELECT_BASE} ORDER BY r.fecha, r.id")
        return self.__filas_a_registros(filas)

    def buscar_por_id(self, id_registro):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE r.id = ?", (id_registro,))
        return self.__filas_a_registros([fila])[0] if fila else None

    def listar_por_empleado(self, id_empleado):
        filas = self._leer_todos(
            f"{self.SELECT_BASE} WHERE r.id_empleado = ? ORDER BY r.fecha",
            (id_empleado,))
        return self.__filas_a_registros(filas)

    def listar_por_proyecto(self, id_proyecto):
        filas = self._leer_todos(
            f"{self.SELECT_BASE} WHERE r.id_proyecto = ? ORDER BY r.fecha",
            (id_proyecto,))
        return self.__filas_a_registros(filas)

    def listar_pendientes(self):
        filas = self._leer_todos(
            f"{self.SELECT_BASE} WHERE r.aprobado = 0 ORDER BY r.fecha")
        return self.__filas_a_registros(filas)

    # ---------- Update ----------

    def actualizar(self, registro):
        cursor = self._escribir(
            """UPDATE registros_tiempo
                  SET fecha = ?, horas = ?, descripcion = ?, aprobado = ?,
                      horas_aprobadas = ?, id_empleado = ?, id_proyecto = ?
                WHERE id = ?""",
            (str(registro.fecha),
             registro.horas,
             registro.descripcion,
             1 if registro.aprobado else 0,
             registro.horas_aprobadas,
             registro.empleado.id,
             registro.proyecto.id,
             registro.id),
            error="No se pudo actualizar el registro.",
            error_integridad="Los datos del registro no cumplen las restricciones de la base.")

        return cursor.rowcount > 0

    def marcar_aprobado(self, id_registro):
        cursor = self._escribir(
            "UPDATE registros_tiempo SET aprobado = 1, horas_aprobadas = horas "
            "WHERE id = ?",
            (id_registro,),
            error="No se pudo aprobar el registro.")

        return cursor.rowcount > 0

    # ---------- Delete ----------

    def eliminar(self, id_registro):
        cursor = self._escribir(
            "DELETE FROM registros_tiempo WHERE id = ?",
            (id_registro,),
            error="No se pudo eliminar el registro.")

        return cursor.rowcount > 0

    # ---------- Fabricas ----------

    def __filas_a_registros(self, filas):
        empleados = {}
        proyectos = {}
        registros = []

        for fila in filas:
            id_empleado = fila["id_empleado"]
            id_proyecto = fila["id_proyecto"]

            if id_empleado not in empleados:
                empleados[id_empleado] = self.repo_empleados.buscar_por_id(id_empleado)
            if id_proyecto not in proyectos:
                proyectos[id_proyecto] = self.repo_proyectos.buscar_por_id(id_proyecto)

            registros.append(self.__fila_a_registro(
                fila, empleados[id_empleado], proyectos[id_proyecto]))

        return registros

    @staticmethod
    def __fila_a_registro(fila, empleado, proyecto):
        registro = RegistroTiempo(
            fecha=date.fromisoformat(fila["fecha"]),
            horas=fila["horas"],
            descripcion=fila["descripcion"] or "",
            empleado=empleado,
            proyecto=proyecto,
            id_registro=fila["id"])

        registro.aprobado = bool(fila["aprobado"])
        registro.horas_aprobadas = fila["horas_aprobadas"] or 0.0
        return registro
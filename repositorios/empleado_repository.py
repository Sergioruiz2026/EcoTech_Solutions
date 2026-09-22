"""
RepositorioEmpleado: persistencia de Empleado y Gerente.
Estrategia: herencia de tabla unica, con la columna 'tipo' como discriminador.
"""

from datetime import date

from modelos.empleado import Empleado
from modelos.gerente import Gerente
from modelos.departamento import Departamento
from repositorios.repositorio_base import RepositorioBase


class RepositorioEmpleado(RepositorioBase):

    SELECT_BASE = """
        SELECT e.id, e.nombre, e.correo, e.direccion, e.telefono,
               e.fecha_contrato, e.salario, e.tipo, e.area,
               e.id_departamento, d.nombre AS nombre_departamento
        FROM empleados e
        LEFT JOIN departamentos d ON d.id = e.id_departamento
    """

    # ---------- Create ----------

    def crear(self, empleado):
        es_gerente = isinstance(empleado, Gerente)

        cursor = self._escribir(
            """INSERT INTO empleados
                   (nombre, correo, direccion, telefono, fecha_contrato,
                    salario, tipo, area, id_departamento)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (empleado.nombre,
             empleado.correo,
             empleado.direccion,
             empleado.telefono,
             str(empleado.fecha_contrato),
             empleado.obtener_salario(),
             "gerente" if es_gerente else "empleado",
             empleado.area if es_gerente else None,
             empleado.departamento.id if empleado.departamento else None),
            error="No se pudo crear el empleado.",
            error_integridad=f"Ya existe un empleado con el correo '{empleado.correo}'.")

        empleado.id = cursor.lastrowid
        return empleado

    # ---------- Read ----------

    def listar(self):
        filas = self._leer_todos(f"{self.SELECT_BASE} ORDER BY e.nombre")
        return [self.__fila_a_empleado(fila) for fila in filas]

    def buscar_por_id(self, id_empleado):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE e.id = ?", (id_empleado,))
        return self.__fila_a_empleado(fila) if fila else None

    def buscar_por_correo(self, correo):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE e.correo = ?", (correo,))
        return self.__fila_a_empleado(fila) if fila else None

    def listar_por_departamento(self, id_departamento):
        filas = self._leer_todos(
            f"{self.SELECT_BASE} WHERE e.id_departamento = ? ORDER BY e.nombre",
            (id_departamento,))
        return [self.__fila_a_empleado(fila) for fila in filas]
    def listar_por_proyecto(self, id_proyecto):
        filas = self._leer_todos(
            f"""{self.SELECT_BASE}
                JOIN empleados_proyectos ep ON ep.id_empleado = e.id
                WHERE ep.id_proyecto = ?
             ORDER BY e.nombre""",
            (id_proyecto,))

        return [self.__fila_a_empleado(fila) for fila in filas]

    # ---------- Update ----------

    def actualizar(self, empleado):
        es_gerente = isinstance(empleado, Gerente)

        cursor = self._escribir(
            """UPDATE empleados
                  SET nombre = ?, correo = ?, direccion = ?, telefono = ?,
                      salario = ?, tipo = ?, area = ?, id_departamento = ?
                WHERE id = ?""",
            (empleado.nombre,
             empleado.correo,
             empleado.direccion,
             empleado.telefono,
             empleado.obtener_salario(),
             "gerente" if es_gerente else "empleado",
             empleado.area if es_gerente else None,
             empleado.departamento.id if empleado.departamento else None,
             empleado.id),
            error="No se pudo actualizar el empleado.",
            error_integridad="Ya existe otro empleado con ese correo.")

        return cursor.rowcount > 0

    # ---------- Delete ----------

    def eliminar(self, id_empleado):
        cursor = self._escribir(
            "DELETE FROM empleados WHERE id = ?",
            (id_empleado,),
            error="No se pudo eliminar el empleado.",
            error_integridad="No se puede eliminar: el empleado tiene datos asociados.")

        return cursor.rowcount > 0

    # ---------- Fabrica: decide que clase reconstruir ----------

    @staticmethod
    def __fila_a_empleado(fila):
        comunes = {
            "nombre": fila["nombre"],
            "correo": fila["correo"],
            "salario": fila["salario"],
            "direccion": fila["direccion"] or "",
            "telefono": fila["telefono"] or "",
            "fecha_contrato": date.fromisoformat(fila["fecha_contrato"]),
            "id_empleado": fila["id"],
        }

        if fila["tipo"] == "gerente":
            empleado = Gerente(area=fila["area"] or "sin area", **comunes)
        else:
            empleado = Empleado(**comunes)

        if fila["id_departamento"] is not None:
            empleado.departamento = Departamento(
                nombre=fila["nombre_departamento"],
                id_departamento=fila["id_departamento"])

        return empleado
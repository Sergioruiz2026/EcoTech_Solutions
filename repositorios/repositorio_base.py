"""
RepositorioBase: comportamiento comun a todos los repositorios.
Centraliza la conexion, el manejo de errores y las transacciones.

El detalle tecnico de cada fallo se guarda en el archivo de registro;
al usuario solo se le devuelve el mensaje del dominio. Asi los nombres
de tablas y columnas no llegan nunca a la pantalla.
"""

import sqlite3

from seguridad.auditoria import registrar_fallo
from seguridad.validaciones import ErrorDominio


class RepositorioBase:

    def __init__(self, base_datos):
        self.base_datos = base_datos
        self.conexion = base_datos.conectar()

    # ---------- Lectura ----------

    def _leer_todos(self, sql, parametros=(),
                    error="Error al consultar la base de datos."):
        try:
            cursor = self.conexion.cursor()
            cursor.execute(sql, parametros)
            return cursor.fetchall()
        except sqlite3.Error as fallo:
            registrar_fallo(f"Consulta fallida: {sql.strip()[:80]}", fallo)
            raise RuntimeError(error)

    def _leer_uno(self, sql, parametros=(),
                  error="Error al consultar la base de datos."):
        filas = self._leer_todos(sql, parametros, error)
        return filas[0] if filas else None

    # ---------- Escritura ----------

    def _escribir(self, sql, parametros=(),
                  error="Error al escribir en la base de datos.",
                  error_integridad="La operacion viola una restriccion de la base."):
        try:
            cursor = self.conexion.cursor()
            cursor.execute(sql, parametros)
            self.conexion.commit()
            return cursor

        except sqlite3.IntegrityError as fallo:
            self.conexion.rollback()
            registrar_fallo(f"Restriccion violada: {sql.strip()[:80]}", fallo)
            raise ErrorDominio(error_integridad)

        except sqlite3.Error as fallo:
            self.conexion.rollback()
            registrar_fallo(f"Escritura fallida: {sql.strip()[:80]}", fallo)
            raise RuntimeError(error)
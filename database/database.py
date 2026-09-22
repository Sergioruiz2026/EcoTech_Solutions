"""
Capa de acceso a SQLite: conexion, esquema y cierre.
Las clases de dominio no contienen SQL; todo el acceso pasa por aqui.
"""

import sqlite3
from pathlib import Path

RUTA_POR_DEFECTO = Path(__file__).resolve().parent.parent / "ecotech.db"


# Nota de diseno: las columnas que identifican a una entidad por su nombre
# usan COLLATE NOCASE. Sin eso, SQLite compara distinguiendo mayusculas y
# "Operaciones" y "operaciones" conviven como dos departamentos distintos,
# que para cualquier persona son el mismo.
ESQUEMA = """
CREATE TABLE IF NOT EXISTS departamentos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS empleados (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    correo          TEXT NOT NULL UNIQUE COLLATE NOCASE,
    direccion       TEXT,
    telefono        TEXT,
    fecha_contrato  TEXT NOT NULL,
    salario         REAL NOT NULL CHECK (salario >= 0),
    tipo            TEXT NOT NULL DEFAULT 'empleado',
    area            TEXT,
    id_departamento INTEGER,
    FOREIGN KEY (id_departamento) REFERENCES departamentos(id)
);

CREATE TABLE IF NOT EXISTS proyectos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    descripcion   TEXT,
    fecha_inicio  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registros_tiempo (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha        TEXT NOT NULL,
    horas        REAL NOT NULL CHECK (horas > 0 AND horas <= 24),
    descripcion  TEXT,
    aprobado     INTEGER NOT NULL DEFAULT 0,
    horas_aprobadas REAL NOT NULL DEFAULT 0 CHECK (horas_aprobadas >= 0),
    id_empleado  INTEGER NOT NULL,
    id_proyecto  INTEGER NOT NULL,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id) ON DELETE CASCADE,
    FOREIGN KEY (id_proyecto) REFERENCES proyectos(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario   TEXT NOT NULL UNIQUE COLLATE NOCASE,
    contrasena_hash  TEXT NOT NULL,
    rol              TEXT NOT NULL,
    id_empleado      INTEGER UNIQUE,
    debe_cambiar_clave INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS empleados_proyectos (
    id_empleado  INTEGER NOT NULL,
    id_proyecto  INTEGER NOT NULL,
    PRIMARY KEY (id_empleado, id_proyecto),
    FOREIGN KEY (id_empleado) REFERENCES empleados(id) ON DELETE CASCADE,
    FOREIGN KEY (id_proyecto) REFERENCES proyectos(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS consultas_api (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario   TEXT NOT NULL,
    tipo_consulta    TEXT NOT NULL,
    parametros_json  TEXT NOT NULL,
    respuesta_json   TEXT NOT NULL,
    fecha_consulta   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class BaseDatos:

    def __init__(self, ruta=None):
        self.ruta = str(ruta or RUTA_POR_DEFECTO)
        self.conexion = None

    def conectar(self):
        if self.conexion is None:
            self.conexion = sqlite3.connect(self.ruta)
            self.conexion.execute("PRAGMA foreign_keys = ON")
            self.conexion.row_factory = sqlite3.Row
        return self.conexion

    def crear_tablas(self):
        conexion = self.conectar()
        conexion.executescript(ESQUEMA)
        columnas = {
            fila[1] for fila in conexion.execute("PRAGMA table_info(usuarios)")
        }
        if "debe_cambiar_clave" not in columnas:
            conexion.execute(
                "ALTER TABLE usuarios ADD COLUMN debe_cambiar_clave "
                "INTEGER NOT NULL DEFAULT 0")
        conexion.commit()

    def cerrar(self):
        if self.conexion is not None:
            self.conexion.close()
            self.conexion = None
import unittest
from datetime import date
from tempfile import TemporaryDirectory
from pathlib import Path

from database.database import BaseDatos
from modelos.proyecto import Proyecto
from repositorios.proyecto_repository import RepositorioProyecto


class TestRepositorioProyecto(unittest.TestCase):
    def test_listar_ordena_proyectos_por_id(self):
        with TemporaryDirectory() as carpeta:
            base_datos = BaseDatos(Path(carpeta) / "prueba.db")
            base_datos.crear_tablas()
            repositorio = RepositorioProyecto(base_datos)

            repositorio.crear(Proyecto("Zeta", fecha_inicio=date(2026, 1, 1)))
            repositorio.crear(Proyecto("Alfa", fecha_inicio=date(2026, 1, 2)))

            self.assertEqual([proyecto.id for proyecto in repositorio.listar()], [1, 2])

            base_datos.cerrar()


if __name__ == "__main__":
    unittest.main()
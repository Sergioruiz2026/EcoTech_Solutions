"""
Clase Informe: contrato comun para la generacion de reportes.
Requerimiento que resuelve: R8 (informes en distintos formatos por polimorfismo).
"""

from abc import ABC, abstractmethod
from datetime import date


class Informe(ABC):

    EXTENSION = None
    TIPO = "generico"

    def __init__(self, titulo, id_informe=None):

        if not titulo or not titulo.strip():
            raise ValueError("El informe debe tener un titulo.")

        self.id = id_informe
        self.titulo = titulo.strip()
        self.tipo = self.TIPO
        self.fecha_emision = date.today()

    # ---------- Comportamiento comun a todos los formatos ----------

    def encabezado(self):
        return (f"ECOTECH SOLUTIONS\n"
                f"{self.titulo}\n"
                f"Emitido: {self.fecha_emision} | Formato: {self.tipo}")

    def nombre_archivo(self):
        base = self.titulo.lower().replace(" ", "_")
        return f"{base}.{self.EXTENSION}"

    # ---------- Lo que cada subclase esta obligada a implementar ----------

    @abstractmethod
    def generar_reporte(self, datos):
        ...

    def generar_archivo(self, datos):
        """Devuelve el contenido listo para guardar en el formato indicado."""
        return self.generar_reporte(datos).encode("utf-8")

    def __str__(self):
        return f"Informe {self.tipo} - {self.titulo}"
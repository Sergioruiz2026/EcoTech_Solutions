"""
Registro de eventos y errores del sistema.

Separa lo que ve el usuario de lo que necesita el desarrollador:
el usuario recibe un mensaje del dominio, sin rutas ni nombres de tablas,
y el detalle tecnico queda guardado en el archivo de registro.
"""

import logging
import os
from pathlib import Path
from datetime import datetime

RUTA_REGISTRO = Path(__file__).resolve().parent.parent / "ecotech.log"
RUTA_USO_IA = Path(__file__).resolve().parent.parent / "USO_DE_IA.md"

logging.basicConfig(
    filename=str(RUTA_REGISTRO),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

_registro = logging.getLogger("ecotech")


def registrar_evento(mensaje):
    """Deja constancia de una accion relevante para la auditoria."""
    _registro.info(mensaje)


def registrar_prompt(prompt, herramienta="No especificada", decision="Pendiente"):
    """Agrega un prompt al registro documental de uso de IA."""
    texto = " ".join(str(prompt).split()).replace("|", "\\|")
    herramienta = " ".join(str(herramienta).split()).replace("|", "\\|")
    decision = " ".join(str(decision).split()).replace("|", "\\|")
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with RUTA_USO_IA.open("a", encoding="utf-8") as archivo:
        archivo.write(f"| {fecha} | {herramienta} | {texto} | {decision} |\n")
        archivo.flush()
        os.fsync(archivo.fileno())


def registrar_acceso(usuario, exitoso):
    """Registra cada intento de autenticacion, exitoso o no."""
    estado = "ACCESO CONCEDIDO" if exitoso else "ACCESO DENEGADO"
    nombre_auditable = (usuario.nombre_usuario
                        if usuario is not None else "usuario desconocido")
    _registro.info("%s | usuario=%s", estado, nombre_auditable)


def registrar_bloqueo(usuario, segundos):
    """Registra un bloqueo temporal sin guardar nombres desconocidos."""
    nombre_auditable = (usuario.nombre_usuario
                        if usuario is not None else "usuario desconocido")
    _registro.warning(
        "BLOQUEO TEMPORAL | usuario=%s | duracion=%s segundos",
        nombre_auditable, segundos)


def registrar_fallo(contexto, error):
    """Guarda el detalle tecnico de un error sin mostrarlo al usuario."""
    _registro.error("%s | %s: %s", contexto, type(error).__name__, error)


def mensaje_seguro(error, respaldo="Ocurrio un problema al procesar la solicitud."):
    """Devuelve un texto apto para mostrar en pantalla.

    Los errores del dominio ya traen un mensaje pensado para el usuario.
    Cualquier otro se reemplaza por un texto generico, para no exponer
    rutas de archivos, nombres de tablas ni trazas internas.
    """
    from seguridad.validaciones import ErrorDominio, ErrorValidacion

    if isinstance(error, ErrorValidacion):
        return error.mensaje

    if isinstance(error, ErrorDominio):
        return str(error)

    return respaldo

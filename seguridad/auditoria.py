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


def _sanear_markdown(texto):
    """Normaliza el texto para evitar romper tablas Markdown."""
    if texto is None:
        return ""
    texto = str(texto).replace("\\r\\n", "\\n").replace("\\r", "\\n")
    texto = texto.replace("|", "\\|")
    texto = " ".join(texto.replace("\\n", " ").split())
    return texto


def registrar_prompt(prompt, herramienta="No especificada", respuesta="Pendiente",
                    *, fase="No especificada", ruta_archivo=None, decision=None):
    """Agrega un prompt al registro documental de uso de IA."""
    if decision is not None:
        respuesta = decision

    fase = _sanear_markdown(fase)
    herramienta = _sanear_markdown(herramienta)
    texto = _sanear_markdown(prompt)
    respuesta = _sanear_markdown(respuesta)

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    archivo_destino = Path(ruta_archivo) if ruta_archivo is not None else RUTA_USO_IA
    archivo_destino.parent.mkdir(parents=True, exist_ok=True)

    with archivo_destino.open("a", encoding="utf-8") as archivo:
        archivo.write(
            f"| {fecha} | {fase} | {herramienta} | {texto} | {respuesta} |\n"
        )
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

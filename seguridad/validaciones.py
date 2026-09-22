"""
Modulo de validacion de entradas.

Centraliza la verificacion de tipo, rango, longitud y formato de todo dato
que ingresa al sistema, venga del teclado, de un archivo o de una API.

Cada funcion devuelve el valor ya limpio y convertido, o lanza ErrorValidacion.
"""

import re
from datetime import date, datetime


# ---------------- Limites ----------------

LARGO_MAXIMO_TEXTO = 300
LARGO_MINIMO_CLAVE = 8
LARGO_MAXIMO_CLAVE = 128


# ---------------- Patrones ----------------

PATRON_CORREO = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$")

PATRON_NOMBRE = re.compile(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]{1,79}$")

PATRON_USUARIO = re.compile(r"^[a-z][a-z0-9._-]{2,29}$")

PATRON_TELEFONO = re.compile(r"^\+?56\s?9\s?\d{4}\s?\d{4}$")

PATRON_TITULO = re.compile(
    r"^[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ][A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ'.,()\- ]{1,79}$")

PATRON_MONEDA = re.compile(r"^[A-Za-z]{3}$")


class ErrorDominio(ValueError):
    """Error cuyo mensaje fue redactado por nosotros y es seguro mostrar.

    Todo lo que hereda de esta clase puede llegar a la pantalla tal cual:
    no contiene rutas, nombres de tablas ni trazas internas.
    """


class ErrorValidacion(ErrorDominio):
    """Entrada que no cumple las reglas del sistema."""

    def __init__(self, campo, mensaje):
        self.campo = campo
        self.mensaje = mensaje
        super().__init__(f"{campo}: {mensaje}")


# ---------------- Texto ----------------

def validar_texto(valor, campo, minimo=1, maximo=LARGO_MAXIMO_TEXTO,
                  obligatorio=True):
    if valor is None:
        valor = ""

    if not isinstance(valor, str):
        raise ErrorValidacion(campo, "debe ser texto.")

    if any(ord(caracter) < 32 for caracter in valor):
        raise ErrorValidacion(campo, "contiene caracteres de control no permitidos.")

    limpio = valor.strip()

    if not limpio:
        if obligatorio:
            raise ErrorValidacion(campo, "no puede quedar vacio.")
        return ""

    if len(limpio) < minimo:
        raise ErrorValidacion(campo, f"debe tener al menos {minimo} caracteres.")

    if len(limpio) > maximo:
        raise ErrorValidacion(campo, f"no puede superar los {maximo} caracteres.")

    return limpio


def validar_nombre(valor, campo="nombre"):
    limpio = validar_texto(valor, campo, minimo=2, maximo=80)
    if not PATRON_NOMBRE.match(limpio):
        raise ErrorValidacion(
            campo, "solo admite letras, espacios, guiones y apostrofes, "
                   "y debe comenzar con una letra.")
    return limpio


def validar_titulo(valor, campo="nombre"):
    """Nombres de departamentos y proyectos: admiten numeros y puntuacion simple."""
    limpio = validar_texto(valor, campo, minimo=2, maximo=80)
    if not PATRON_TITULO.match(limpio):
        raise ErrorValidacion(
            campo, "solo admite letras, numeros, espacios y puntuacion simple, "
                   "y debe comenzar con una letra o un numero.")
    return limpio


def validar_descripcion(valor, campo="descripcion", obligatorio=False):
    return validar_texto(valor, campo, minimo=0, maximo=LARGO_MAXIMO_TEXTO,
                         obligatorio=obligatorio)


def validar_codigo_moneda(valor, campo="moneda"):
    limpio = validar_texto(valor, campo, minimo=3, maximo=3)
    if not PATRON_MONEDA.match(limpio):
        raise ErrorValidacion(
            campo, "debe ser un codigo de tres letras (por ejemplo USD o CLP).")
    return limpio.upper()


def validar_correo(valor, campo="correo"):
    limpio = validar_texto(valor, campo, minimo=5, maximo=120).lower()
    if not PATRON_CORREO.match(limpio):
        raise ErrorValidacion(
            campo, "no tiene un formato valido (ejemplo: nombre@empresa.cl).")
    return limpio


def validar_telefono(valor, campo="telefono", obligatorio=False):
    limpio = validar_texto(valor, campo, minimo=0, maximo=20,
                           obligatorio=obligatorio)
    if not limpio:
        return ""
    if not PATRON_TELEFONO.match(limpio):
        raise ErrorValidacion(
            campo, "debe ser un numero chileno valido (ejemplo: +56 9 1234 5678).")
    return limpio


def validar_usuario(valor, campo="nombre de usuario"):
    limpio = validar_texto(valor, campo, minimo=3, maximo=30).lower()
    if not PATRON_USUARIO.match(limpio):
        raise ErrorValidacion(
            campo, "debe comenzar con una letra y contener solo minusculas, "
                   "numeros, punto, guion o guion bajo (3 a 30 caracteres).")
    return limpio


def validar_contrasena(valor, campo="contrasena", minimo=LARGO_MINIMO_CLAVE):
    if not isinstance(valor, str):
        raise ErrorValidacion(campo, "debe ser texto.")

    if len(valor) < minimo:
        raise ErrorValidacion(
            campo, f"debe tener al menos {minimo} caracteres.")

    if len(valor) > LARGO_MAXIMO_CLAVE:
        raise ErrorValidacion(
            campo, f"no puede superar los {LARGO_MAXIMO_CLAVE} caracteres.")

    if not re.search(r"[A-Za-z]", valor):
        raise ErrorValidacion(campo, "debe contener al menos una letra.")

    if not re.search(r"\d", valor):
        raise ErrorValidacion(campo, "debe contener al menos un numero.")

    if valor.strip() != valor:
        raise ErrorValidacion(campo, "no puede comenzar ni terminar con espacios.")

    return valor


# ---------------- Numeros ----------------

def validar_entero(valor, campo, minimo=None, maximo=None):
    if isinstance(valor, bool):
        raise ErrorValidacion(campo, "debe ser un numero entero.")

    if isinstance(valor, str):
        texto = valor.strip()
        if not re.fullmatch(r"[+-]?\d+", texto):
            raise ErrorValidacion(campo, "debe ser un numero entero.")
        valor = int(texto)

    if not isinstance(valor, int):
        raise ErrorValidacion(campo, "debe ser un numero entero.")

    if minimo is not None and valor < minimo:
        raise ErrorValidacion(campo, f"no puede ser menor que {minimo}.")

    if maximo is not None and valor > maximo:
        raise ErrorValidacion(campo, f"no puede ser mayor que {maximo}.")

    return valor


def _normalizar_numero(texto):
    """Convierte la escritura chilena de numeros al formato que entiende float().

    Regla: si hay coma, la coma es el separador decimal y los puntos son de
    miles. Si solo hay puntos, se consideran separadores de miles unicamente
    cuando agrupan de a tres digitos; en cualquier otro caso el punto es
    decimal. Asi '1.650.000' vale un millon seiscientos cincuenta mil, pero
    '0.2' sigue valiendo dos decimas.
    """
    texto = texto.strip()

    if "," in texto:
        return texto.replace(".", "").replace(",", ".")

    if re.fullmatch(r"[+-]?\d{1,3}(\.\d{3})+", texto):
        return texto.replace(".", "")

    return texto


def validar_decimal(valor, campo, minimo=None, maximo=None):
    if isinstance(valor, bool):
        raise ErrorValidacion(campo, "debe ser un numero.")

    if isinstance(valor, str):
        texto = _normalizar_numero(valor)
        if not re.fullmatch(r"[+-]?\d+(\.\d+)?", texto):
            raise ErrorValidacion(campo, "debe ser un numero.")
        valor = float(texto)

    if not isinstance(valor, (int, float)):
        raise ErrorValidacion(campo, "debe ser un numero.")

    valor = float(valor)

    if minimo is not None and valor < minimo:
        raise ErrorValidacion(campo, f"no puede ser menor que {minimo}.")

    if maximo is not None and valor > maximo:
        raise ErrorValidacion(campo, f"no puede ser mayor que {maximo}.")

    return valor


def usuario_puede_ver_salarios(usuario):
    """Valida si el usuario autenticado puede ver salarios reales."""
    if usuario is None:
        return False

    rol = getattr(usuario, "rol", "").lower() if hasattr(usuario, "rol") else ""
    if rol in {"gerente", "administrador"}:
        return True

    if hasattr(usuario, "tiene_permiso"):
        return bool(usuario.tiene_permiso("ver_salarios"))

    return False


def formatear_salario_informe(salario, usuario=None):
    """Devuelve el salario real o un valor enmascarado según el rol."""
    if usuario_puede_ver_salarios(usuario):
        try:
            valor = float(salario)
            return f"$ {valor:,.0f}"
        except (TypeError, ValueError):
            return "$ *******"

    return "$ *******"


def formatear_correo_informe(correo, usuario=None):
    """Oculta parte del correo si el usuario no tiene permisos de salario."""
    if usuario_puede_ver_salarios(usuario):
        return correo or "[SIN CORREO]"

    if not correo:
        return "[CONFIDENCIAL]"

    local, dominio = correo.split("@", 1)
    if len(local) <= 2:
        return f"{local[0]}*@{dominio}"

    return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{dominio}"


# ---------------- Fechas y opciones ----------------

def validar_fecha(valor, campo="fecha", minima=None, maxima=None):
    if isinstance(valor, datetime):
        valor = valor.date()

    if isinstance(valor, str):
        texto = valor.strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
            raise ErrorValidacion(campo, "debe tener el formato AAAA-MM-DD.")
        try:
            valor = date.fromisoformat(texto)
        except ValueError:
            raise ErrorValidacion(
                campo, "no corresponde a una fecha real del calendario.")

    if not isinstance(valor, date):
        raise ErrorValidacion(campo, "debe ser una fecha.")

    if minima is not None and valor < minima:
        raise ErrorValidacion(campo, f"no puede ser anterior a {minima}.")

    if maxima is not None and valor > maxima:
        raise ErrorValidacion(campo, f"no puede ser posterior a {maxima}.")

    return valor


def validar_opcion(valor, campo, permitidos):
    limpio = validar_texto(valor, campo, minimo=1, maximo=50).lower()
    if limpio not in permitidos:
        raise ErrorValidacion(
            campo, f"debe ser uno de: {', '.join(sorted(permitidos))}.")
    return limpio

"""
Clase Usuario: cuenta de acceso al sistema.
Requerimiento que resuelve: R6 (separacion de autenticacion y autorizacion).
"""

import hashlib
import hmac
import secrets

from seguridad import validaciones as v


class Usuario:

    PERMISOS_POR_ROL = {
        "administrador": {"consultar_datos", "gestionar_datos", "ver_salarios",
                          "editar_empleados", "aprobar_horas",
                          "generar_informes", "consultar_externos",
                          "gestionar_usuarios"},
        "gerente": {"consultar_datos", "gestionar_datos", "ver_salarios",
                    "aprobar_horas", "generar_informes",
                    "consultar_externos", "gestionar_usuarios"},
        "operador": {"consultar_datos", "generar_informes", "consultar_externos"},
    }

    LARGO_MINIMO_CLAVE = 8
    ALGORITMO_HASH = "pbkdf2_sha256"
    ITERACIONES_HASH = 600000

    def __init__(self, nombre_usuario, contrasena, rol, empleado=None,
                 id_usuario=None, debe_cambiar_clave=False):

        self.id = id_usuario
        self.nombre_usuario = v.validar_usuario(nombre_usuario)
        self.rol = v.validar_opcion(rol, "El rol", set(self.PERMISOS_POR_ROL))
        self.empleado = empleado
        self.bloqueado_hasta = None
        self.debe_cambiar_clave = bool(debe_cambiar_clave)

        contrasena = v.validar_contrasena(contrasena, "La contrasena")
        self.__contrasena_hash = self.__generar_hash(contrasena)

    # ---------- Resumen de la contrasena ----------

    @staticmethod
    def __generar_hash(contrasena):
        sal = secrets.token_bytes(16)
        resumen = hashlib.pbkdf2_hmac(
            "sha256", contrasena.encode("utf-8"), sal,
            Usuario.ITERACIONES_HASH).hex()
        return (f"{Usuario.ALGORITMO_HASH}${Usuario.ITERACIONES_HASH}$"
                f"{sal.hex()}${resumen}")

    def obtener_hash(self):
        return self.__contrasena_hash

    @classmethod
    def desde_hash(cls, nombre_usuario, contrasena_hash, rol,
                   empleado=None, id_usuario=None, debe_cambiar_clave=False):
        """Reconstruye una cuenta que ya existe, sin recalcular el hash."""
        usuario = object.__new__(cls)
        usuario.id = id_usuario
        usuario.nombre_usuario = nombre_usuario
        usuario.rol = rol
        usuario.empleado = empleado
        usuario.bloqueado_hasta = None
        usuario.debe_cambiar_clave = bool(debe_cambiar_clave)
        usuario.__contrasena_hash = contrasena_hash
        return usuario

    # ---------- Autenticacion ----------

    def autenticar(self, contrasena):
        partes = self.__contrasena_hash.split("$")

        if len(partes) == 4 and partes[0] == self.ALGORITMO_HASH:
            try:
                iteraciones = int(partes[1])
                sal = bytes.fromhex(partes[2])
                resumen_guardado = bytes.fromhex(partes[3])
            except (TypeError, ValueError):
                return False

            candidato = hashlib.pbkdf2_hmac(
                "sha256", contrasena.encode("utf-8"), sal, iteraciones)
            return hmac.compare_digest(candidato, resumen_guardado)

        if len(partes) != 2:
            return False

        sal, resumen_guardado = partes
        candidato = hashlib.sha256((sal + contrasena).encode("utf-8")).hexdigest()
        if not hmac.compare_digest(candidato, resumen_guardado):
            return False

        self.__contrasena_hash = self.__generar_hash(contrasena)
        return True

    def cambiar_contrasena(self, contrasena_actual, contrasena_nueva):
        if not self.autenticar(contrasena_actual):
            return False

        self.establecer_contrasena(contrasena_nueva)
        return True

    def establecer_contrasena(self, contrasena, minimo=8):
        contrasena = v.validar_contrasena(
            contrasena, "La contrasena nueva", minimo=minimo)
        self.__contrasena_hash = self.__generar_hash(contrasena)

    # ---------- Autorizacion ----------

    def tiene_permiso(self, permiso):
        return permiso in self.PERMISOS_POR_ROL[self.rol]

    # ---------- Representacion ----------

    def __str__(self):
        vinculo = self.empleado.nombre if self.empleado else "sin empleado asociado"
        return f"Usuario {self.nombre_usuario} ({self.rol}) - {vinculo}"
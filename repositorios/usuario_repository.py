"""
RepositorioUsuario: persistencia de las cuentas de acceso.
La contrasena nunca viaja ni se almacena: solo su resumen.
"""

from seguridad.validaciones import ErrorDominio
from modelos.usuario import Usuario
from repositorios.repositorio_base import RepositorioBase


class RepositorioUsuario(RepositorioBase):

    SELECT_BASE = """
        SELECT id, nombre_usuario, contrasena_hash, rol, id_empleado,
               debe_cambiar_clave
        FROM usuarios
    """

    MENSAJE_SEGURIDAD_ADMIN = (
        "Error de Seguridad: Solo un Administrador puede crear, promover o "
        "modificar cuentas administrativas."
    )

    def __init__(self, base_datos, repo_empleados):
        super().__init__(base_datos)
        self.repo_empleados = repo_empleados

    @staticmethod
    def validar_operacion_administrativa(actor, usuario_destino=None, nuevo_rol=None,
                                        accion="operacion"):
        """Restringe la elevacion de privilegios a cuentas administrativas.

        Solo un usuario activo con rol Administrador puede:
        1) crear un rol Administrador,
        2) promover una cuenta a Administrador,
        3) modificar o eliminar otras cuentas administrativas.
        El resto de la gestion de usuarios y la administracion de claves temporales
        sigue permitida para gerentes y perfiles autorizados no administrativos.
        """
        actor_rol = getattr(actor, "rol", None)
        if actor_rol != "administrador":
            es_promocion_admin = nuevo_rol == "administrador"
            es_modificar_admin = (
                usuario_destino is not None and usuario_destino.rol == "administrador"
            )
            if es_promocion_admin or es_modificar_admin:
                raise ErrorDominio(
                    RepositorioUsuario.MENSAJE_SEGURIDAD_ADMIN
                )

        # En este punto el actor es administrador. Rechazar la operacion solo si se
        # intenta tocar otra cuenta administrativa desde una sesion no autorizada,
        # pero como la regla anterior ya bloqueo los perfiles no administradores,
        # esta validacion evita contraejemplos futuros y mantiene la semantica de
        # seguridad por defecto.
        if usuario_destino is not None and usuario_destino.rol == "administrador":
            if actor is None or getattr(actor, "rol", None) != "administrador":
                raise ErrorDominio(
                    RepositorioUsuario.MENSAJE_SEGURIDAD_ADMIN
                )

    # ---------- Create ----------

    def crear(self, usuario):
        cursor = self._escribir(
            "INSERT INTO usuarios (nombre_usuario, contrasena_hash, rol, "
            "id_empleado, debe_cambiar_clave) VALUES (?, ?, ?, ?, ?)",
            (usuario.nombre_usuario,
             usuario.obtener_hash(),
             usuario.rol,
             usuario.empleado.id if usuario.empleado else None,
             int(usuario.debe_cambiar_clave)),
            error="No se pudo crear la cuenta.",
            error_integridad=f"El nombre '{usuario.nombre_usuario}' ya esta en uso, "
                             "o ese empleado ya tiene una cuenta.")

        usuario.id = cursor.lastrowid
        return usuario

    # ---------- Read ----------

    def listar(self):
        filas = self._leer_todos(f"{self.SELECT_BASE} ORDER BY nombre_usuario")
        return [self.__fila_a_usuario(fila) for fila in filas]

    def buscar_por_id(self, id_usuario):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE id = ?", (id_usuario,))
        return self.__fila_a_usuario(fila) if fila else None

    def buscar_por_nombre(self, nombre_usuario):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE nombre_usuario = ?",
                              (nombre_usuario,))
        return self.__fila_a_usuario(fila) if fila else None

    def buscar_por_empleado(self, id_empleado):
        fila = self._leer_uno(f"{self.SELECT_BASE} WHERE id_empleado = ?",
                              (id_empleado,))
        return self.__fila_a_usuario(fila) if fila else None

    # ---------- Autenticacion ----------

    def autenticar(self, nombre_usuario, contrasena):
        usuario = self.buscar_por_nombre(nombre_usuario)

        if usuario is None:
            return None
        hash_original = usuario.obtener_hash()
        if not usuario.autenticar(contrasena):
            return None

        if usuario.obtener_hash() != hash_original:
            self.actualizar_contrasena(usuario)

        return usuario

    # ---------- Update ----------

    def actualizar_contrasena(self, usuario):
        cursor = self._escribir(
            "UPDATE usuarios SET contrasena_hash = ? WHERE id = ?",
            (usuario.obtener_hash(), usuario.id),
            error="No se pudo actualizar la contrasena.")

        return cursor.rowcount > 0

    def cambiar_rol(self, id_usuario, nuevo_rol):
        if nuevo_rol not in Usuario.PERMISOS_POR_ROL:
            raise ValueError(f"Rol no reconocido: {nuevo_rol}")

        cursor = self._escribir(
            "UPDATE usuarios SET rol = ? WHERE id = ?",
            (nuevo_rol, id_usuario),
            error="No se pudo cambiar el rol.")

        return cursor.rowcount > 0

    def actualizar(self, usuario, nuevo_rol, contrasena=None):
        if nuevo_rol not in Usuario.PERMISOS_POR_ROL:
            raise ValueError(f"Rol no reconocido: {nuevo_rol}")

        if contrasena:
            usuario.establecer_contrasena(contrasena)
            cursor = self._escribir(
                "UPDATE usuarios SET rol = ?, contrasena_hash = ?, "
                "debe_cambiar_clave = 1 WHERE id = ?",
                (nuevo_rol, usuario.obtener_hash(), usuario.id),
                error="No se pudo actualizar el usuario.")
            usuario.rol = nuevo_rol
            usuario.debe_cambiar_clave = True
            return cursor.rowcount > 0

        cursor = self._escribir(
            "UPDATE usuarios SET rol = ?, contrasena_hash = ? WHERE id = ?",
            (nuevo_rol, usuario.obtener_hash(), usuario.id),
            error="No se pudo actualizar el usuario.")
        usuario.rol = nuevo_rol
        return cursor.rowcount > 0

    def cambiar_contrasena(self, id_usuario, nueva_contrasena):
        usuario = self.buscar_por_id(id_usuario)
        if usuario is None:
            return False

        usuario.establecer_contrasena(nueva_contrasena, minimo=6)
        cursor = self._escribir(
            "UPDATE usuarios SET contrasena_hash = ?, debe_cambiar_clave = 1 "
            "WHERE id = ?",
            (usuario.obtener_hash(), usuario.id),
            error="No se pudo actualizar la contrasena.")
        return cursor.rowcount > 0

    def actualizar_clave_usuario(self, id_usuario, nueva_clave_plana):
        usuario = self.buscar_por_id(id_usuario)
        if usuario is None:
            return False

        usuario.establecer_contrasena(nueva_clave_plana)
        cursor = self._escribir(
            "UPDATE usuarios SET contrasena_hash = ?, debe_cambiar_clave = 0 "
            "WHERE id = ?",
            (usuario.obtener_hash(), usuario.id),
            error="No se pudo actualizar la contrasena.")
        return cursor.rowcount > 0

    # ---------- Delete ----------

    def eliminar(self, id_usuario):
        cursor = self._escribir(
            "DELETE FROM usuarios WHERE id = ?",
            (id_usuario,),
            error="No se pudo eliminar la cuenta.")

        return cursor.rowcount > 0

    # ---------- Fabrica ----------

    def __fila_a_usuario(self, fila):
        empleado = None
        if fila["id_empleado"] is not None:
            empleado = self.repo_empleados.buscar_por_id(fila["id_empleado"])

        return Usuario.desde_hash(
            nombre_usuario=fila["nombre_usuario"],
            contrasena_hash=fila["contrasena_hash"],
            rol=fila["rol"],
            empleado=empleado,
            id_usuario=fila["id"],
            debe_cambiar_clave=fila["debe_cambiar_clave"])
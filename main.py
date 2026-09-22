"""
ECOTECH SOLUTIONS
Programa principal. Construye el sistema sobre SQLite y genera los informes
finales a partir de los datos recuperados desde la base.

"""

from datetime import date
from getpass import getpass
import json
from math import ceil
import sqlite3
from pathlib import Path
from time import monotonic

from database.database import BaseDatos

from modelos.departamento import Departamento
from modelos.empleado import Empleado
from modelos.gerente import Gerente
from modelos.proyecto import Proyecto
from modelos.registro_tiempo import RegistroTiempo
from modelos.usuario import Usuario

from repositorios.departamento_repository import RepositorioDepartamento
from repositorios.empleado_repository import RepositorioEmpleado
from repositorios.proyecto_repository import RepositorioProyecto
from repositorios.registro_repository import RepositorioRegistroTiempo
from repositorios.usuario_repository import RepositorioUsuario
from repositorios.consulta_api_repository import RepositorioConsultaApi

from informes.informe_pdf import InformePDF
from informes.informe_excel import InformeExcel
from servicios.api_externa import ClienteApisExternas, ErrorApiExterna
from seguridad import validaciones as v
from seguridad.validaciones import ErrorDominio, ErrorValidacion
from seguridad.auditoria import (registrar_acceso, registrar_bloqueo,
                                 registrar_evento, registrar_fallo,
                                 mensaje_seguro)


RUTA_BD = Path("ecotech.db")
CARPETA_SALIDA = Path("salidas")
BLOQUEO_BASE_SEGUNDOS = 30
_estado_login = {}


def titulo(texto):
    print()
    print("=" * 66)
    print(f"  {texto}")
    print("=" * 66)


def pedir(mensaje, validador, valor_actual=None, obligatorio=True):
    """Pide un dato por teclado y no avanza hasta que sea valido.

    Si el usuario presiona Enter sin escribir nada y existe un valor actual,
    se conserva ese valor. Asi las actualizaciones no obligan a reescribir
    los campos que no cambian.
    """
    while True:
        entrada = input(mensaje)

        if not entrada.strip():
            if valor_actual is not None:
                return valor_actual
            if not obligatorio:
                return ""

        try:
            return validador(entrada)
        except ErrorValidacion as error:
            print(f"     {error.mensaje} Intentelo nuevamente.")


def cargar_departamento_completo(id_departamento, repo_departamentos, repo_empleados):
    """Arma un Departamento con su personal cargado desde la base."""
    departamento = repo_departamentos.buscar_por_id(id_departamento)
    if departamento is None:
        return None

    for persona in repo_empleados.listar_por_departamento(id_departamento):
        departamento.asignar_empleado(persona)

    return departamento


def cargar_proyecto_completo(id_proyecto, repo_proyectos, repo_empleados, repo_registros):
    """Arma un Proyecto con su equipo y sus jornadas cargados desde la base."""
    proyecto = repo_proyectos.buscar_por_id(id_proyecto)
    if proyecto is None:
        return None

    for persona in repo_empleados.listar_por_proyecto(id_proyecto):
        proyecto.asignar_empleado(persona)

    for registro in repo_registros.listar_por_proyecto(id_proyecto):
        registro.proyecto = proyecto
        proyecto.registros_tiempo.append(registro)

    return proyecto


def respaldar_usuarios_creados():
    """Conserva las cuentas creadas por el usuario al reiniciar los datos demo."""
    if not RUTA_BD.exists():
        return []

    conexion = sqlite3.connect(RUTA_BD)
    try:
        return conexion.execute(
            "SELECT nombre_usuario, contrasena_hash, rol, id_empleado "
            "FROM usuarios"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conexion.close()


def autenticar_usuario(repo_usuarios, intentos_maximos=3):
    """Solicita credenciales y conserva los bloqueos durante la ejecucion."""
    nombre_usuario = input("  Usuario: ").strip()
    usuario = repo_usuarios.buscar_por_nombre(nombre_usuario)
    estado = _estado_login.get(nombre_usuario)
    ahora = monotonic()
    bloqueado_hasta = estado["bloqueado_hasta"] if estado else 0
    if usuario is not None and usuario.bloqueado_hasta:
        bloqueado_hasta = max(bloqueado_hasta, usuario.bloqueado_hasta)
    if bloqueado_hasta > ahora:
        segundos = ceil(bloqueado_hasta - ahora)
        print(f"  Usuario temporalmente bloqueado. Reintente en {segundos} segundos.")
        return None

    intentos = 0
    while intentos < intentos_maximos:
        contrasena = getpass("  Clave: ")
        sesion = repo_usuarios.autenticar(nombre_usuario, contrasena)
        registrar_acceso(usuario, sesion is not None)

        if sesion is not None:
            _estado_login.pop(nombre_usuario, None)
            sesion.bloqueado_hasta = None
            print(f"  Acceso concedido. Sesion: {sesion.nombre_usuario} ({sesion.rol})")
            return sesion

        estado = _estado_login.setdefault(
            nombre_usuario, {"fallos": 0, "bloqueos": 0, "bloqueado_hasta": 0})
        intentos += 1
        estado["fallos"] += 1
        restantes = intentos_maximos - intentos
        if restantes:
            print(f"  Credenciales invalidas. Intentos restantes: {restantes}")

    estado = _estado_login[nombre_usuario]
    estado["bloqueos"] += 1
    estado["fallos"] = 0
    segundos = BLOQUEO_BASE_SEGUNDOS * 2 ** (estado["bloqueos"] - 1)
    estado["bloqueado_hasta"] = monotonic() + segundos
    if usuario is not None:
        usuario.bloqueado_hasta = estado["bloqueado_hasta"]
    print("  Acceso bloqueado: se superó el número de intentos permitidos.")
    registrar_bloqueo(usuario, segundos)
    return None


def completar_cambio_obligatorio(repo_usuarios, sesion, intentos_maximos=3):
    """Obliga a reemplazar una clave temporal antes de entrar al sistema."""
    titulo("Cambio obligatorio de contraseña")
    print("  Su contraseña fue restablecida por un administrador.")
    print("  Debe definir una nueva contraseña para continuar.")

    for intento in range(intentos_maximos):
        actual = getpass("  Contraseña actual/temporal: ")
        if not sesion.autenticar(actual):
            restantes = intentos_maximos - intento - 1
            if restantes:
                print(f"  Contraseña actual incorrecta. Intentos restantes: {restantes}")
            else:
                print("  Se agotaron los intentos. Regresando al menú de login.")
            continue

        nueva = getpass("  Nueva contraseña (Enter para cancelar): ")
        if not nueva:
            print("  Operación cancelada. Regresando al menú de login.")
            return False
        confirmacion = getpass("  Repita la nueva contraseña: ")
        if nueva != confirmacion:
            restantes = intentos_maximos - intento - 1
            if restantes:
                print(f"  Las contraseñas no coinciden. Intentos restantes: {restantes}")
            else:
                print("  Se agotaron los intentos. Regresando al menú de login.")
            continue

        try:
            v.validar_contrasena(nueva, "La contrasena nueva")
            if not repo_usuarios.actualizar_clave_usuario(sesion.id, nueva):
                print("  No se pudo actualizar la contraseña. Regresando al login.")
                return False
        except ErrorValidacion as error:
            restantes = intentos_maximos - intento - 1
            print(f"  {error.mensaje}")
            if restantes:
                print(f"  Intentos restantes: {restantes}")
            else:
                print("  Se agotaron los intentos. Regresando al menú de login.")
            continue

        sesion.debe_cambiar_clave = False
        _estado_login.pop(sesion.nombre_usuario, None)
        sesion.bloqueado_hasta = None
        print("  Contraseña actualizada. Acceso concedido al sistema.")
        return True

    return False


def registrar_nuevo_usuario(repo_usuarios, administrador_autorizado=None):
    """Registra una cuenta con autorizacion de un gerente o administrador."""
    titulo("Crear usuario")
    nombre_usuario = pedir("  Nombre de usuario: ", v.validar_usuario)
    if repo_usuarios.buscar_por_nombre(nombre_usuario) is not None:
        print("  Ese nombre de usuario ya esta registrado.")
        return

    while True:
        contrasena = getpass("  Clave: ")
        confirmacion = getpass("  Confirme la clave: ")
        if contrasena != confirmacion:
            print("  Las claves no coinciden. Intentelo nuevamente.")
            continue
        try:
            v.validar_contrasena(contrasena, "La contrasena")
            break
        except ErrorValidacion as error:
            print(f"  {error.mensaje}")

    opciones_rol = {
        "1": "administrador",
        "2": "gerente",
        "3": "operador",
    }
    print("  1. Administrador")
    print("  2. Gerencia")
    print("  3. Usuario")
    opcion_rol = pedir("  Seleccione el tipo de usuario: ",
                       lambda valor: v.validar_opcion(
                           valor, "La opcion de usuario", set(opciones_rol)))
    rol = opciones_rol[opcion_rol]

    if administrador_autorizado is None:
        print("  Para crear una cuenta debe autorizar un gerente o administrador.")
        nombre_autorizador = input("  Usuario autorizador: ").strip()
        clave_autorizador = getpass("  Clave del autorizador: ")
        administrador_autorizado = repo_usuarios.autenticar(
            nombre_autorizador, clave_autorizador)

    if (administrador_autorizado is None
            or not administrador_autorizado.tiene_permiso("gestionar_usuarios")):
        print("  Autorizacion rechazada. La cuenta no fue creada.")
        return

    usuario = Usuario(nombre_usuario, contrasena, rol)
    repo_usuarios.crear(usuario)
    registrar_evento(
        f"USUARIO CREADO | administrador="
        f"{administrador_autorizado.nombre_usuario if administrador_autorizado else 'registro publico'} | "
        f"usuario={usuario.nombre_usuario} | rol={usuario.rol}")
    print(f"  Usuario '{usuario.nombre_usuario}' creado con rol '{usuario.rol}'.")


def mostrar_usuarios(repo_usuarios):
    """Muestra todas las cuentas almacenadas, sin exponer contrasenas."""
    usuarios = repo_usuarios.listar()
    titulo("Usuarios registrados")
    if not usuarios:
        print("  No hay usuarios registrados.")
        return

    ahora = monotonic()
    print("  ID    USERNAME                       ROL             ESTADO DE BLOQUEO")
    print("  " + "-" * 78)
    for usuario in usuarios:
        estado = _estado_login.get(usuario.nombre_usuario)
        bloqueado_hasta = estado["bloqueado_hasta"] if estado else 0
        if usuario.bloqueado_hasta:
            bloqueado_hasta = max(bloqueado_hasta, usuario.bloqueado_hasta)
        estado_bloqueo = (f"Bloqueado ({ceil(bloqueado_hasta - ahora)} s)"
                          if bloqueado_hasta > ahora else "Desbloqueado")
        empleado = usuario.empleado.nombre if usuario.empleado else "sin empleado asociado"
        print(f"  {usuario.id:<5} {usuario.nombre_usuario:<30} "
              f"{usuario.rol:<15} {estado_bloqueo:<25} | {empleado}")


def cambiar_contrasena_usuario(repo_usuarios):
    mostrar_usuarios(repo_usuarios)
    id_usuario = leer_id("  ID del usuario: ")
    if id_usuario is None:
        return

    usuario = repo_usuarios.buscar_por_id(id_usuario)
    if usuario is None:
        print("  Usuario no encontrado.")
        return

    nueva_contrasena = getpass("  Nueva contraseña: ")
    try:
        v.validar_contrasena(nueva_contrasena, "La contrasena nueva", minimo=6)
        if not repo_usuarios.cambiar_contrasena(id_usuario, nueva_contrasena):
            print("  No se pudo actualizar la contraseña.")
            return
    except ErrorValidacion as error:
        print(f"  {error.mensaje}")
        return

    _estado_login.pop(usuario.nombre_usuario, None)
    usuario.bloqueado_hasta = None
    print("  ¡Contraseña actualizada exitosamente! Se han reiniciado también "
          "los intentos fallidos y el estado de bloqueo.")


def modificar_usuario(repo_usuarios):
    mostrar_usuarios(repo_usuarios)
    id_usuario = leer_id("  ID del usuario a modificar: ")
    if id_usuario is None:
        return

    usuario = repo_usuarios.buscar_por_id(id_usuario)
    if usuario is None:
        print("  Usuario no encontrado.")
        return

    roles = set(Usuario.PERMISOS_POR_ROL)
    print("  Roles disponibles: " + ", ".join(sorted(roles)))
    nuevo_rol = pedir(
        f"  Rol [{usuario.rol}]: ",
        lambda valor: v.validar_opcion(valor, "El rol", roles), usuario.rol)
    nueva_contrasena = getpass(
        "  Nueva clave (Enter para conservar la actual): ")
    repo_usuarios.actualizar(usuario, nuevo_rol, nueva_contrasena or None)
    print(f"  Usuario '{usuario.nombre_usuario}' actualizado correctamente.")


def eliminar_usuario(repo_usuarios, sesion):
    mostrar_usuarios(repo_usuarios)
    id_usuario = leer_id("  ID del usuario a eliminar: ")
    if id_usuario is None:
        return

    usuario = repo_usuarios.buscar_por_id(id_usuario)
    if usuario is None:
        print("  Usuario no encontrado.")
        return
    if usuario.id == sesion.id:
        print("  No puede eliminar la cuenta con la que inicio sesion.")
        return

    confirmacion = pedir(
        f"  ¿Eliminar al usuario '{usuario.nombre_usuario}'? (S/N): ",
        lambda valor: v.validar_opcion(valor, "La confirmacion", {"s", "n"}))
    if confirmacion == "s":
        repo_usuarios.eliminar(usuario.id)
        print("  Usuario eliminado correctamente.")
    else:
        print("  Eliminacion cancelada; no se aplico.")


def menu_usuarios(sesion, repo_usuarios):
    if not sesion.tiene_permiso("gestionar_usuarios"):
        print("  Esta cuenta no tiene permiso para gestionar usuarios.")
        return

    while True:
        titulo("Menu de usuarios")
        print("  1. Mostrar usuarios registrados")
        print("  2. Crear usuario")
        print("  3. Modificar usuario")
        print("  4. Eliminar usuario")
        print("  5. Cambiar contraseña")
        print("  0. Volver")
        opcion = input("  Seleccione una opcion: ").strip()
        try:
            if opcion == "1":
                mostrar_usuarios(repo_usuarios)
            elif opcion == "2":
                registrar_nuevo_usuario(repo_usuarios, sesion)
            elif opcion == "3":
                modificar_usuario(repo_usuarios)
            elif opcion == "4":
                eliminar_usuario(repo_usuarios, sesion)
            elif opcion == "5":
                cambiar_contrasena_usuario(repo_usuarios)
            elif opcion == "0":
                return
            else:
                print("  Opcion no valida.")
        except ErrorDominio as error:
            registrar_fallo(f"Gestion de usuarios opcion {opcion}", error)
            print(f"  {mensaje_seguro(error)}")
        except Exception as error:
            registrar_fallo(f"Gestion de usuarios opcion {opcion}", error)
            print("  No se pudo completar la operacion. Revise los datos e intentelo nuevamente.")


def iniciar_sesion(repo_usuarios, intentos_maximos=3):
    """Permite iniciar sesion o registrar una cuenta nueva."""
    while True:
        titulo("BIENVENIDO A ECOTECH SOLUTIONS")
        print("  1. Ingresar con usuario")
        print("  2. Registrar nuevo usuario")
        print("  0. Salir")
        opcion = input("  Seleccione una opcion: ").strip()

        if opcion == "1":
            sesion = autenticar_usuario(repo_usuarios, intentos_maximos)
            if sesion is not None:
                if (sesion.debe_cambiar_clave
                        and not completar_cambio_obligatorio(repo_usuarios, sesion)):
                    continue
                return sesion
        elif opcion == "2":
            try:
                registrar_nuevo_usuario(repo_usuarios)
            except ErrorDominio as error:
                registrar_fallo("Registro de usuario", error)
                print(f"  {mensaje_seguro(error)}")
        elif opcion == "0":
            return None
        else:
            print("  Opcion no valida.")


def mostrar_historial_consultas(repo_consultas):
    limite = pedir(
        "  Cantidad de consultas [10]: ",
        lambda x: v.validar_entero(x, "La cantidad", minimo=1, maximo=100),
        10)
    try:
        consultas = repo_consultas.listar(limite)
        if not consultas:
            print("  No hay consultas externas guardadas.")
            return

        titulo("Historial de consultas externas")
        for consulta in consultas:
            parametros = json.loads(consulta["parametros_json"])
            respuesta = json.loads(consulta["respuesta_json"])
            resumen = (f"clima: {respuesta.get('estado_tiempo', 'sin estado')}"
                       if consulta["tipo_consulta"] == "clima"
                       else f"tipo de cambio: {respuesta.get('tipo_cambio', 'sin tasa')}")
            print(f"  {consulta['fecha_consulta']} | {consulta['nombre_usuario']} | "
                  f"{consulta['tipo_consulta']} | {parametros} | {resumen}")
    except (ValueError, TypeError, json.JSONDecodeError):
        print("  No se pudo leer el historial de consultas.")
    except Exception as error:
        registrar_fallo("Historial de consultas externas", error)
        print("  No se pudo leer el historial de consultas.")


def consultar_salario_convertido(sesion, repo_empleados, repo_consultas):
    """Convierte un salario base en CLP a otra moneda con la tasa actual."""
    if not sesion.tiene_permiso("ver_salarios"):
        print("  Esta cuenta no tiene permiso para consultar salarios.")
        return

    empleado = repo_empleados.buscar_por_id(leer_id("  ID empleado: "))
    if empleado is None:
        print("  Empleado no encontrado.")
        return

    moneda_destino = pedir(
        "  Moneda de destino [USD]: ",
        lambda x: v.validar_codigo_moneda(x, "La moneda"), "USD")
    try:
        cambio = ClienteApisExternas.consultar_tipo_cambio("CLP", moneda_destino)
        salario_base = empleado.obtener_salario()
        salario_convertido = salario_base * cambio["tipo_cambio"]
        respuesta = {
            "empleado": empleado.nombre,
            "salario_base": salario_base,
            "moneda_base": "CLP",
            "moneda_destino": cambio["destino"],
            "tipo_cambio": cambio["tipo_cambio"],
            "salario_convertido": salario_convertido,
        }
        repo_consultas.crear(
            sesion.nombre_usuario, "salario_convertido",
            {"id_empleado": empleado.id, "origen": "CLP",
             "destino": cambio["destino"]}, respuesta)
        print(f"  Salario de {empleado.nombre}: {salario_base:.2f} CLP")
        print(f"  Tipo de cambio: 1 CLP = {cambio['tipo_cambio']} "
              f"{cambio['destino']}")
        print(f"  Salario convertido: {salario_convertido:.2f} "
              f"{cambio['destino']}")
        print("  Consulta guardada localmente.")
    except ErrorDominio as error:
        print(f"  Dato invalido: {mensaje_seguro(error)}")
    except ErrorApiExterna as error:
        registrar_fallo("Conversion de salario", error)
        print(f"  No fue posible convertir el salario: {error}")
    except Exception as error:
        registrar_fallo("Conversion de salario", error)
        print("  No fue posible convertir el salario en este momento.")


def consultar_servicios_externos(sesion, repo_empleados, repo_consultas):
    """Consulta servicios externos o muestra su historial."""
    if not sesion.tiene_permiso("consultar_externos"):
        print("  Esta cuenta no tiene permiso para consultar servicios externos.")
        return

    titulo("6. Consultas externas para planificacion")
    print("  1. Consultar clima y tipo de cambio")
    print("  2. Ver historial de consultas")
    if sesion.tiene_permiso("ver_salarios"):
        print("  3. Convertir salario a otra moneda")
    print("  0. Volver")
    opcion = input("  Seleccione una opcion: ").strip()
    if opcion == "2":
        mostrar_historial_consultas(repo_consultas)
        return
    if opcion == "3":
        consultar_salario_convertido(sesion, repo_empleados, repo_consultas)
        return
    if opcion == "0":
        return
    if opcion != "1":
        print("  Opcion no valida.")
        return

    ciudad = pedir("  Ciudad [Quillota]: ",
                   lambda x: v.validar_nombre(x, "La ciudad"), "Quillota")
    pais = pedir("  Pais [Chile]: ",
                 lambda x: v.validar_nombre(x, "El pais"), "Chile")
    moneda_origen = pedir("  Moneda de origen [USD]: ",
                          lambda x: v.validar_codigo_moneda(x, "La moneda"), "USD")
    moneda_destino = pedir("  Moneda de destino [CLP]: ",
                           lambda x: v.validar_codigo_moneda(x, "La moneda"), "CLP")

    try:
        clima = ClienteApisExternas.consultar_clima(ciudad, pais)
        repo_consultas.crear(
            sesion.nombre_usuario, "clima", {"ciudad": ciudad, "pais": pais}, clima)
        print(f"  Clima: {clima['temperatura']} grados, humedad {clima['humedad']}%")
        print(f"  Estado del tiempo: {clima['estado_tiempo']} "
              f"(codigo {clima['codigo_climatico']})")
        if clima["alerta"]:
            print(f"  {clima['alerta']}")

        cambio = ClienteApisExternas.consultar_tipo_cambio(
            moneda_origen, moneda_destino)
        repo_consultas.crear(
            sesion.nombre_usuario, "tipo_cambio",
            {"origen": moneda_origen.upper(), "destino": moneda_destino.upper()}, cambio)
        print(f"  Tipo de cambio: 1 {cambio['origen']} = "
              f"{cambio['tipo_cambio']} {cambio['destino']}")
        print("  Respuestas guardadas localmente.")
    except ErrorDominio as error:
        print(f"  Dato invalido: {mensaje_seguro(error)}")
    except ErrorApiExterna as error:
        registrar_fallo("Consulta a servicio externo", error)
        print(f"  Consulta externa no disponible: {error}")
    except Exception as error:
        registrar_fallo("Consulta a servicio externo", error)
        print("  Consulta externa no disponible en este momento.")


def leer_id(mensaje):
    try:
        return v.validar_entero(input(mensaje), "El identificador", minimo=1)
    except ErrorValidacion as error:
        print(f"  {error.mensaje}")
        return None


def mostrar_empleados(repo_empleados, sesion):
    puede_ver_salarios = sesion.tiene_permiso("ver_salarios")
    print("  ID    NOMBRE                         CORREO                         SALARIO       DEPARTAMENTO")
    print("  " + "-" * 105)
    for empleado in repo_empleados.listar():
        departamento = (empleado.departamento.nombre
                        if empleado.departamento else "Sin departamento")
        salario = (f"{empleado.obtener_salario():>12.2f}"
                   if puede_ver_salarios else "************")
        print(f"  {empleado.id:<5} {empleado.nombre:<30} {empleado.correo:<30} "
              f"{salario}  {departamento}")


def crear_empleado(repo_empleados, repo_departamentos):
    nombre = pedir("  Nombre: ", v.validar_nombre)

    while True:
        correo = pedir("  Correo: ", v.validar_correo)
        if repo_empleados.buscar_por_correo(correo) is None:
            break
        print("     Ese correo ya esta registrado. Ingrese otro.")

    salario = pedir("  Salario: ",
                    lambda x: v.validar_decimal(x, "El salario", minimo=0))
    telefono = pedir("  Telefono (opcional): ", v.validar_telefono,
                     obligatorio=False)

    empleado = Empleado(nombre, correo, salario, telefono=telefono)

    mostrar_departamentos(repo_departamentos)
    id_departamento = pedir(
        "  ID departamento (0 para omitir): ",
        lambda x: v.validar_entero(x, "El identificador", minimo=0))

    if id_departamento:
        departamento = repo_departamentos.buscar_por_id(id_departamento)
        if departamento is None:
            print("     Departamento no encontrado; se creara sin departamento.")
        else:
            departamento.asignar_empleado(empleado)

    repo_empleados.crear(empleado)
    print(f"  Empleado creado con ID {empleado.id}.")


def actualizar_empleado(repo_empleados):
    empleado = repo_empleados.buscar_por_id(leer_id("  ID empleado: "))
    if empleado is None:
        print("  Empleado no encontrado.")
        return
    empleado.nombre = pedir(f"  Nombre [{empleado.nombre}]: ",
                            v.validar_nombre, empleado.nombre)
    empleado.correo = pedir(f"  Correo [{empleado.correo}]: ",
                            v.validar_correo, empleado.correo)
    empleado.actualizar_salario(
        pedir(f"  Salario [{empleado.obtener_salario():g}]: ",
              lambda x: v.validar_decimal(x, "El salario", minimo=0),
              empleado.obtener_salario()))
    repo_empleados.actualizar(empleado)
    print("  Empleado actualizado y guardado en la BD.")


def consultar_empleado(repo_empleados, sesion):
    empleado = repo_empleados.buscar_por_id(leer_id("  ID empleado: "))
    if empleado is None:
        print("  Empleado no encontrado.")
    else:
        salario = (str(empleado.obtener_salario())
                   if sesion.tiene_permiso("ver_salarios") else "********")
        print(f"  {empleado.nombre} | {empleado.correo} | "
              f"salario {salario}")


def mostrar_proyectos(repo_proyectos):
    for proyecto in repo_proyectos.listar():
        print(f"  {proyecto.id}: {proyecto.nombre} - {proyecto.descripcion}")


def crear_proyecto(repo_proyectos):
    nombre = pedir("  Nombre: ", v.validar_titulo)
    descripcion = pedir("  Descripcion (opcional): ", v.validar_descripcion,
                        obligatorio=False)
    fecha_inicio = pedir("  Fecha de inicio [AAAA-MM-DD, Enter = hoy]: ",
                         lambda x: v.validar_fecha(x, "La fecha de inicio"),
                         date.today())
    proyecto = Proyecto(nombre, descripcion, fecha_inicio)
    repo_proyectos.crear(proyecto)
    print(f"  Proyecto creado con ID {proyecto.id}.")


def actualizar_proyecto(repo_proyectos):
    proyecto = repo_proyectos.buscar_por_id(leer_id("  ID proyecto: "))
    if proyecto is None:
        print("  Proyecto no encontrado.")
        return
    nombre = pedir(f"  Nombre [{proyecto.nombre}]: ",
                   v.validar_titulo, proyecto.nombre)
    descripcion = pedir(f"  Descripcion [{proyecto.descripcion}]: ",
                        v.validar_descripcion, proyecto.descripcion)
    proyecto.editar_proyecto(nombre=nombre, descripcion=descripcion)
    repo_proyectos.actualizar(proyecto)
    print("  Proyecto actualizado y guardado en la BD.")


def consultar_proyecto(repo_proyectos):
    proyecto = repo_proyectos.buscar_por_id(leer_id("  ID proyecto: "))
    if proyecto is None:
        print("  Proyecto no encontrado.")
    else:
        print(f"  {proyecto.nombre} | {proyecto.descripcion} | "
              f"inicio {proyecto.fecha_inicio}")


def mostrar_departamentos(repo_departamentos):
    for departamento in repo_departamentos.listar():
        print(f"  {departamento.id}: {departamento.nombre}")


def crear_departamento(repo_departamentos):
    departamento = Departamento(pedir("  Nombre: ", v.validar_titulo))
    repo_departamentos.crear(departamento)
    print(f"  Departamento creado con ID {departamento.id}.")


def actualizar_departamento(repo_departamentos):
    departamento = repo_departamentos.buscar_por_id(leer_id("  ID departamento: "))
    if departamento is None:
        print("  Departamento no encontrado.")
        return
    departamento.nombre = pedir(f"  Nombre [{departamento.nombre}]: ",
                                v.validar_titulo, departamento.nombre)
    repo_departamentos.actualizar(departamento)
    print("  Departamento actualizado y guardado en la BD.")


def consultar_departamento(repo_departamentos):
    departamento = repo_departamentos.buscar_por_id(leer_id("  ID departamento: "))
    if departamento is None:
        print("  Departamento no encontrado.")
    else:
        print(f"  {departamento.nombre} | empleados: "
              f"{len(departamento.empleados)}")


def mostrar_registros(repo_registros):
    for registro in repo_registros.listar():
        extra = registro.horas_extras_por_aprobar
        print(f"  {registro.id}: {registro.fecha} | {registro.horas} h "
              f"(aprobadas: {registro.horas_aprobadas:g} h, pendientes: "
              f"{registro.horas_pendientes:g} h, extras por aprobar: "
              f"{extra:g} h) | {registro.empleado.nombre} | "
              f"{registro.proyecto.nombre} [{registro.estado}]")


def crear_registro(repo_registros, repo_empleados, repo_proyectos, sesion):
    mostrar_empleados(repo_empleados, sesion)
    empleado = repo_empleados.buscar_por_id(leer_id("  ID empleado: "))
    mostrar_proyectos(repo_proyectos)
    proyecto = repo_proyectos.buscar_por_id(leer_id("  ID proyecto: "))
    if empleado is None or proyecto is None:
        print("  El empleado y el proyecto deben existir.")
        return
    fecha = pedir("  Fecha [AAAA-MM-DD, Enter = hoy]: ",
                  lambda x: v.validar_fecha(x, "La fecha"), date.today())
    horas = pedir("  Horas: ",
                  lambda x: v.validar_decimal(x, "Las horas", minimo=0.01, maximo=24))
    descripcion = pedir("  Descripcion (opcional): ", v.validar_descripcion,
                        obligatorio=False)
    registro = RegistroTiempo(fecha, horas, descripcion, empleado, proyecto)
    repo_registros.crear(registro)
    print(f"  Registro creado con ID {registro.id}: {registro.horas:g} h, "
          f"pendiente de aprobacion.")


def actualizar_registro(repo_registros):
    registro = repo_registros.buscar_por_id(leer_id("  ID registro: "))
    if registro is None:
        print("  Registro no encontrado.")
        return
    registro.fecha = pedir(f"  Fecha [{registro.fecha}]: ",
                           lambda x: v.validar_fecha(x, "La fecha"), registro.fecha)
    registro.horas = pedir(
        f"  Horas [{registro.horas:g}]: ",
        lambda x: v.validar_decimal(x, "Las horas", minimo=0.01, maximo=24),
        registro.horas)
    registro.descripcion = pedir(f"  Descripcion [{registro.descripcion}]: ",
                                 v.validar_descripcion, registro.descripcion)
    registro.validar_horas()
    registro.aprobado = False
    registro.horas_aprobadas = 0.0
    repo_registros.actualizar(registro)
    print(f"  Registro actualizado: {registro.horas:g} h en total. "
          f"Vuelve a quedar pendiente de aprobacion.")


def consultar_registro(repo_registros):
    registro = repo_registros.buscar_por_id(leer_id("  ID registro: "))
    if registro is None:
        print("  Registro no encontrado.")
    else:
        print(f"  {registro.fecha} | {registro.horas} h | "
              f"{registro.empleado.nombre} | {registro.proyecto.nombre} | "
              f"{registro.descripcion}")


def exportar_datos_json(
        repo_departamentos, repo_empleados, repo_proyectos, repo_registros):
    datos = {
        "departamentos": [
            {"id": departamento.id, "nombre": departamento.nombre}
            for departamento in repo_departamentos.listar()
        ],
        "empleados": [
            {"id": empleado.id, "nombre": empleado.nombre, "correo": empleado.correo,
             "salario": empleado.obtener_salario(),
             "departamento": empleado.departamento.id if empleado.departamento else None}
            for empleado in repo_empleados.listar()
        ],
        "proyectos": [
            {"id": proyecto.id, "nombre": proyecto.nombre,
             "descripcion": proyecto.descripcion,
             "fecha_inicio": str(proyecto.fecha_inicio)}
            for proyecto in repo_proyectos.listar()
        ],
        "registros_horas": [
            {"id": registro.id, "fecha": str(registro.fecha), "horas": registro.horas,
             "horas_normales": registro.horas_normales,
             "horas_extras": registro.horas_extras,
             "horas_extras_por_aprobar": registro.horas_extras_por_aprobar,
             "horas_aprobadas": registro.horas_aprobadas,
             "horas_pendientes": registro.horas_pendientes,
             "estado": registro.estado,
             "aprobado": registro.aprobado,
             "empleado_id": registro.empleado.id, "proyecto_id": registro.proyecto.id,
             "descripcion": registro.descripcion}
            for registro in repo_registros.listar()
        ]
    }
    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / "ecotech_datos.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Respaldo JSON actualizado: {ruta}")


def eliminar_dato(repositorio, nombre, listar):
    listar(repositorio)
    id_dato = leer_id(f"  ID {nombre}: ")
    if id_dato is None:
        return
    confirmacion = pedir(
        "  ¿Eliminar seleccionado? (S/N): ",
        lambda valor: v.validar_opcion(valor, "La confirmacion", {"s", "n"}))
    if confirmacion == "n":
        print("  Eliminacion cancelada; no se aplico.")
    elif repositorio.eliminar(id_dato):
        print("  Dato eliminado y cambio guardado en la BD.")
    else:
        print("  No se encontro el dato o no pudo eliminarse.")


def menu_entidad(sesion, nombre, crear, mostrar, actualizar, eliminar, consultar,
                 sincronizar, solo_consulta=False):
    if not sesion.tiene_permiso("consultar_datos"):
        print("  Esta cuenta no tiene permiso para consultar datos.")
        return
    if not solo_consulta and not sesion.tiene_permiso("gestionar_datos"):
        print("  Esta cuenta no tiene permiso para gestionar datos.")
        return
    while True:
        titulo(f"Menu {nombre}")
        if solo_consulta:
            print("  1. Mostrar")
            print("  2. Consultar")
        else:
            print("  1. Crear")
            print("  2. Mostrar")
            print("  3. Actualizar")
            print("  4. Eliminar")
            print("  5. Consultar")
        print("  0. Volver")
        opcion = input("  Seleccione una opcion: ").strip()
        try:
            if solo_consulta and opcion == "1":
                mostrar()
            elif solo_consulta and opcion == "2":
                consultar()
            elif not solo_consulta and opcion == "1":
                crear()
                sincronizar()
            elif not solo_consulta and opcion == "2":
                mostrar()
            elif not solo_consulta and opcion == "3":
                actualizar()
                sincronizar()
            elif not solo_consulta and opcion == "4":
                eliminar()
                sincronizar()
            elif not solo_consulta and opcion == "5":
                consultar()
            elif opcion == "0":
                return
            else:
                print("  Opcion no valida.")
        except ErrorDominio as error:
            registrar_fallo(f"Operacion '{nombre}' opcion {opcion}", error)
            print(f"  {mensaje_seguro(error)}")
        except Exception as error:
            registrar_fallo(f"Operacion '{nombre}' opcion {opcion}", error)
            print("  No se pudo completar la operacion. "
                  "Revise los datos e intentelo nuevamente.")


def generar_informes(sesion, repo_departamentos, repo_proyectos,
                     repo_empleados, repo_registros, planta):
    titulo("Informes")
    if not sesion.tiene_permiso("generar_informes"):
        print("  La sesion no tiene permiso para generar informes.")
        return
    
    datos = {
        "departamentos": repo_departamentos.listar(),
        "empleados": repo_empleados.listar(),
        "proyectos": [],
        "registros_horas": repo_registros.listar(),
    }
    datos["proyectos"] = [
        cargar_proyecto_completo(item.id, repo_proyectos, repo_empleados, repo_registros)
        for item in repo_proyectos.listar()
    ]
    CARPETA_SALIDA.mkdir(exist_ok=True)
    informe_pdf = InformePDF("Informe general EcoTech")
    informe_excel = InformeExcel("Informe general EcoTech")
    print(informe_pdf.generar_reporte(datos, usuario=sesion))

    print("\n  Exportar informe:")
    print("  1. PDF")
    print("  2. Excel")
    print("  3. PDF y Excel")
    print("  0. No exportar")
    opcion = input("  Seleccione una opcion: ").strip()

    informes = {
        "1": [informe_pdf],
        "2": [informe_excel],
        "3": [informe_pdf, informe_excel],
    }.get(opcion, [])

    if opcion not in {"0", "1", "2", "3"}:
        print("  Opcion no valida. No se exporto el informe.")
        return

    for informe in informes:
        ruta = CARPETA_SALIDA / informe.nombre_archivo()
        ruta.write_bytes(informe.generar_archivo(datos, usuario=sesion))
        print(f"  >>> {informe} guardado en {ruta}")


def menu_principal(
        sesion, repo_departamentos, repo_empleados, repo_proyectos, repo_registros,
    repo_consultas, repo_usuarios, planta):
    sincronizar = lambda: exportar_datos_json(
        repo_departamentos, repo_empleados, repo_proyectos, repo_registros)
    solo_consulta = not sesion.tiene_permiso("gestionar_datos")
    while True:
        titulo("Menu principal")
        print("  1. Empleados")
        print("  2. Proyectos")
        print("  3. Departamentos")
        print("  4. Registros de horas")
        print("  5. Informes")
        if not solo_consulta:
            print("  6. Consultas externas")
            if sesion.tiene_permiso("gestionar_usuarios"):
                print("  7. Usuarios registrados")
                print("  8. Cambiar de usuario")
            else:
                print("  7. Cambiar de usuario")
        else:
            print("  6. Cambiar de usuario")
        print("  0. Salir del programa")
        opcion = input("  Seleccione una opcion: ").strip()
        if opcion == "1":
            menu_entidad(
                sesion, "Empleados",
                lambda: crear_empleado(repo_empleados, repo_departamentos),
                lambda: mostrar_empleados(repo_empleados, sesion),
                lambda: actualizar_empleado(repo_empleados),
                lambda: eliminar_dato(
                    repo_empleados, "empleado",
                    lambda: mostrar_empleados(repo_empleados, sesion)),
                lambda: consultar_empleado(repo_empleados, sesion), sincronizar,
                solo_consulta)
        elif opcion == "2":
            menu_entidad(
                sesion, "Proyectos", lambda: crear_proyecto(repo_proyectos),
                lambda: mostrar_proyectos(repo_proyectos),
                lambda: actualizar_proyecto(repo_proyectos),
                lambda: eliminar_dato(repo_proyectos, "proyecto", mostrar_proyectos),
                lambda: consultar_proyecto(repo_proyectos), sincronizar,
                solo_consulta)
        elif opcion == "3":
            menu_entidad(
                sesion, "Departamentos", lambda: crear_departamento(repo_departamentos),
                lambda: mostrar_departamentos(repo_departamentos),
                lambda: actualizar_departamento(repo_departamentos),
                lambda: eliminar_dato(
                    repo_departamentos, "departamento", mostrar_departamentos),
                lambda: consultar_departamento(repo_departamentos), sincronizar,
                solo_consulta)
        elif opcion == "4":
            menu_entidad(
                sesion, "Registros de horas",
                lambda: crear_registro(
                    repo_registros, repo_empleados, repo_proyectos, sesion),
                lambda: mostrar_registros(repo_registros),
                lambda: actualizar_registro(repo_registros),
                lambda: eliminar_dato(repo_registros, "registro", mostrar_registros),
                lambda: consultar_registro(repo_registros), sincronizar,
                solo_consulta)
        elif opcion == "5":
            generar_informes(
                sesion, repo_departamentos, repo_proyectos, repo_empleados,
                repo_registros, planta)
        elif opcion == "6" and not solo_consulta:
            consultar_servicios_externos(sesion, repo_empleados, repo_consultas)
        elif opcion == "7" and not solo_consulta and sesion.tiene_permiso("gestionar_usuarios"):
            menu_usuarios(sesion, repo_usuarios)
        elif opcion == ("6" if solo_consulta else
                        ("8" if sesion.tiene_permiso("gestionar_usuarios") else "7")):
            return "cambiar_usuario"
        elif opcion == "0":
            return "salir"
        else:
            print("  Opcion no valida.")


def main():

    # ---------------- Preparacion ----------------
    base_nueva = not RUTA_BD.exists()

    bd = BaseDatos()
    bd.crear_tablas()

    repo_departamentos = RepositorioDepartamento(bd)
    repo_empleados = RepositorioEmpleado(bd)
    repo_proyectos = RepositorioProyecto(bd)
    repo_registros = RepositorioRegistroTiempo(bd, repo_empleados, repo_proyectos)
    repo_usuarios = RepositorioUsuario(bd, repo_empleados)
    repo_consultas = RepositorioConsultaApi(bd)

    # ---------------- 1. Personal ----------------
    if base_nueva:
        operaciones = repo_departamentos.crear(Departamento("Operaciones"))
        mantencion = repo_departamentos.crear(Departamento("Mantencion"))

        andres = Gerente("Andres Munoz Pino", "andres.munoz@ecotech.cl", 1650000,
                         area="Operaciones", telefono="+56 9 5555 1000")
        camila = Empleado("Camila Rojas Vergara", "camila.rojas@ecotech.cl", 950000)
        luis = Empleado("Luis Farias Soto", "luis.farias@ecotech.cl", 880000)
        paula = Empleado("Paula Ibarra Leon", "paula.ibarra@ecotech.cl", 1010000)

        for persona in (andres, camila, luis):
            operaciones.asignar_empleado(persona)
        mantencion.asignar_empleado(paula)

        for persona in (andres, camila, luis, paula):
            repo_empleados.crear(persona)

        # ---------------- Ingreso seguro ----------------
        repo_usuarios.crear(Usuario("amunoz", "gerencia-2026", "gerente", empleado=andres))
        repo_usuarios.crear(Usuario("crojas", "camila-2026", "operador", empleado=camila))
        repo_usuarios.crear(Usuario("auditor.externo", "auditoria-2026", "administrador"))
    else:
        operaciones = repo_departamentos.buscar_por_nombre("Operaciones")
        mantencion = repo_departamentos.buscar_por_nombre("Mantencion")
        andres = repo_empleados.buscar_por_correo("andres.munoz@ecotech.cl")
        camila = repo_empleados.buscar_por_correo("camila.rojas@ecotech.cl")
        luis = repo_empleados.buscar_por_correo("luis.farias@ecotech.cl")
        paula = repo_empleados.buscar_por_correo("paula.ibarra@ecotech.cl")

    sesion = iniciar_sesion(repo_usuarios)
    if sesion is None:
        bd.cerrar()
        return

    titulo("1. Estructura organizacional (recuperada desde la base)")
    for registro_dep in repo_departamentos.listar():
        departamento = cargar_departamento_completo(
            registro_dep.id, repo_departamentos, repo_empleados)
        print(f"\n  {departamento.nombre}")
        for persona in departamento.empleados:
            print(f"     - {persona}")
        jefe = departamento.obtener_gerente()
        print(f"     Jefatura: {jefe.nombre if jefe else 'sin gerente asignado'}")

    # ---------------- 2. Proyectos ----------------
    planta = repo_proyectos.buscar_por_nombre("Planta Solar Quillota")
    if planta is None:
        planta = repo_proyectos.crear(Proyecto(
            "Planta Solar Quillota", "Instalacion de paneles fotovoltaicos",
            date(2026, 3, 2)))
    bodega = repo_proyectos.buscar_por_nombre("Bodega Placilla")
    if bodega is None:
        bodega = repo_proyectos.crear(Proyecto(
            "Bodega Placilla", "Automatizacion del sistema de pesaje",
            date(2026, 5, 18)))

    repo_proyectos.asignar_empleado(planta.id, camila.id)
    repo_proyectos.asignar_empleado(planta.id, luis.id)
    repo_proyectos.asignar_empleado(bodega.id, paula.id)
    repo_proyectos.asignar_empleado(bodega.id, camila.id)

    titulo("2. Proyectos y equipos")
    for proyecto in repo_proyectos.listar():
        print(f"\n  {proyecto.nombre}  (inicio {proyecto.fecha_inicio})")
        for persona in repo_empleados.listar_por_proyecto(proyecto.id):
            print(f"     - {persona.nombre}")

    # ---------------- 3. Jornadas ----------------
    titulo("3. Registro y aprobacion de jornadas")
    if base_nueva:
        jornadas = [
            RegistroTiempo(date(2026, 4, 15), 8.0, "Montaje de estructura", camila, planta),
            RegistroTiempo(date(2026, 4, 16), 7.5, "Cableado de paneles", camila, planta),
            RegistroTiempo(date(2026, 4, 16), 6.0, "Instalacion electrica", luis, planta),
            RegistroTiempo(date(2026, 4, 17), 13.0, "Turno extendido", luis, planta),
            RegistroTiempo(date(2026, 5, 20), 8.0, "Calibracion de balanzas", paula, bodega),
        ]
        for jornada in jornadas:
            aprobada = andres.aprobar_horas(jornada)
            repo_registros.crear(jornada)
            if jornada.estado == "parcial":
                estado = (
                    f"{jornada.horas_aprobadas:g} h aprobadas + "
                    f"{jornada.horas_extras_por_aprobar:g} h extra por aprobar"
                )
            else:
                estado = "aprobada" if aprobada else "pendiente de aprobacion"
            print(f"  {jornada.fecha}  {jornada.horas:>5} h  "
                  f"{jornada.empleado.nombre:<22} {estado}")

    print(f"\n  Total de jornadas guardadas: {len(repo_registros.listar())}")
    print(f"  Pendientes de aprobacion:    {len(repo_registros.listar_pendientes())}")
    exportar_datos_json(
        repo_departamentos, repo_empleados, repo_proyectos, repo_registros)

    # ---------------- 4. Cuentas y control de acceso ----------------
    titulo("4. Control de acceso")
    intentos = [
        ("amunoz", "gerencia-2026"),
        ("crojas", "camila-2026"),
        ("amunoz", "clave-equivocada"),
        ("nadie", "lo-que-sea"),
    ]
    for nombre, clave in intentos:
        sesion_prueba = repo_usuarios.autenticar(nombre, clave)
        if sesion_prueba is None:
            print(f"  {nombre:<16} acceso denegado")
        else:
            print(f"  {nombre:<16} autenticado como {sesion_prueba.rol:<14} "
                                f"gestionar_datos: {sesion_prueba.tiene_permiso('gestionar_datos')}")

    print("\n  Proteccion del salario (R5):")
    gerente_bd = repo_empleados.buscar_por_id(andres.id)
    print(f"     Via metodo:        {gerente_bd.obtener_salario()}")
    print(f"     Acceso directo:    {getattr(gerente_bd, 'salario', 'no existe')}")
    try:
        gerente_bd.actualizar_salario(-1)
    except ValueError as error:
        print(f"     Valor invalido:    {error}")

    while sesion is not None:
        accion = menu_principal(
            sesion, repo_departamentos, repo_empleados, repo_proyectos,
            repo_registros, repo_consultas, repo_usuarios, planta)
        if accion != "cambiar_usuario":
            break
        sesion = iniciar_sesion(repo_usuarios)

    # ---------------- Cierre ----------------
    titulo("Resumen")
    print(f"  Departamentos: {len(repo_departamentos.listar())}")
    print(f"  Empleados:     {len(repo_empleados.listar())}")
    print(f"  Proyectos:     {len(repo_proyectos.listar())}")
    print(f"  Jornadas:      {len(repo_registros.listar())}")
    print(f"  Cuentas:       {len(repo_usuarios.listar())}")
    print(f"  Base de datos: {RUTA_BD.resolve()}")

    bd.cerrar()
    print("\n  Conexion cerrada.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Ejecucion interrumpida por el usuario.")
    except Exception as error:
        registrar_fallo("Fallo no controlado en el programa principal", error)
        print("\n  El programa se detuvo por un error inesperado.")
        print("  El detalle quedo registrado en ecotech.log para su revision.")
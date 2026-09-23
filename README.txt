ECOTECH SOLUTIONS - Sistema de gestion de empleados
INACAP Valparaiso - TI3V21 - Programacion Orientada a Objeto Seguro
Evaluacion Sumativa N.2 - Unidades 2 y 3


===============================================================================
 COMO EJECUTARLO
===============================================================================

1. Descomprime el archivo donde quieras.

2. Necesitas Python 3.10 o superior instalado.

3. Abre una terminal DENTRO de la carpeta del proyecto y ejecuta:

       python main.py

   Si en Windows no reconoce el comando, prueba con:  py main.py

No requiere instalar ninguna libreria: usa solo la biblioteca estandar de
Python. Ver requirements.txt.


===============================================================================
 CREDENCIALES DE PRUEBA
===============================================================================

Al iniciar, el sistema ofrece ingresar con una cuenta existente o registrar
una nueva. La clave no se muestra mientras se escribe: eso es intencional,
no es una falla del teclado.

   Usuario           Clave               Rol             Permisos
   ---------------   -----------------   -------------   ----------------------
   amunoz            gerencia-2026       gerente         datos, informes, APIs
   auditor.externo   auditoria-2026      administrador   todos
   crojas            camila-2026         operador        solo consulta e informes

Para recorrer el sistema completo, entra como amunoz.
La cuenta crojas sirve para comprobar que el control de acceso funciona:
al ser operador, solo ve el menu simplificado de consultas e informes.

Se permiten tres intentos por ciclo. Tras tres fallos para el mismo usuario,
se aplica un bloqueo temporal creciente que se conserva aunque se vuelva al
menu de inicio. Todos los intentos y bloqueos quedan registrados en ecotech.log.


===============================================================================
 QUE HACE
===============================================================================

Al ejecutarse, el programa:

  1. Crea la base de datos SQLite desde cero.
  2. Carga datos de ejemplo: 2 departamentos, 4 empleados, 2 proyectos
     y 5 jornadas de trabajo.
  3. Pide credenciales.
  4. Muestra la estructura recuperada desde la base.
  5. Registra y aprueba las jornadas segun la regla del gerente.
  6. Abre un menu con operaciones CRUD, informes y consultas externas.

Menu principal:

 Administrador y gerente:
  1. Empleados            Crear, mostrar, actualizar, eliminar, consultar
  2. Proyectos            Idem
  3. Departamentos        Idem
  4. Registros de horas   Idem
  5. Informes             Genera PDF y Excel en salidas/
  6. Consultas externas   Geolocalizacion, clima, tipo de cambio y historial
  7. Crear usuario        Gestion de cuentas segun autorizacion

 Usuario:
  1. Empleados            Mostrar y consultar
  2. Proyectos            Mostrar y consultar
  3. Departamentos        Mostrar y consultar
  4. Registros de horas   Mostrar y consultar
  5. Informes             Genera PDF y Excel en salidas/

Menu de consultas externas:

  1. Consultar geolocalizacion
  2. Consultar clima
  3. Consultar tipo de cambio
  4. Convertir salario a otra moneda
  5. Ver historial de consultas
  0. Volver

La consulta de geolocalizacion usa la API por IP para obtener la direccion
publica detectada, junto con ciudad, pais y proveedor de internet. El sistema
mantiene la geolocalizacion automatica como ayuda para sugerir una ubicacion
por defecto para otras consultas, pero ahora el usuario tambien puede invocarla
explcitamente desde el menu y visualizar los datos reales obtenidos de la API.
Al comenzar, el sistema permite iniciar sesión o registrar un usuario nuevo.
Al registrar una cuenta se solicita nombre de usuario, clave y rol. Los roles
disponibles son administrador, gerente y operador (usuario común). Para crear
cualquier tipo de cuenta se solicitan las credenciales de un gerente o
administrador existente.


===============================================================================
 SEGURIDAD
===============================================================================

AUTENTICACION
  Las claves se guardan como resumen SHA-256 con sal aleatoria por cuenta,
  nunca en texto plano. La comparacion usa tiempo constante para no revelar
  informacion por la duracion de la respuesta. El acceso permite tres intentos
  por ciclo; los fallos consecutivos para el mismo usuario activan bloqueos
  temporales crecientes, desde 30 segundos, que se conservan al volver al menu.

AUTORIZACION
  Cada rol tiene un conjunto de permisos declarado en un unico lugar. El menu
  los comprueba antes de ejecutar cualquier operacion.

MODULO DE GESTION DE USUARIOS Y ROLES (RBAC)
  La aplicacion administra cuentas de acceso desde un repositorio central de
  usuarios, donde cada cuenta tiene nombre de usuario, rol, empleado asociado,
  estado de bloqueo y bandera de cambio obligatorio de clave.

  Los roles implementados son administrador, gerente y operador, con permisos
  distintos definidos en modelos/usuario.py:

    * administrador: acceso completo a gestion de usuarios, consulta de salarios,
      generacion de informes, aprobacion de jornadas y consultas externas.
    * gerente: puede gestionar datos, aprobar jornadas, generar informes,
      consultar salarios y crear o modificar usuarios en el sistema.
    * operador: solo puede consultar informacion y generar informes basicos.

  La gestion de usuarios solo esta disponible para cuentas con el permiso
  gestionar_usuarios. Desde ese menu se permite:

    * listar usuarios registrados y su estado de bloqueo,
    * crear cuentas con validacion de clave y rol,
    * cambiar la contraseña de otra cuenta,
    * modificar el rol del usuario,
    * eliminar cuentas no asociadas a la sesion actual.

  La recuperacion o restablecimiento de clave temporal se implementa como un
  flujo de seguridad: si una clave fue reformulada por administracion o se marca
  como obligatoria, el usuario no puede seguir usando la sesion hasta definir una
  nueva contraseña. El cambio se realiza validando la clave actual, confirmando
  la nueva clave y revisando la complejidad exigida por la politica del sistema.

  La asignacion del rol Administrador queda restringida a la autorizacion de una
  cuenta ya existente con permisos de gestion. Es decir, nadie puede autoproclamarse
  administrador desde el registro publico; la creacion de perfiles con permisos
  avanzados requiere la autenticacion de un gerente o administrador valido, con
  verificacion previa del permiso gestionar_usuarios.

FLUJO DE AUTENTICACION Y SEGURIDAD
  El inicio de sesion valida usuario y clave usando hashes PBKDF2 con sal por
  cuenta, y se compara mediante hmac.compare_digest para evitar fugas por tiempo.
  El sistema admite tres intentos fallidos por ciclo; si se excede ese limite,
  la cuenta queda bloqueada temporalmente durante un periodo creciente basado en
  el numero de bloqueos anteriores. Ese estado se conserva durante la ejecucion
  y aparece en la visualizacion de usuarios.

  Cuando una cuenta tiene una clave temporal o se le exige cambio de contraseña,
  el programa fuerza el cambio obligatorio antes de permitir el uso normal del
  sistema. El usuario debe ingresar la contraseña actual, escribir la nueva clave
  dos veces y cumplir la validacion de seguridad antes de continuar.

  Adicionalmente, la auditoria registra accesos validos e invalidos, bloqueos
  temporales y errores de dominio en ecotech.log para dejar trazabilidad sin
  exponer detalles internos al usuario final.

ENMASCARAMIENTO DE DATOS EN INFORMES (DATA MASKING)
  Los informes PDF y Excel usan la capa de validacion para aplicar enmascaramiento
  de datos sensibles segun el rol del usuario que genera el reporte.

  La funcion usuario_puede_ver_salarios() permite distinguir entre usuarios con
  permisos de salario (gerentes y administradores) y perfiles con menos alcance.
  En informes, las columnas de salario y correo se procesan con:

    * formatear_salario_informe(): devuelve el monto real para gerente o
      administrador, y oculta el valor con asteriscos para usuarios sin permiso.
    * formatear_correo_informe(): muestra el correo completo para usuarios con
      permisos suficientes; para perfiles restringidos, solo expone un correo
      parcialmente enmascarado, preservando la identidad sin revelar el dato
      completo.

  De este modo, el mismo informe puede reutilizarse para distintos perfiles sin
  filtrar el contenido manualmente: los roles con mayor privilegio reciben datos
  completos y los roles operativos ven una representacion segura y legible.

VALIDACION DE ENTRADAS
  Todo dato que entra al sistema pasa por seguridad/validaciones.py, que
  verifica tipo, rango, longitud y formato mediante expresiones regulares.
  El modulo lo usan por igual las clases del dominio, el menu y el cliente
  de APIs externas: un solo criterio, un solo lugar.

MENSAJES DE ERROR
  El usuario recibe mensajes del dominio. El detalle tecnico -sentencias SQL,
  restricciones violadas, trazas de red- se guarda en ecotech.log y no llega
  a la pantalla.

CONSULTAS A BASE DE DATOS
  Todas usan parametros enlazados, nunca concatenacion de texto. Es la
  defensa estandar contra inyeccion SQL.


===============================================================================
 SERVICIOS EXTERNOS
===============================================================================

  Geolocalizacion    http://ip-api.com/json
  Geocodificacion    https://geocoding-api.open-meteo.com/v1/search
  Pronostico         https://api.open-meteo.com/v1/forecast
  Tipo de cambio     https://open.er-api.com/v6/latest

La geolocalizacion por IP se usa para detectar ciudad, pais y proveedor del
usuario actual, y puede consultarse directamente desde el menu de servicios
externos. La geocodificacion se reutiliza internamente cuando se consulta clima
para convertir la ubicacion en coordenadas, y la API de pronostico devuelve la
informacion meteorologica real. La API de tipo de cambio se usa tanto para la
consulta independiente como para la conversion de salario a otra moneda.

Ninguno requiere llave de acceso, de modo que no hay credenciales de API en
el codigo. El tiempo de espera y las direcciones se leen de variables de
entorno, con valores por defecto:

  ECOTECH_URL_IP_GEO
  ECOTECH_URL_GEOCODIFICACION
  ECOTECH_URL_PRONOSTICO
  ECOTECH_URL_TIPO_CAMBIO
  ECOTECH_API_TIMEOUT          (8 segundos por defecto)

Si no hay conexion a internet, las opciones de servicios externos informan que
el servicio no esta disponible y el programa continua sin interrumpirse. El
resto del sistema funciona sin conexion.

Las respuestas obtenidas se guardan en la tabla consultas_api, con el usuario
que consulto, los parametros y la respuesta completa.


===============================================================================
 ESTRUCTURA
===============================================================================

  main.py            Programa principal y menu
  modelos/           Las 9 clases del dominio
  informes/          Jerarquia Informe / InformePDF / InformeExcel
  repositorios/      Acceso a la base de datos (patron repositorio)
  database/          Conexion y esquema SQLite
  seguridad/         Validacion de entradas y registro de auditoria
  servicios/         Cliente de APIs externas
  USO_DE_IA.md       Registro del uso de herramientas de IA
  tests/             Pruebas automatizadas (8 casos)
  registrar_prompt.py  Comando para registrar prompts en USO_DE_IA.md
  requirements.txt   Declaracion de dependencias (no hay externas)

===============================================================================
 PRUEBAS AUTOMATIZADAS
===============================================================================

Desde la carpeta del proyecto:

       python -m unittest discover -s tests -t .

Tambien es posible ejecutar una prueba puntual, por ejemplo:

       python -m unittest tests.test_registrar_prompt
       python -m unittest tests.test_registro_tiempo
       python -m unittest tests.test_salario_convertido

Debe terminar con "OK" y la cantidad de pruebas esperadas. El proyecto usa
unittest de la biblioteca estandar, sin dependencias externas ni pytest.

Que cubren:

  test_registro_tiempo.py         Aprobacion parcial de jornadas y horas extras
  test_salario_convertido.py      Conversion de salario y permiso ver_salarios
  test_api_externa.py             Respuestas de las APIs simuladas, sin internet
  test_informes_masking.py        Enmascaramiento de salarios y correos en PDF/Excel
  test_registrar_prompt.py        Registro de prompts con archivo temporal seguro

Las pruebas de la API no usan conexion: simulan cada codigo de respuesta HTTP
con unittest.mock, de modo que corren igual sin acceso a internet. Las pruebas
que validan informes y auditoria mantienen la salida consistente con los permisos
de cada rol.


===============================================================================
 ARCHIVOS QUE SE GENERAN AL EJECUTAR
===============================================================================

  ecotech.db         Base de datos SQLite
  ecotech.log        Registro de accesos y errores
  salidas/           Informes generados y respaldo en JSON

Ninguno viene incluido en la entrega: los tres se crean solos.
main.py reinicia los datos de demostracion al iniciar, pero conserva las
cuentas de usuario creadas desde la opcion 7 para que puedan volver a iniciar
sesion en ejecuciones posteriores.

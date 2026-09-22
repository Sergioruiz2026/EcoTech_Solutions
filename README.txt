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
  6. Consultas externas   Clima y tipo de cambio desde APIs
  7. Crear usuario        Gestion de cuentas segun autorizacion

 Usuario:
  1. Empleados            Mostrar y consultar
  2. Proyectos            Mostrar y consultar
  3. Departamentos        Mostrar y consultar
  4. Registros de horas   Mostrar y consultar
  5. Informes             Genera PDF y Excel en salidas/

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

  Geocodificacion    https://geocoding-api.open-meteo.com/v1/search
  Pronostico         https://api.open-meteo.com/v1/forecast
  Tipo de cambio     https://open.er-api.com/v6/latest

Ninguno requiere llave de acceso, de modo que no hay credenciales de API en
el codigo. El tiempo de espera y las direcciones se leen de variables de
entorno, con valores por defecto:

  ECOTECH_URL_GEOCODIFICACION
  ECOTECH_URL_PRONOSTICO
  ECOTECH_URL_TIPO_CAMBIO
  ECOTECH_API_TIMEOUT          (8 segundos por defecto)

Si no hay conexion a internet, la opcion 6 informa que el servicio no esta
disponible y el programa continua sin interrumpirse. El resto del sistema
funciona sin conexion.

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

Debe terminar con "OK" y 8 pruebas ejecutadas. No requiere instalar pytest ni
ninguna otra herramienta: usa el modulo unittest de la biblioteca estandar.

Que cubren:

  test_registro_tiempo.py     Aprobacion parcial de jornadas y horas extras
  test_salario_convertido.py  Conversion de salario y permiso ver_salarios
  test_api_externa.py         Respuestas de las APIs simuladas, sin internet

Las pruebas de la API no usan conexion: simulan cada codigo de respuesta HTTP
con unittest.mock, de modo que corren igual sin acceso a internet.


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

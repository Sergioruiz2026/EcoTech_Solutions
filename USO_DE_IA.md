# Registro del uso de herramientas de IA

**Proyecto:** EcoTech Solutions — Sistema de gestión de empleados
**Asignatura:** TI3V21 — Programación Orientada a Objeto Seguro
**Evaluación:** Sumativa N.º 2 — Unidades 2 y 3
**Criterios que documenta:** 2.1.5 y 3.1.4

---

## 1. Herramienta utilizada

| Dato | Detalle |
|---|---|
| Herramienta | Claude (Anthropic), asistente conversacional |
| Modalidad de uso | Sesión guiada: se describía el objetivo, la herramienta proponía código, el equipo lo probaba en su equipo y devolvía el resultado real de la ejecución |
| Alcance | Módulo de validación de entradas, aprobación parcial de jornadas, manejo seguro de mensajes de error y registro de auditoría |
| Qué **no** se generó con IA | El modelo UML de la Unidad 1, la estructura de clases original, los repositorios y el cliente de APIs externas. Esas piezas fueron escritas por el equipo antes de esta sesión |

**Criterio de trabajo adoptado:** ninguna propuesta se incorporó sin ejecutarla primero. Cada fragmento se probó en el equipo, y varias correcciones surgieron precisamente de esa ejecución, no de la lectura del código.

---

## 2. Fragmentos apoyados en IA y decisión tomada

### 2.1 Módulo de validación de entradas — `seguridad/validaciones.py`

**Qué se pidió:** un módulo único que centralizara la verificación de tipo, rango, longitud y formato de todo dato que entra al sistema.

**Qué devolvió:** el módulo completo, con expresiones regulares para nombres, correos, teléfonos y nombres de usuario, y una excepción propia que identifica el campo que falló.

**Qué encontramos al probarlo:** la función que convierte números interpretaba mal los decimales. Como acepta el formato chileno de miles (`1.650.000`), eliminaba todos los puntos, y entonces `0.2` se convertía en `2.0`.

**Por qué era grave:** no producía ningún error visible. Simplemente guardaba un número equivocado. Los errores que no se anuncian son los que más cuesta detectar.

**Cómo se corrigió:** se sustituyó la regla «borrar todos los puntos» por una que distingue el contexto — si hay coma, la coma es el decimal y los puntos son miles; si solo hay puntos, se consideran miles únicamente cuando agrupan de a tres dígitos.

**Decisión: ADOPTADO CON CORRECCIÓN.**

---

### 2.2 Aprobación parcial de jornadas — `modelos/registro_tiempo.py`, `modelos/gerente.py`

**Qué se pidió:** revisar la coherencia entre el mensaje que muestra el programa y lo que efectivamente se guarda.

**Qué se detectó:** al registrar una jornada de trece horas, el programa informaba *«12 h aprobadas + 1 h extra pendiente»*, pero el método de aprobación devolvía un rechazo y la jornada quedaba marcada como no aprobada **en su totalidad**. Ni la clase ni la tabla contemplaban una aprobación parcial: el campo admitía solo dos estados.

**Las dos opciones evaluadas:** cambiar el mensaje para que dijera únicamente que la jornada quedó pendiente, o ampliar el modelo para que la aprobación parcial existiera de verdad.

**Qué se decidió y por qué:** se amplió el modelo. Bajar el mensaje habría resuelto la contradicción perdiendo una funcionalidad que ya estaba a medio camino. Se agregó el atributo `horas_aprobadas`, la columna correspondiente en la base con su restricción, y el desglose en ambos informes.

**Verificación:** se consultó la tabla directamente después de ejecutar. La jornada figura con `13.0` horas registradas y `12.0` aprobadas. El mensaje dejó de ser una promesa.

**Decisión: ADOPTADO CON AMPLIACIÓN DEL MODELO.**

---

### 2.3 Enmascaramiento de mensajes de error — `seguridad/auditoria.py`

**Qué se pidió:** evitar que los mensajes de error mostraran información interna del sistema. Los repositorios concatenaban el detalle de SQLite, de modo que en pantalla aparecía `UNIQUE constraint failed: departamentos.nombre`, revelando nombres de tablas y columnas.

**Qué devolvió:** un módulo de auditoría que envía el detalle técnico a un archivo de registro y devuelve al usuario un mensaje genérico.

**Qué falló en la primera versión:** resultó demasiado estricto. Ocultaba también mensajes que eran perfectamente seguros de mostrar, como *«Ya existe un departamento llamado 'Operaciones'»*, que está redactado para el usuario y no expone nada. El resultado era peor que el problema original: el usuario dejaba de saber qué había pasado.

**Cómo se corrigió:** se introdujo una jerarquía de excepciones. `ErrorDominio` agrupa los errores cuyo mensaje redactamos nosotros y que por lo tanto son seguros de mostrar; todo lo demás se reemplaza por un texto genérico. La decisión la toma el tipo de la excepción, no una revisión manual de cada mensaje.

**Decisión: ADOPTADO DESPUÉS DE DOS ITERACIONES.**

---

### 2.4 Bloque de comprobación del salario — `main.py`

**Qué ocurrió:** un fragmento sugerido previamente se incorporó al programa con una indentación incorrecta, quedando dentro del bucle que recorre los intentos de acceso. El mensaje se imprimía una vez por cada usuario autenticado.

**Cómo se detectó:** ejecutando el programa y comparando la salida con la esperada. No produce ningún error de sintaxis, así que el editor no lo señala.

**Decisión: CORREGIDO.** Sirve como advertencia: en Python la indentación es sintaxis, y un fragmento pegado desde otro contexto puede cambiar de significado sin dejar rastro.

---

### 2.5 Constante duplicada — `modelos/gerente.py`

**Qué se detectó:** el límite de doce horas estaba escrito dos veces, en dos clases distintas y con nombres distintos: como tope de aprobación del gerente y como duración de la jornada normal en el registro de tiempo. Coincidían por casualidad.

**Por qué importaba:** el día que alguien modificara una, la otra quedaría desfasada y el sistema empezaría a contradecirse sin que nadie lo notara.

**Cómo se corrigió:** la constante quedó definida en un solo lugar y la otra clase la referencia.

**Decisión: CORREGIDO.**

---

### 2.6 Unificación de la validación en el cliente de APIs — `servicios/api_externa.py`

**Qué se encontró:** el cliente de APIs ya validaba correctamente ciudad, país y moneda con sus propias expresiones regulares. El problema no era la calidad, sino que existían **dos criterios de validación distintos** conviviendo en el mismo sistema.

**Qué se decidió:** reemplazar las validaciones propias del cliente por llamadas al módulo único. No porque las anteriores estuvieran mal, sino porque dos implementaciones separadas tienden a divergir con el tiempo.

**Decisión: REFACTORIZADO POR CRITERIO DE MANTENIBILIDAD.**

---

### 2.7 Comparación de nombres sensible a mayúsculas — `database/database.py`

**Este hallazgo no provino de la IA.**

Durante una prueba manual del menú se escribió `operaciones` en minúscula, existiendo ya un departamento llamado `Operaciones`. El sistema lo aceptó y creó un segundo registro.

**La causa:** SQLite compara texto distinguiendo mayúsculas de minúsculas. La restricción `UNIQUE` estaba correctamente declarada, pero para el motor eran dos valores diferentes. Para cualquier persona son el mismo departamento.

**Por qué la IA no lo anticipó:** porque el código era formalmente correcto. El problema no estaba en la sintaxis ni en la lógica, sino en el desajuste entre cómo compara el motor y cómo entiende un nombre una persona.

**Cómo se corrigió:** se añadió `COLLATE NOCASE` a las cuatro columnas que identifican una entidad por su nombre: nombre de departamento, nombre de proyecto, correo de empleado y nombre de usuario.

**Decisión: CORRECCIÓN DE ORIGEN PROPIO.** Es el ejemplo más claro de la sesión de que probar el sistema encuentra cosas que revisar el código no encuentra.

---

## 3. Decisiones técnicas que se sostuvieron

### 3.1 Uso de `urllib` en lugar de `requests`

La guía menciona `requests` como ejemplo de librería oficial. El proyecto usa `urllib`, de la biblioteca estándar.

**Fundamento:** `urllib` forma parte de la instalación estándar de Python, mientras que `requests` es una dependencia de terceros que debe instalarse. Mantener el proyecto sin dependencias externas simplifica su ejecución en cualquier equipo y reduce la superficie de riesgo.

**Se mantiene la decisión**, con la justificación disponible para la defensa.

### 3.2 Servicios externos sin autenticación

Los tres servicios consumidos —geocodificación, pronóstico del tiempo y tipo de cambio— no requieren llave de acceso.

**Implicancia:** el manejo de credenciales de API no aplica a este proyecto. El mecanismo que se usaría está de todos modos presente: el tiempo de espera y las direcciones de los servicios se leen de variables de entorno, con un valor por defecto. Una llave se gestionaría del mismo modo, nunca escrita dentro del código.

---

## 4. Balance del uso de IA

**Dónde aportó valor:** produjo estructuras completas y correctas en minutos —el módulo de validación son más de doscientas líneas— e incorporó correcciones con precisión cuando se le indicó qué estaba mal.

**Dónde no bastó:** de los siete casos documentados, **tres se detectaron ejecutando el programa, no leyéndolo**: el error del separador decimal, la indentación del bloque de salario y la comparación sensible a mayúsculas. Ninguno produce un error visible; los tres habrían pasado inadvertidos en una revisión de código.

**La conclusión que deja el proceso:** el valor de la herramienta depende de tener un criterio propio con el cual contrastarla. Las correcciones más importantes no surgieron de pedirle a la IA que revisara su propio trabajo, sino de ejecutar el sistema y comparar lo que hacía con lo que debía hacer.

---

## 5. Pendiente de completar por el equipo

> Esta sección debe ser completada por quienes desarrollaron el código original.
> Está en blanco a propósito: documentar un uso de IA que no ocurrió es peor que no documentarlo.

**Código anterior a esta sesión** — clases de dominio, repositorios, cliente de APIs externas, menú interactivo:

- Herramienta utilizada:
- Fragmentos generados o apoyados en IA:
- Qué se adoptó sin cambios y por qué:
- Qué se modificó y con qué criterio:
- Qué se descartó y por qué:

**Para cada fragmento conviene registrar:** qué se pidió, qué devolvió la herramienta, qué se detectó al revisarlo o ejecutarlo, y qué se decidió.

## 6. Registro cronológico de prompts

Los prompts nuevos se agregan con el comando siguiente desde la carpeta del proyecto:

```text
python registrar_prompt.py "Texto completo del prompt" --herramienta "Nombre de la herramienta" --decision "Pendiente"
```

El comando registra inmediatamente la fecha, la herramienta, el prompt y la decisión en la tabla siguiente. El archivo se vacía y sincroniza en cada registro antes de continuar. La conversación del editor no puede capturarse automáticamente desde Python; por eso cada prompt debe pasar por este comando en el momento en que se ejecuta.

| Fecha | Herramienta | Prompt | Decisión |
|---|---|---|---|
| 2026-09-16 | GitHub Copilot | Implementar en los archivos para que cada vez que se realice un prompt se registre acá. | Adoptado: se agregó un registrador documental y un comando para ejecutarlo. |
| 2026-09-20 | GitHub Copilot | los prompt no se estan guardando en el .md | Pendiente de revisión: el registrador funciona mediante `registrar_prompt.py`, pero la conversación del editor no puede capturarse automáticamente desde Python. |
| 2026-09-20 20:32:18 | Claude | En mi proyecto Python EcoTech (solo biblioteca estandar) el permiso ver_salarios existe en modelos/usuario.py pero ningun menu lo usa, y el rol operador ve todos los salarios en main.py (mostrar_empleados y consultar_empleado). Modifica el codigo para que el salario solo se muestre si la sesion tiene el permiso como administrador o gerente ver_salarios y en caso contrario aparezca enmascarado. Cambia lo minimo, explica cada cambio. Ademas, explicame que opciones hay para el registro publico de operadores, sin implementarlas todavia. | Adoptado: se aplicó la verificación de permisos en la capa de menú y el salario se muestra o enmascara según `sesion.tiene_permiso("ver_salarios")`; la explicación del registro público quedó como opción futura y no como cambio implementado. |
| 2026-09-20 20:35:20 | Claude | En mi proyecto Python EcoTech la funcion registrar_acceso de seguridad/auditoria.py guarda en ecotech.log el texto que el usuario escribe en el campo Usuario, y ahi terminan claves escritas por error. Modifica el flujo de autenticacion en main.py y auditoria.py para registrar el nombre solo si existe en la base de datos y, si no existe, registrar usuario desconocido. Solo biblioteca estandar y sin romper los demas mensajes. Explica el cambio y como comprobarlo revisando el log. | Adoptado: la auditoría ahora registra solo usuarios validados; si no existen, se escribe `usuario desconocido` en `ecotech.log` sin dejar caer texto arbitrario del input. |
| 2026-09-20 20:37:25 | Claude | En mi proyecto Python EcoTech el limite de tres intentos de login en main.py (autenticar_usuario e iniciar_sesion) se reinicia al volver al menu de inicio, asi que se puede reintentar sin limite, y el README dice que el programa termina. Implementa un control que no se reinicie al volver al menu, por ejemplo un bloqueo temporal creciente por nombre de usuario, con solo biblioteca estandar. Registra el bloqueo en ecotech.log, explica ventajas y limites de la solucion elegida y sugiere pruebas. | Adoptado: se implementó un bloqueo temporal persistente por usuario con crecimiento progresivo de espera y registro de eventos en `ecotech.log`, sin reiniciar al volver al menú. |
| 2026-09-20 20:39:35 | Claude | En mi proyecto Python EcoTech modelos/usuario.py guarda las contrasenas con SHA-256 mas sal en una sola pasada. Cambialo a hashlib.pbkdf2_hmac con SHA-256 y al menos 600000 iteraciones, guardando en el hash el algoritmo y las iteraciones, y comparando con hmac.compare_digest. Manten compatibilidad con el formato antiguo (sal y resumen separados por un simbolo de dolar) y, si un hash antiguo entra correctamente, actualiza la cuenta al formato nuevo usando repositorios/usuario_repository.py. Solo biblioteca estandar. Explica por que el cambio y como probar que las cuentas existentes siguen entrando. | Adoptado: se migró a `hashlib.pbkdf2_hmac` con `sha256`, 600000 iteraciones y compatibilidad con hashes heredados; la comprobación usa `hmac.compare_digest` y actualiza automáticamente la contraseña al formato nuevo. |
| 2026-09-20 20:41:11 | Claude | En mi proyecto Python EcoTech servicios/api_externa.py trata todos los codigos HTTP distintos de 200 con el mismo mensaje. Mejoralo para dar un mensaje seguro distinto segun 400, 401 o 403, 404, 429 y 5xx, para validar que el JSON recibido sea un objeto y que rates sea un diccionario, y para comparar el pais sin distinguir tildes. Solo biblioteca estandar, mensajes sin URLs ni detalles internos. Escribe pruebas con unittest.mock que simulen cada caso sin usar internet. | Adoptado: el cliente de APIs ahora distingue mensajes por código HTTP, valida la estructura JSON y `rates`, normaliza el país sin distinguir tildes y mantiene una respuesta segura sin exponer detalles internos. |
| 2026-09-20 20:42:52 | Claude | En mi proyecto Python EcoTech la opcion 6 de main.py consulta clima y tipo de cambio pero solo imprime temperatura y humedad, y guarda el weather_code sin mostrarlo. Traduce el weather_code de Open-Meteo a un estado del tiempo en texto, muestra una alerta si hay lluvia o tormenta, y agrega una opcion para ver el historial de consultas usando RepositorioConsultaApi.listar. Solo biblioteca estandar, reutilizando seguridad/validaciones.py. Explica el diseno. | Adoptado: se traduce el `weather_code` a texto legible, se muestra una alerta por lluvia/tormenta y se agregó el historial de consultas a través de `RepositorioConsultaApi.listar`. |
| 2026-09-20 20:45:05 | Claude | En mi proyecto Python EcoTech el planteamiento pide calcular pagos ajustados al pais del proyecto. Agrega una opcion que calcule el salario de un empleado en otra moneda usando el tipo de cambio consultado, visible solo con el permiso ver_salarios, validando las entradas con seguridad/validaciones.py y manejando fallos de la API sin detener el programa. Solo biblioteca estandar. Explica el diseno y sugiere pruebas. | Adoptado: se agregó la conversión de salario a otra moneda con validación de entrada, permiso `ver_salarios` y manejo de errores de la API sin interrumpir la ejecución del menú. |
| 2026-09-21 11:26:20 | No especificada | por que no crea una cuenta de usuario como administrador si le doy autorizacion con credenciales de gerencia? | Pendiente |
| 2026-09-21 12:05:04 | Copilot | Prueba de funcionamiento de Copilot | Confirm? la respuesta con la IA. |
| 2026-09-21 12:06:35 | copilot | necesito verificar archivo registrar_prompt.py si esta funcionando correctamente, IA utilizada copilot | La verificación ha mostrado que el script se ejecuta, pero estoy confirmando también que la escritura final en el registro quedó correcta en el documento de auditoría. |
| 2026-09-21 12:08:51 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:09:09 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:24:47 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:27:51 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:29:54 | No especificada | Actúa como un desarrollador senior en Python experto en Clean Architecture y seguridad. | Necesito implementar enmascaramiento de datos (Data Masking) para los salarios de los empleados en la generación de informes (PDF y Excel) del proyecto EcoTech Solutions. |
| 2026-09-21 12:31:01 | gemini | Actúa como un desarrollador senior en Python experto en Clean Architecture y seguridad.Necesito implementar enmascaramiento de datos (Data Masking) para los salarios de los empleados en la generación de informes (PDF y Excel) del proyecto EcoTech Solutions.Requisitos del script:1. Validar el rol del usuario autenticado (instancia de la clase Usuario / Gerente / Administrador).2. Si el usuario tiene rol de Gerente o Administrador, el reporte debe incluir el salario real formateado (ej. "$ 1,500,000").3. Si el usuario es un empleado o usuario estándar, el campo salario en el informe debe enmascararse reemplazando los dígitos por asteriscos (ej. "$ *******" o "[CONFIDENCIAL]").4. La lógica de enmascaramiento debe estar aislada en una función auxiliar dentro de la capa de seguridad o de formato (ej. seguridad/validaciones.py o en la capa de informes/informe.py).5. Dame el código listo para integrar en los módulos `informe_pdf.py` e `informe_excel.py`. | aceptada |
| 2026-09-21 12:37:50 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:38:15 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:42:07 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:42:31 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:43:23 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 12:48:02 | copilot | el correo debe quedar asi como el ejemplo j***z@ecotech.com utilizando las mismas credenciales de salario para informes generemos la seguridad en los correos. | aceptada |
| 2026-09-21 13:39:22 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 13:39:54 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 13:40:35 | gemini | Actúa como un desarrollador senior en Python.Necesito refactorizar el flujo de inicio de sesión (login) en mi aplicación de consola (EcoTech Solutions) para mejorar la UX y el control de intentos.Requisitos del flujo:1. Pedir el nombre de usuario una sola vez al inicio de la opción "1. Ingresar con usuario".2. Verificar si el usuario se encuentra temporalmente bloqueado antes de pedir la contraseña. Si está bloqueado, mostrar inmediatamente: "Usuario temporalmente bloqueado. Reintente en X segundos." y regresar al menú principal.3. Si el usuario no está bloqueado, permitir hasta 3 intentos ingresando ÚNICAMENTE la contraseña (sin volver a pedir el usuario).4. Si ingresa la contraseña correcta en cualquier intento, dar acceso al sistema.5. Si falla los 3 intentos: - Registrar la marca de tiempo (timestamp) del bloqueo en el usuario. - Mostrar el mensaje: "Acceso bloqueado: se superó el número de intentos permitidos." - Regresar inmediatamente al menú principal.6. Estructura el código usando un bucle `while` para los intentos de contraseña y manejo claro del tiempo de bloqueo (ejemplo: 20 o 30 segundos usando `datetime` o `time`). | aceptada |
| 2026-09-21 13:45:45 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 13:49:51 | copilot | en el menu principal de administrador y gerente deberia aparecer un menu de usuarios registrados y mostrar todos los usuarios que se han guardado y con la opcion de modificar eliminar o crear | aceptada |
| 2026-09-21 13:55:05 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 14:03:48 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 14:04:15 | GitHub Copilot | Prueba CLI automatizada | Aceptado |
| 2026-09-21 14:05:08 | visual | Actúa como un desarrollador senior en Python experto en seguridad y Clean Architecture.Necesito implementar la funcionalidad de "Cambio de contraseña obligatorio tras restablecimiento por Administrador" en EcoTech Solutions.Requisitos de implementación:1. Modelo y Base de Datos (`modelos/usuario.py` y `ecotech.db`): - Agregar el campo/atributo `debe_cambiar_clave` (booleano / entero 0 o 1) en la tabla `usuarios` y en la clase `Usuario`. - Cuando el Administrador cambia la contraseña a un usuario, fijar `debe_cambiar_clave = 1`.2. Repositorio (`repositorios/usuario_repository.py`): - Actualizar el método de cambio de contraseña para que acepte o actualice la marca `debe_cambiar_clave`. - Crear un método `actualizar_clave_usuario(id_usuario, nueva_clave_plana)` que guarde el nuevo hash y cambie `debe_cambiar_clave = 0`.3. Flujo en Menú Principal (`main.py`): - Al iniciar sesión exitosamente, verificar si `usuario.debe_cambiar_clave == 1` (o True). - Si es True, interceptar el acceso y solicitar: a) Contraseña actual/temporal (validar que coincida). b) Nueva contraseña. c) Repetir nueva contraseña (validar que ambas coincidan). - Si la validación es correcta, actualizar el hash en la base de datos, cambiar `debe_cambiar_clave = 0` y dar acceso al menú principal. - Si la clave actual es incorrecta o las nuevas no coinciden, dar hasta 3 intentos o cancelar la operación regresando al menú de login. | aceptada |

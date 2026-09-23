"""Clientes de APIs externas con validacion y manejo seguro de fallos."""

import json
import os
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode
from urllib.request import Request, urlopen

from seguridad import validaciones as v


class ErrorApiExterna(RuntimeError):
    """Fallo controlado al consultar un servicio externo."""


class ClienteApisExternas:
   URL_IP_GEO = os.getenv("ECOTECH_URL_IP_GEO", "http://ip-api.com/json")

   @classmethod
   def consultar_ubicacion_ip(cls, ip=""):
        """Obtiene el país, ciudad y proveedor de internet de una IP (para logs de seguridad)."""
        base_url = cls.URL_IP_GEO.rstrip("/")
        
        # Si hay IP especificada se concatena /IP, si no, se consulta el endpoint base /json
        endpoint = f"{base_url}/{ip.strip()}" if ip.strip() else base_url

        datos = cls._obtener_json(
            endpoint, 
            {"fields": "status,country,city,isp,query"}
        )

        if datos.get("status") != "success":
            raise ErrorApiExterna("No se pudo geolocalizar la dirección IP.")

        return {
            "ip": datos.get("query"),
            "pais": datos.get("country"),
            "ciudad": datos.get("city"),
            "proveedor": datos.get("isp"),
        }
     
    
   URL_GEOCODIFICACION = os.getenv(
        "ECOTECH_URL_GEOCODIFICACION",
        "https://geocoding-api.open-meteo.com/v1/search")
   URL_GEOCODIFICACION_INVERSA = os.getenv(
        "ECOTECH_URL_GEOCODIFICACION_INVERSA",
       "https://api.bigdatacloud.net/data/reverse-geocode-client")
   URL_PRONOSTICO = os.getenv(
        "ECOTECH_URL_PRONOSTICO",
        "https://api.open-meteo.com/v1/forecast")
   URL_TIPO_CAMBIO = os.getenv(
        "ECOTECH_URL_TIPO_CAMBIO",
        "https://open.er-api.com/v6/latest")
   TIMEOUT = int(os.getenv("ECOTECH_API_TIMEOUT", "8"))
   ESTADOS_TIEMPO = {
        0: "Despejado",
        1: "Mayormente despejado",
        2: "Parcialmente nublado",
        3: "Nublado",
        45: "Niebla",
        48: "Niebla con escarcha",
        51: "Llovizna ligera",
        53: "Llovizna moderada",
        55: "Llovizna intensa",
        56: "Llovizna helada ligera",
        57: "Llovizna helada intensa",
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        65: "Lluvia intensa",
        66: "Lluvia helada ligera",
        67: "Lluvia helada intensa",
        71: "Nieve ligera",
        73: "Nieve moderada",
        75: "Nieve intensa",
        77: "Granulos de nieve",
        80: "Chubascos ligeros",
        81: "Chubascos moderados",
        82: "Chubascos violentos",
        85: "Chubascos de nieve ligeros",
        86: "Chubascos de nieve intensos",
        95: "Tormenta",
        96: "Tormenta con granizo ligero",
        99: "Tormenta con granizo intenso",
    }

    # Las entradas que viajan a la API se validan con el mismo modulo
    # que usa el resto del sistema: un solo criterio, un solo lugar.

   @staticmethod
   def validar_ciudad(ciudad):
        return v.validar_nombre(ciudad, "La ciudad")

   @staticmethod
   def validar_pais(pais):
        return v.validar_nombre(pais, "El pais")

   @staticmethod
   def validar_moneda(moneda):
        return v.validar_codigo_moneda(moneda, "La moneda")

   @classmethod
   def describir_tiempo(cls, codigo):
        """Traduce el codigo WMO y marca lluvia o tormenta cuando corresponde."""
        estado = cls.ESTADOS_TIEMPO.get(codigo, "Estado del tiempo no informado")
        alerta = None
        if codigo in {95, 96, 99}:
            alerta = "Alerta: hay tormenta."
        elif isinstance(codigo, int) and 51 <= codigo <= 67:
            alerta = "Alerta: hay lluvia."
        elif isinstance(codigo, int) and 80 <= codigo <= 82:
            alerta = "Alerta: hay lluvia."
        return estado, alerta

   @classmethod
   def _mensaje_estado_http(cls, estado):
        if estado == 400:
            return "El servicio externo rechazo la solicitud."
        if estado in {401, 403}:
            return "El servicio externo no autoriza esta consulta."
        if estado == 404:
            return "El recurso solicitado no existe en el servicio externo."
        if estado == 429:
            return "El servicio externo recibio demasiadas consultas. Intente mas tarde."
        if 500 <= estado <= 599:
            return "El servicio externo no esta disponible en este momento."
        return "El servicio externo no pudo completar la consulta."

   @staticmethod
   def _normalizar_pais(pais):
        descompuesto = unicodedata.normalize("NFD", pais)
        sin_tildes = "".join(
            caracter for caracter in descompuesto
            if unicodedata.category(caracter) != "Mn")
        return sin_tildes.casefold()

   @classmethod
   def _obtener_json(cls, url, parametros):
        consulta = f"{url}?{urlencode(parametros)}"
        solicitud = Request(consulta, headers={"User-Agent": "EcoTech/1.0"})
        try:
            with urlopen(solicitud, timeout=cls.TIMEOUT) as respuesta:
                if respuesta.status != 200:
                    raise ErrorApiExterna(cls._mensaje_estado_http(respuesta.status))
                contenido = json.loads(respuesta.read().decode("utf-8"))
                if not isinstance(contenido, dict):
                    raise ErrorApiExterna(
                        "El servicio externo devolvio datos con formato invalido.")
                return contenido
        except HTTPError as error:
            raise ErrorApiExterna(cls._mensaje_estado_http(error.code)) from None
        except (URLError, TimeoutError, OSError):
            raise ErrorApiExterna(
                "No fue posible conectarse al servicio externo.") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ErrorApiExterna(
                "El servicio externo devolvio una respuesta invalida.") from None

   @classmethod
   def consultar_ubicacion_dispositivo(cls, latitud, longitud, precision=None):
        """Obtiene ubicacion legible a partir de coordenadas reales del dispositivo."""
        try:
            latitud = float(latitud)
            longitud = float(longitud)
        except (TypeError, ValueError):
            raise ErrorApiExterna("Las coordenadas del dispositivo no son validas.") from None

        if not -90 <= latitud <= 90:
            raise ErrorApiExterna("Las coordenadas del dispositivo no son validas.")
        if not -180 <= longitud <= 180:
            raise ErrorApiExterna("Las coordenadas del dispositivo no son validas.")

        respuesta = cls._obtener_json(
            cls.URL_GEOCODIFICACION_INVERSA,
            {"latitude": latitud, "longitude": longitud,
             "accept-language": "es", "addressdetails": 1, "format": "json"})
        resultados = respuesta.get("results") or []
        if resultados:
            lugar = resultados[0]
            ciudad = lugar.get("name") or lugar.get("city")
            region = lugar.get("admin1") or lugar.get("state")
            pais = lugar.get("country")
        else:
            direccion = respuesta.get("address") or {}
            ciudad = (direccion.get("city") or direccion.get("town")
                      or direccion.get("village") or direccion.get("municipality"))
            region = direccion.get("state") or direccion.get("region")
            pais = direccion.get("country")
            ciudad = ciudad or respuesta.get("locality")
            region = region or respuesta.get("principalSubdivision")
            pais = pais or respuesta.get("countryName")
        if not ciudad and not region and not pais:
            raise ErrorApiExterna("No se encontraron resultados para esas coordenadas.")

        return {
            "latitud": latitud,
            "longitud": longitud,
            "precision": precision,
            "ciudad": ciudad or "No disponible",
            "region": region or "No disponible",
            "pais": pais or "No disponible",
        }

   @classmethod
   def consultar_clima(cls, ciudad, pais):
        ciudad = cls.validar_ciudad(ciudad)
        pais = cls.validar_pais(pais)
        ubicacion = cls._obtener_json(
            cls.URL_GEOCODIFICACION,
            {"name": ciudad, "count": 1, "language": "es", "format": "json"})
        resultados = ubicacion.get("results", [])
        if not resultados:
            raise ErrorApiExterna("No se encontro la ciudad solicitada.")

        lugar = resultados[0]
        if (cls._normalizar_pais(lugar.get("country", ""))
            != cls._normalizar_pais(pais)):
            raise ErrorApiExterna("La ciudad no coincide con el pais indicado.")

        pronostico = cls._obtener_json(
            cls.URL_PRONOSTICO,
            {"latitude": lugar["latitude"], "longitude": lugar["longitude"],
             "current": "temperature_2m,relative_humidity_2m,weather_code",
             "timezone": "auto"})
        actual = pronostico.get("current")
        if not isinstance(actual, dict):
            raise ErrorApiExterna("El servicio de clima no entrego datos utilizables.")
        codigo_climatico = actual.get("weather_code")
        estado_tiempo, alerta = cls.describir_tiempo(codigo_climatico)
        return {
            "ciudad": lugar.get("name", ciudad),
            "pais": lugar.get("country", pais),
            "temperatura": actual.get("temperature_2m"),
            "humedad": actual.get("relative_humidity_2m"),
            "codigo_climatico": codigo_climatico,
            "estado_tiempo": estado_tiempo,
            "alerta": alerta,
            "hora": actual.get("time"),
            "zona_horaria": pronostico.get("timezone"),
        }

   @classmethod
   def consultar_tipo_cambio(cls, moneda_origen, moneda_destino):
        origen = cls.validar_moneda(moneda_origen)
        destino = cls.validar_moneda(moneda_destino)
        if origen == destino:
            return {"origen": origen, "destino": destino, "tipo_cambio": 1.0}

        respuesta = cls._obtener_json(
            f"{cls.URL_TIPO_CAMBIO.rstrip('/')}/{origen}", {})
        tasas = respuesta.get("rates")
        if not isinstance(tasas, dict):
            raise ErrorApiExterna(
                "El servicio de tipo de cambio devolvio tasas invalidas.")
        tasa = tasas.get(destino)
        if not isinstance(tasa, (int, float)):
            raise ErrorApiExterna("El servicio de tipo de cambio no entrego una tasa valida.")
        return {"origen": origen, "destino": destino, "tipo_cambio": tasa,
                "fecha": respuesta.get("date") or respuesta.get("time_last_update_utc")}

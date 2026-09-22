import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from servicios.api_externa import ClienteApisExternas, ErrorApiExterna


class RespuestaFalsa:
    def __init__(self, contenido, estado=200):
        self.status = estado
        self.contenido = contenido

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.contenido).encode("utf-8")


class TestClienteApisExternas(unittest.TestCase):
    def test_traduce_codigo_y_alerta_por_lluvia_o_tormenta(self):
        self.assertEqual(
            ClienteApisExternas.describir_tiempo(0),
            ("Despejado", None))
        self.assertEqual(
            ClienteApisExternas.describir_tiempo(63),
            ("Lluvia moderada", "Alerta: hay lluvia."))
        self.assertEqual(
            ClienteApisExternas.describir_tiempo(95),
            ("Tormenta", "Alerta: hay tormenta."))

    def test_estados_http_tienen_mensajes_seguros(self):
        casos = {
            400: "rechazo",
            401: "autoriza",
            403: "autoriza",
            404: "no existe",
            429: "demasiadas",
            500: "disponible",
            503: "disponible",
        }

        for estado, fragmento in casos.items():
            with self.subTest(estado=estado):
                error_http = HTTPError(
                    "https://interno.invalid", estado, "detalle interno", {}, None)
                try:
                    with patch(
                            "servicios.api_externa.urlopen",
                            side_effect=error_http):
                        with self.assertRaisesRegex(
                                ErrorApiExterna, fragmento) as contexto:
                            ClienteApisExternas._obtener_json(
                                "https://interno.invalid", {})
                finally:
                    error_http.close()

                self.assertNotIn("https://", str(contexto.exception))
                self.assertNotIn(str(estado), str(contexto.exception))

    def test_rechaza_json_que_no_es_un_objeto(self):
        with patch(
                "servicios.api_externa.urlopen",
                return_value=RespuestaFalsa(["no", "es", "objeto"])):
            with self.assertRaisesRegex(ErrorApiExterna, "formato invalido"):
                ClienteApisExternas._obtener_json("https://interno.invalid", {})

    def test_rechaza_rates_que_no_es_diccionario(self):
        with patch.object(
                ClienteApisExternas,
                "_obtener_json",
                return_value={"rates": ["invalido"]}):
            with self.assertRaisesRegex(ErrorApiExterna, "tasas invalidas"):
                ClienteApisExternas.consultar_tipo_cambio("USD", "CLP")

    def test_compara_pais_sin_distinguir_tildes(self):
        ubicacion = {
            "results": [{
                "name": "Lima",
                "country": "Per\u00fa",
                "latitude": -12.0,
                "longitude": -77.0,
            }]
        }
        pronostico = {
            "current": {
                "temperature_2m": 20,
                "relative_humidity_2m": 70,
                "weather_code": 1,
                "time": "2026-09-20T12:00",
            },
            "timezone": "America/Lima",
        }
        with patch.object(
                ClienteApisExternas,
                "_obtener_json",
                side_effect=[ubicacion, pronostico]):
            resultado = ClienteApisExternas.consultar_clima("Lima", "Peru")

        self.assertEqual(resultado["pais"], "Per\u00fa")


if __name__ == "__main__":
    unittest.main()

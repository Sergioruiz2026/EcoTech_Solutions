import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from main import consultar_servicios_externos, menu_principal
from modelos.usuario import Usuario
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

    def test_operador_tiene_permiso_de_consultas_externas(self):
        usuario = Usuario("operador1", "ClaveSegura1", "operador")
        self.assertTrue(usuario.tiene_permiso("consultar_externos"))

    def test_menu_muestra_consultas_externas_para_operador(self):
        usuario = Usuario("operador1", "ClaveSegura1", "operador")
        with patch("main.leer_opcion", return_value=0), \
                patch("sys.stdout") as stdout:
            respuesta = menu_principal(
                usuario, None, None, None, None, None, None, None)

        self.assertEqual(respuesta, "salir")
        salida = "\n".join(call.args[0] for call in stdout.write.call_args_list)
        self.assertIn("Consultas externas", salida)

    def test_submenu_consultas_externas_vuelve_al_menu_despues_de_historial(self):
        usuario = Usuario("operador1", "ClaveSegura1", "operador")
        repo_consultas = object()

        with patch("main.leer_opcion", side_effect=[2, 0]), \
                patch("main.mostrar_historial_consultas") as mostrar_historial, \
                patch("sys.stdout"):
            consultar_servicios_externos(usuario, None, repo_consultas)

        self.assertEqual(mostrar_historial.call_count, 1)
        mostrar_historial.assert_called_once_with(repo_consultas)

    def test_consultas_externas_muestra_ubicacion_detectada(self):
        usuario = Usuario("operador1", "ClaveSegura1", "operador")

        class RepoConsultasFake:
            def crear(self, *args, **kwargs):
                return None

        repo_consultas = RepoConsultasFake()

        with patch("main.ClienteApisExternas.consultar_ubicacion_ip",
                   return_value={"ciudad": "Santiago", "pais": "Chile"}), \
                patch("main.leer_opcion", side_effect=[1, 0]), \
                patch("main.pedir", side_effect=["Santiago", "Chile", "USD", "CLP"]) as pedir_mock, \
                patch("main.ClienteApisExternas.consultar_clima",
                      return_value={
                          "temperatura": 23.9,
                          "humedad": 51,
                          "estado_tiempo": "Despejado",
                          "codigo_climatico": 0,
                          "alerta": None,
                      }), \
                patch("main.ClienteApisExternas.consultar_tipo_cambio",
                      return_value={"origen": "USD", "destino": "CLP", "tipo_cambio": 959.45}), \
                patch("sys.stdout") as stdout:
            consultar_servicios_externos(usuario, None, repo_consultas)

        salida = "\n".join(call.args[0] for call in stdout.write.call_args_list)
        self.assertIn("Ubicacion detectada: Santiago, Chile", salida)
        self.assertEqual(pedir_mock.call_args_list[0].args[2], "Santiago")
        self.assertEqual(pedir_mock.call_args_list[1].args[2], "Chile")


if __name__ == "__main__":
    unittest.main()

"""Persistencia local de respuestas relevantes de APIs externas."""

import json

from repositorios.repositorio_base import RepositorioBase


class RepositorioConsultaApi(RepositorioBase):

    def crear(self, usuario, tipo_consulta, parametros, respuesta):
        cursor = self._escribir(
            "INSERT INTO consultas_api "
            "(nombre_usuario, tipo_consulta, parametros_json, respuesta_json) "
            "VALUES (?, ?, ?, ?)",
            (usuario, tipo_consulta, json.dumps(parametros, ensure_ascii=False),
             json.dumps(respuesta, ensure_ascii=False)),
            error="No se pudo guardar la consulta externa.")
        return cursor.lastrowid

    def listar(self, limite=20):
        if not isinstance(limite, int) or limite < 1 or limite > 100:
            raise ValueError("El limite debe estar entre 1 y 100.")
        return self._leer_todos(
            "SELECT nombre_usuario, tipo_consulta, parametros_json, "
            "respuesta_json, fecha_consulta FROM consultas_api "
            "ORDER BY id DESC LIMIT ?", (limite,))

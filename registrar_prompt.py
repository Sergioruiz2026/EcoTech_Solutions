"""Registra un prompt de IA en USO_DE_IA.md."""

import argparse
from pathlib import Path

from seguridad.auditoria import registrar_prompt, RUTA_USO_IA


def _leer_entrada_o_default(mensaje, valor_predeterminado):
    valor = input(mensaje).strip()
    return valor if valor else valor_predeterminado


def main():
    parser = argparse.ArgumentParser(
        description="Registra un prompt de IA en USO_DE_IA.md."
    )
    parser.add_argument("--fase", help="Fase o contexto del uso de IA")
    parser.add_argument("--prompt", help="Texto del prompt a registrar")
    parser.add_argument("--respuesta", help="Respuesta de la IA")
    parser.add_argument(
        "--decision",
        help="Alias compatible para la respuesta.",
        default=None,
    )
    parser.add_argument(
        "--herramienta",
        help="Herramienta de IA utilizada",
        default="No especificada",
    )
    parser.add_argument(
        "--archivo",
        help="Ruta del archivo de uso de IA donde se registrará el prompt.",
        default=str(RUTA_USO_IA),
    )
    args = parser.parse_args()

    if not any([args.fase, args.prompt, args.respuesta, args.decision,
                args.herramienta != "No especificada",
                args.archivo != str(RUTA_USO_IA)]):
        print("=" * 60)
        print("        REGISTRO DE USO DE IA - ECOTECH")
        print("=" * 60)
        print()

        fase = _leer_entrada_o_default("Fase del proceso:\n> ", "No especificada")
        prompt = _leer_entrada_o_default("Prompt utilizado:\n> ", "")
        if not prompt:
            print("\nError: debes ingresar un prompt.")
            return

        respuesta = _leer_entrada_o_default("Respuesta de la IA:\n> ", "Pendiente")
        herramienta = _leer_entrada_o_default(
            "\nHerramienta de IA [Visual Studio / Copilot / Gemini]:\n> ",
            "No especificada",
        )

        registrar_prompt(
            prompt,
            herramienta,
            respuesta,
            fase=fase,
            ruta_archivo=Path(args.archivo),
        )
        print(f"\n[OK] Prompt registrado correctamente en {args.archivo}.")
        return

    print("=" * 60)
    print("        REGISTRO DE USO DE IA - ECOTECH")
    print("=" * 60)
    print()

    fase = args.fase or "No especificada"
    prompt = args.prompt
    respuesta = args.respuesta or args.decision or "Pendiente"
    herramienta = args.herramienta

    if prompt is None:
        prompt = _leer_entrada_o_default("Prompt utilizado:\n> ", "")

    if not prompt:
        print("\nError: debes ingresar un prompt.")
        return

    if args.herramienta == "No especificada":
        herramienta = _leer_entrada_o_default(
            "\nHerramienta de IA [Visual Studio / Copilot / Gemini]:\n> ",
            "No especificada",
        )

    if respuesta == "Pendiente" and args.respuesta is None and args.decision is None:
        respuesta = _leer_entrada_o_default(
            "\nRespuesta de la IA:\n> ",
            "Pendiente",
        )

    registrar_prompt(
        prompt,
        herramienta,
        respuesta,
        fase=fase,
        ruta_archivo=Path(args.archivo),
    )

    print(f"\n[OK] Prompt registrado correctamente en {args.archivo}.")


if __name__ == "__main__":
    main()
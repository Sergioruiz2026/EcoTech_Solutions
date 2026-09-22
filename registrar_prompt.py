"""Registra un prompt de IA en USO_DE_IA.md."""

import argparse

from seguridad.auditoria import registrar_prompt


def _leer_entrada_o_default(mensaje, valor_predeterminado):
    valor = input(mensaje).strip()
    return valor if valor else valor_predeterminado


def main():
    parser = argparse.ArgumentParser(
        description="Registra un prompt de IA en USO_DE_IA.md."
    )
    parser.add_argument("--prompt", help="Texto del prompt a registrar")
    parser.add_argument(
        "--herramienta",
        help="Herramienta de IA utilizada",
        default="No especificada",
    )
    parser.add_argument(
        "--decision",
        help="Decisión tomada sobre la respuesta",
        default="Pendiente",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("        REGISTRO DE USO DE IA - ECOTECH")
    print("=" * 60)
    print()

    prompt = args.prompt
    herramienta = args.herramienta
    decision = args.decision

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

    if args.decision == "Pendiente":
        decision = _leer_entrada_o_default(
            "\nDecisión tomada sobre la respuesta:\n> ",
            "Pendiente",
        )

    registrar_prompt(prompt, herramienta, decision)

    print("\n[OK] Prompt registrado correctamente en USO_DE_IA.md.")


if __name__ == "__main__":
    main()
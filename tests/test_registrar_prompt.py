import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_registrar_prompt_acepta_argumentos_cli():
    proceso = subprocess.run(
        [
            sys.executable,
            str(ROOT / "registrar_prompt.py"),
            "--prompt",
            "Prueba CLI automatizada",
            "--herramienta",
            "GitHub Copilot",
            "--decision",
            "Aceptado",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )

    assert proceso.returncode == 0, proceso.stderr
    assert "registrado correctamente" in proceso.stdout.lower()

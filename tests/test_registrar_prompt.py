import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestRegistrarPrompt(unittest.TestCase):
    def setUp(self):
        self.archivo_temp = ROOT / "test_USO_DE_IA_temp.md"
        if self.archivo_temp.exists():
            self.archivo_temp.unlink()
        self.archivo_temp.write_text("", encoding="utf-8")

    def tearDown(self):
        if self.archivo_temp.exists():
            self.archivo_temp.unlink()

    def test_registrar_prompt_acepta_argumentos_cli(self):
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
                "--archivo",
                str(self.archivo_temp),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )

        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        self.assertIn("registrado correctamente", proceso.stdout.lower())

        contenido = self.archivo_temp.read_text(encoding="utf-8")
        self.assertIn("Prueba CLI automatizada", contenido)
        self.assertIn("GitHub Copilot", contenido)
        self.assertIn("Aceptado", contenido)


if __name__ == '__main__':
    unittest.main()

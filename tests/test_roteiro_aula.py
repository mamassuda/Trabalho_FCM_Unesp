import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RoteiroAulaTests(unittest.TestCase):
    def test_roteiro_executa_e_exporta_csv_e_quatro_graficos(self):
        script = ROOT / 'Scripts/atividade_aula_futebol.py'
        self.assertTrue(script.exists(), 'Roteiro da aula ainda não implementado.')
        pasta_temporaria = ROOT / 'previa_backup'
        pasta_temporaria.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=pasta_temporaria) as pasta:
            result = subprocess.run([sys.executable, str(script), '--ano', '2025', '--saida', pasta],
                                    cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            arquivos = list(Path(pasta).iterdir())
            self.assertEqual(len([p for p in arquivos if p.suffix == '.png']), 4)
            self.assertTrue((Path(pasta) / 'analise_2025_futebol.csv').exists())
            self.assertIn('20 clubes', result.stdout)
            self.assertTrue(all(p.stat().st_size > 1000 for p in arquivos))


if __name__ == '__main__':
    unittest.main()

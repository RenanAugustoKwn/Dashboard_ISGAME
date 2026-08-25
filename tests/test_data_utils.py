import unittest

import pandas as pd

from data_utils import preparar_dados, resumo_tcle


class PrepararDadosTests(unittest.TestCase):
    def test_converte_formatos_do_csv_de_referencia(self):
        df = pd.DataFrame(
            {"respostasDemografico.dataNascimento": ["03/06/1964", "1 janeiro - 1937", "08121941", "08/21/2000", "4119r45"]}
        )
        resultado = preparar_dados(df, pd.Timestamp("2026-08-25"))
        self.assertEqual(resultado["Idade"].iloc[:4].tolist(), [62, 89, 84, 26])
        self.assertTrue(pd.isna(resultado["Idade"].iloc[4]))

    def test_fallback_para_ano_e_tcle_booleano(self):
        df = pd.DataFrame({"respostasDemografico.anoNascimento": [1950, None], "participanteTCLE": [1.0, False]})
        resultado = preparar_dados(df, pd.Timestamp("2026-08-25"))
        self.assertEqual(resultado["Idade"].iloc[0], 76)
        self.assertEqual(resumo_tcle(resultado), (1, 2))

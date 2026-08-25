import unittest

import pandas as pd

from data_utils import preparar_dados, resumo_tcle


class PrepararDadosTests(unittest.TestCase):
    REFERENCIA = pd.Timestamp("2026-08-24")

    def test_converte_formatos_reais_da_planilha_ic2025(self):
        df = pd.DataFrame(
            {
                "respostasDemografico.dataNascimento": [
                    "03/06/1964",
                    "1 janeiro - 1937",
                    "23 de abril de 1951",
                    "08121941",
                    "15/10/53",
                    "04 021942",
                    "08/21/2000",
                    "4119r45",
                ]
            }
        )
        resultado = preparar_dados(df, self.REFERENCIA)

        self.assertEqual(resultado["Idade"].iloc[:7].tolist(), [62, 89, 75, 84, 72, 84, 26])
        self.assertTrue(pd.isna(resultado["Idade"].iloc[7]))
        self.assertEqual(
            resultado["Faixa etária"].tolist(),
            ["60-69", "80+", "70-79", "80+", "70-79", "80+", "<50", "Não informado"],
        )

    def test_usa_ano_quando_a_data_nao_existe_na_linha(self):
        df = pd.DataFrame(
            {
                "respostasDemografico.dataNascimento": ["03/06/1964", None],
                "respostasDemografico.anoNascimento": [1960, "1950"],
            }
        )
        resultado = preparar_dados(df, self.REFERENCIA)

        self.assertEqual(resultado["Idade"].tolist(), [62, 76])
        self.assertEqual(
            resultado["Origem da idade"].tolist(),
            ["Data de nascimento", "Ano de nascimento"],
        )

    def test_reconhece_booleanos_e_numeros_do_tcle(self):
        df = pd.DataFrame({"participanteTCLE": [True, 1.0, False, 0.0, None]})
        self.assertEqual(resumo_tcle(df), (2, 4))

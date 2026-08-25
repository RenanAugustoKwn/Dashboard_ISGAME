# Dashboard ISGAME

Dashboard Streamlit que consolida os arquivos `dados/*/resultado_final.xlsx`.

## Executar

```powershell
streamlit run app.py
```

Os indicadores usam apenas respostas preenchidas como denominador. A idade é calculada pela data de nascimento; na ausência dela, usa o ano de nascimento como estimativa. A tabela do dashboard omite identificadores e respostas individuais de saúde.

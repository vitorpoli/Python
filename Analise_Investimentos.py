import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
import time
import requests
import datetime
import yfinance as yf
from io import StringIO
from IPython.display import display
import matplotlib.pyplot as plt
import plotly.express as px

# Colocar os dados
n = int(input("Em quantos ativos você tem valor investidor? "))

ativo = []
data_inicio = []
quant = []
cotacao_inicial = []
valor_invest = []

# Criar tabela com valores inseridos

for i in range(n):
    adativo, adcotacao, addata_inicio, adquant = input(
        "Qual o ticker da empresa, cotação inicial, data do investimento (formato DD-MM-AAAA) e quantidade de ações compradas, separados por espaço: ").split()
    adcotacao, adquant = float(adcotacao), int(adquant)
    ativo.append(adativo)
    cotacao_inicial.append(adcotacao)
    data_inicio.append(addata_inicio)
    quant.append(adquant)
    advalor_invest = adquant * adcotacao
    valor_invest.append(advalor_invest)

carteira = pd.DataFrame({"ATIVO": ativo, "VALOR INVESTIDO": valor_invest, "QUANTIDADE": quant,
                        "Cotação Inicial": cotacao_inicial, "DATA APLICAÇÃO": data_inicio})

# Função para obter dados do CDI e IPCA
def get_data(url, data_inicial, tipo):
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        total = sum(float(item['valor']) for item in data)
        return total
    else:
        print(
            f"Falha ao obter dados do {tipo} para {data_inicial}. Código de status: {response.status_code}")
        return None
    

# CDI, IPCA e Ibovespa

data_atual = datetime.datetime.now().date()
# Convertendo a data para o formato desejado
data_final = data_atual.strftime('%d/%m/%Y')

for data_inicial in data_inicio:
    data_inicial_cdi = data_inicial
    data_inicial_ipca = data_inicial
    url_cdi = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados?formato=json&dataInicial={data_inicial_cdi}&dataFinal={data_final}"
    url_ipca = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial={data_inicial_ipca}&dataFinal={data_final}"

    total_cdi = get_data(url_cdi, data_inicial, "CDI")
    total_ipca = get_data(url_ipca, data_inicial, "IPCA")

    # Redirecionar a saída padrão para o buffer para não printar o download
    import sys
    original_stdout = sys.stdout
    sys.stdout = StringIO()

    data_inicio_formatada = datetime.datetime.strptime(
        data_inicial, "%d/%m/%Y").strftime('%Y-%m-%d')
    data_fim_ibovespa = datetime.datetime.now().strftime('%Y-%m-%d')
    ibovespa_data = yf.download(
        '^BVSP', start=data_inicio_formatada)
    ibovespa_data['retorno_diario'] = ibovespa_data['Close'].pct_change()
    rentabilidade_periodo_ibovespa = ibovespa_data['retorno_diario'].sum()

    # Restaurar a saída padrão
    sys.stdout = original_stdout

# comparativo com os índices
for i, acao in enumerate(ativo):
    data_inicial_cdi = data_inicio[i]
    data_inicial_ipca = data_inicio[i]
    data_inicial_ibovespa = datetime.datetime.strptime(
        data_inicio[i], "%d/%m/%Y").strftime('%Y-%m-%d')
    
# api acoes
chave_api = 'IS897KGXF4HY1MAS'

tickers = ativo
ts = TimeSeries(key=chave_api, output_format='pandas')
tabela_acoes = {acao: data for acao in tickers for data,_ in [ts.get_daily(f"{acao}.SAO", outputsize='full')]}
time.sleep(14)  

# Criando listas para armazenar as informações
cotacao_inicial_lista = []
cotacao_atual_lista = []
rentabilidade_lista = []
rentabilidade_cdi_lista = []
rentabilidade_relativa_ibov_lista = []
rentabilidade_esperada_lista = []

# Função para calcular rentabilidade e volatilidade
for acao, data in tabela_acoes.items():
    if acao in ativo:  
        idx = ativo.index(acao)  
        if idx < len(data_inicio):  
            last_closing_price = data['4. close'].iloc[0]
            historical_data = data.loc[(data.index >= min(data_inicio))]
            log_returns = np.log(
                historical_data['4. close'] / historical_data['4. close'].shift(1))
            volatilidade = log_returns.std() * np.sqrt(252)
            cotacao_atual = last_closing_price
            cotacao_inicial_ativo = cotacao_inicial[idx]
            rentabilidade = ((cotacao_atual - cotacao_inicial_ativo) / cotacao_inicial_ativo) * 100
            cotacao_inicial_lista.append(cotacao_inicial_ativo)
            cotacao_atual_lista.append(last_closing_price)
            rentabilidade_lista.append(rentabilidade)

            # Rentabilidade relativa ao CDI
            if total_cdi != 0:  
                rentabilidade_cdi = (rentabilidade / total_cdi) * 100
                rentabilidade_cdi_lista.append(rentabilidade_cdi)

            # Rentabilidade relativa ao IPCA
            if total_ipca != 0:  
                rentabilidade_ipca = (rentabilidade / total_ipca) * 100

            # Rentabilidade relativa ao Ibovespa
            rentabilidade_ibovespa = ibovespa_data['retorno_diario'].sum() * 100
            if rentabilidade_ibovespa != 0:  
                rentabilidade_relativa_ibov = (rentabilidade / rentabilidade_ibovespa) * 100
                rentabilidade_relativa_ibov_lista.append(rentabilidade_relativa_ibov)

        else:
            print(f"Índice fora do limite para {acao}")
    else:
        print(f"{acao} não encontrado na lista 'ativo'")

# Tabela com resultados obtidos
tabela_resultados = pd.DataFrame({"ATIVO": ativo, "Cotação Inicial": cotacao_inicial_lista,
                                 "Cotação Atual": cotacao_atual_lista, "Rentabilidade (%)": rentabilidade_lista,
                                 "Rentabilidade CDI (%)": rentabilidade_cdi_lista,
                                 "Rentabilidade Relativa IBOV (%)": rentabilidade_relativa_ibov_lista})
# Tabela formatada
format_dict = {'Cotação Inicial': '{:.2f}', 'Cotação Atual': '{:.2f}', 'Rentabilidade (%)': '{:.2f}','Valor Investido': '{:.2f}', 'Volatilidade': '{:.2f}', 'Rentabilidade CDI (%)': '{:.2f}', 'Rentabilidade Relativa IBOV (%)': '{:.2f}'}
tabela_resultados = tabela_resultados.style.format(format_dict)

tabela_resultados_data = tabela_resultados.data
print(tabela_resultados_data)


#Gráfico de barras
plt.figure(figsize=(10, 6))
plt.bar(tabela_resultados_data['ATIVO'], tabela_resultados_data['Rentabilidade (%)'], color='skyblue')
plt.xlabel('Ativo')
plt.ylabel('Rentabilidade (%)')
plt.title('Rentabilidade dos Ativos')
plt.show()

# Gráfico de barras interativo
fig = px.bar(tabela_resultados_data, x='ATIVO', y='Rentabilidade (%)', title='Rentabilidade dos Ativos')
fig.show()


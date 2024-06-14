import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import flask

engine = create_engine('postgresql://postgres:63764121@localhost:5432/EpiVis')

def fetch_data():
    query = "SELECT nu_ano, sg_uf, nu_idade_n, cs_sexo, municipio, evolucao, dt_obito FROM dengbr24 WHERE municipio = '431020'"
    df = pd.read_sql(query, engine)
    return df

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server)
app.title = "Dashboard de Doenças Endêmicas em Ijuí"

app.layout = html.Div(className="container", children=[
    html.Div(className="dashboard-header", children=[
        html.H1("EpiVis - Dashboard de Doenças Endêmicas em Ijuí")
    ]),

    html.Div(className="dashboard-content", children=[
        html.Div(className="dropdown-container", children=[
            dcc.Dropdown(
                id='disease-dropdown',
                options=[
                    {'label': 'Evolução', 'value': 'evolucao'},
                    {'label': 'Óbitos', 'value': 'dt_obito'},
                    {'label': 'Sexo', 'value': 'cs_sexo'},
                    {'label': 'Município', 'value': 'municipio'}
                ],
                value='evolucao',
                className='dcc-dropdown'
            )
        ]),
        dcc.Graph(id='line-chart')
    ])
])

@app.callback(
    Output('line-chart', 'figure'),
    [Input('disease-dropdown', 'value')]
)
def update_chart(selected_column):
    df = fetch_data()

    evolucao_mapping = {
        1: 'Cura',
        2: 'Óbito por dengue',
        3: 'Óbito por outras causas',
        4: 'Óbito em investigação',
        9: 'Ignorado'
    }

    if selected_column == 'evolucao':
        df['evolucao'] = df['evolucao'].replace(' ', pd.NA).dropna().astype(int)
        df['evolucao'] = df['evolucao'].map(evolucao_mapping)  

        missing_values = df['evolucao'].isnull().sum()
        if missing_values > 0:
            print(f"Atenção: Existem {missing_values} valores não mapeados na coluna 'evolucao'.")

        df_grouped = df.groupby(['nu_ano', 'evolucao']).size().reset_index(name='count')
        fig = px.bar(df_grouped, x='nu_ano', y='count', color='evolucao', title='Evolução dos casos ao longo dos anos')
        fig.update_layout(xaxis_title="Ano", yaxis_title="Contagem")
    elif selected_column == 'dt_obito':
        df['dt_obito'] = pd.to_datetime(df['dt_obito'], errors='coerce')
        df['obito_ano'] = df['dt_obito'].dt.year
        df_grouped = df.groupby(['obito_ano']).size().reset_index(name='count')
        fig = px.pie(df_grouped, values='count', names='obito_ano', title='Distribuição de Óbitos por Ano')
    elif selected_column == 'cs_sexo':
        df_grouped = df.groupby(['cs_sexo']).size().reset_index(name='count')
        fig = px.pie(df_grouped, values='count', names='cs_sexo', title='Distribuição de Casos por Sexo')
    elif selected_column == 'municipio':
        df_grouped = df.groupby(['municipio']).size().reset_index(name='count')
        fig = px.bar(df_grouped, x='municipio', y='count', title='Casos em Ijuí')
        fig.update_layout(xaxis_title = "Município de Ijuí", yaxis_title="Contagem")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

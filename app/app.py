import dash_bootstrap_components as dbc
from dash_extensions.enrich import Input, Output, State, html, dcc, dash_table
from dash_extensions.enrich import DashProxy, MultiplexerTransform, LogTransform, NoOutputTransform
import dash
from rich import print
import requests as r
import logging
import sys
import os
from datetime import datetime, timedelta
import locale
import json
import time

# Init logging
logging.basicConfig(
    format='[%(asctime)s] [%(name)s:%(lineno)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %z',
    stream=sys.stdout,
    level=10
)

log = logging.getLogger("PIL")
log.setLevel(logging.INFO)

log = logging.getLogger("urllib3.connectionpool")
log.setLevel(logging.INFO)

log = logging.getLogger("app")
log.setLevel(logging.INFO)

# Set the locale to Spanish (Spain)
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

MATCH_TAGS = [
    'Alemania-Escocia',
    'Hungría-Suiza',
    'España-Croacia',
    'Italia-Albania',
    'Eslovenia-Dinamarca',
    'Serbia-Inglaterra',
    'Polonia-Países Bajos',
    'Austria-Francia',
    'Rumanía-Ucrania',
    'Bélgica-Eslovaquia',
    'Turquía-Georgia',
    'Portugal-República Checa',
    'Alemania-Hungría',
    'Escocia-Suiza',
    'Croacia-Albania',
    'España-Italia',
    'Eslovenia-Serbia',
    'Dinamarca-Inglaterra',
    'Polonia-Austria',
    'Países Bajos-Francia',
    'Eslovaquia-Ucrania',
    'Bélgica-Rumanía',
    'Georgia-República Checa',
    'Turquía-Portugal',
    'Suiza-Alemania',
    'Escocia-Hungría',
    'Albania-España',
    'Croacia-Italia',
    'Inglaterra-Eslovenia',
    'Dinamarca-Serbia',
    'Países Bajos-Austria',
    'Francia-Polonia',
    'Eslovaquia-Rumanía',
    'Ucrania-Bélgica',
    'Georgia-Portugal',
    'República Checa-Turquía'
]

TEAMS_EN_ES = {
    'Albania': 'Albania',
    'Austria': 'Austria',
    'Belgium': 'Bélgica',
    'Croatia': 'Croacia',
    'Czech Republic': 'República Checa',
    'Denmark': 'Dinamarca',
    'England': 'Inglaterra',
    'France': 'Francia',
    'Georgia': 'Georgia',
    'Germany': 'Alemania',
    'Hungary': 'Hungría',
    'Italy': 'Italia',
    'Netherlands': 'Países Bajos',
    'Poland': 'Polonia',
    'Portugal': 'Portugal',
    'Romania': 'Rumanía',
    'Scotland': 'Escocia',
    'Serbia': 'Serbia',
    'Slovakia': 'Eslovaquia',
    'Slovenia': 'Eslovenia',
    'Spain': 'España',
    'Switzerland': 'Suiza',
    'Turkey': 'Turquía',
    'Ukraine': 'Ucrania'
}

TEAMS_ES_EN = {v: k for k, v in TEAMS_EN_ES.items()}

# LOAD PREDICTIONS
BASE_DIR = 'app/assets/predictions/'

files = os.listdir(BASE_DIR)
files.sort()

PREDICTIONS = {}

for file in files:
    clean_preds = []
    with open(BASE_DIR + file, 'r') as f:
        preds = f.readlines()
        for pred in preds:
            clean_pred = pred.strip()
            if clean_pred != '':
                clean_preds.append(clean_pred)
    PREDICTIONS[file] = clean_preds

COLUMNS = [
    {
        "name": 'Date',
        "id": 'date'
    },
    {
        "name": 'Home vs Away',
        "id": 'match',
        "presentation": "markdown"
    },
    {
        "name": 'Result',
        "id": 'result',
    },
    *[
        {
            "name": name.split('.')[0].title(),
            "id": name,
        }
        for name in files
    ]
]

TABLE_STYLE_CELL_CONDITIONAL = [
    {'if': {'column_id': 'date'}, 'width': '5vw', 'white-space': 'normal'},
    {'if': {'column_id': 'match'}, 'width': '15vw'},
    {'if': {'column_id': 'result'}, 'width': '5vw'},
    *[
        {'if': {'column_id': name}, 'width': '30vw', }
        for name in files
    ]
]

CLASSIFICATION_COLUMNS = [
    {
        "name": 'Pos.',
        "id": 'position'
    },
    {
        "name": 'Nombre participante',
        "id": 'nombre'
    },
    {
        "name": 'Total ptos',
        "id": 'total',
    },
    {
        "name": 'Res. exacto (10 ptos)',
        "id": 'res_exacto'
    },
    {
        "name": 'Res. partido (5 ptos)',
        "id": 'res_partido',
    },
    {
        "name": 'Eq. octavos (6 ptos)',
        "id": 'octavos',
    },
    {
        "name": 'Eq. cuartos (12 ptos)',
        "id": 'cuartos',
    },
    {
        "name": 'Eq. semis (24 ptos)',
        "id": 'semis',
    },
    {
        "name": 'Eq. final (48 ptos)',
        "id": 'final',
    },
    {
        "name": 'Eq. campeón (50 ptos)',
        "id": 'campeon',
    }
]

CLASSIFICATION_TABLE_STYLE_CELL_CONDITIONAL = [
    {'if': {'column_id': 'position'}, 'width': '1%'},
    {'if': {'column_id': 'nombre'}, 'width': '20%'},
    {'if': {'column_id': 'total'}, 'width': '10%'},
    {'if': {'column_id': 'res_exacto'}, 'width': '10%'},
    {'if': {'column_id': 'res_partido'}, 'width': '10%'},
    {'if': {'column_id': 'octavos'}, 'width': '10%'},
    {'if': {'column_id': 'cuartos'}, 'width': '10%'},
    {'if': {'column_id': 'semis'}, 'width': '10%'},
    {'if': {'column_id': 'final'}, 'width': '10%'},
    {'if': {'column_id': 'campeon'}, 'width': '10%'},
]


app = DashProxy(
    __name__,
    title="Euro 2024 league",
    transforms=[
        MultiplexerTransform(),
        NoOutputTransform(),
        LogTransform()
    ],
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)
app.config.suppress_callback_exceptions = True
server = app.server

app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.H1(["Euro 2024 league"]),
                    width="auto"
                ),
            ],
            justify="center",
            align="center",
            style={
                'margin-top': '15px',
            }
        ),
        # dbc.Row(
        #     [
        #         dbc.Col(
        #             [
        #                 dbc.Checklist(
        #                     options=[
        #                         {"label": "Mostrar fase de Grupos", "value": 1}
        #                     ],
        #                     value=[],
        #                     id="groups-input",
        #                     switch=True
        #                 ),
        #             ],
        #             width="auto"
        #         ),
        #     ],
        #     justify="center",
        #     align="center",
        # ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(
                            id="loading-table",
                            type="default",
                            children=[
                                dash_table.DataTable(
                                    id='matchs-table',
                                    columns=COLUMNS,
                                    page_size=200,
                                    page_action='native',
                                    sort_action='native',
                                    filter_action='native',
                                    filter_options={'case': 'insensitive'},
                                    fixed_rows={'headers': True, 'data': 0},
                                    style_as_list_view=True,
                                    style_cell_conditional=TABLE_STYLE_CELL_CONDITIONAL,
                                    style_data_conditional=[
                                        {
                                            "if": {"state": "selected"},
                                            "backgroundColor": "none",
                                            "border": "1px solid rgb(211, 211, 211)",
                                        }
                                    ],
                                    style_data={
                                        'whiteSpace': 'nowrap',
                                        'height': 'auto',
                                        'padding': '10px',
                                        'text-align': 'center',
                                        'overflow-x': 'auto',
                                    },
                                    style_header={
                                        'font-weight': 'bold',
                                        'text-align': 'center',
                                        "backgroundColor": "#e1e1e142",
                                        'padding': '10px',
                                        'height': '50px'
                                    },
                                    style_cell={
                                        'font-family': 'sans-serif'
                                    },
                                    style_filter={
                                        "backgroundColor": "#e1e1e142",
                                        'text-align': 'center',
                                        'height': '30px',
                                        "color": "black"
                                    }
                                ),
                            ]
                        ),
                    ],
                    width='auto',
                    style={
                        'margin-bottom': '50px',
                    }
                ),
                dbc.Col(
                    [
                        dcc.Loading(
                            id="loading-class-table",
                            type="default",
                            children=[
                                dash_table.DataTable(
                                    id='classification-table',
                                    columns=CLASSIFICATION_COLUMNS,
                                    page_size=200,
                                    page_action='native',
                                    sort_action='native',
                                    filter_action='native',
                                    filter_options={'case': 'insensitive'},
                                    style_as_list_view=True,
                                    style_cell_conditional=CLASSIFICATION_TABLE_STYLE_CELL_CONDITIONAL,
                                    style_data_conditional=[
                                        {
                                            "if": {"state": "selected"},
                                            "backgroundColor": "none",
                                            "border": "1px solid rgb(211, 211, 211)",
                                        }
                                    ],
                                    style_data={
                                        'whiteSpace': 'nowrap',
                                        'height': 'auto',
                                        'padding': '10px',
                                        'text-align': 'center',
                                        'overflow-x': 'auto',
                                    },
                                    style_header={
                                        'font-weight': 'bold',
                                        'text-align': 'center',
                                        "backgroundColor": "#e1e1e142",
                                        'padding': '10px',
                                        'height': '50px'
                                    },
                                    style_cell={
                                        'font-family': 'sans-serif'
                                    },
                                    style_filter={
                                        "backgroundColor": "#e1e1e142",
                                        'text-align': 'center',
                                        'height': '30px',
                                        "color": "black"
                                    }
                                ),
                            ]
                        ),
                    ],
                    width='auto',
                    style={
                        'margin-bottom': '50px',
                    }
                ),
            ],
            justify="center",
            align="center",
            style={
                'margin-top': '7px',
            }
        ),
        html.P(
            id='placeholder',
            style={
                'display': 'none'
            }
        )
    ],
    style={
        'width': '100vw',
        'margin': 'auto',
        'height': '100vh',
        'display': 'flex',
        'flex-direction': 'column'
    }
)


def get_res_symbol(result):
    res_symbol = '1'
    if result[0] < result[1]:
        res_symbol = '2'
    elif result[0] == result[1]:
        res_symbol = 'X'
    return res_symbol


@app.callback(
    Input('placeholder', 'title'),
    # Input('groups-input', 'value'),
    Output('matchs-table', 'data'),
    Output('classification-table', 'data'),
    Output('matchs-table', 'style_data_conditional'),
)
def load_matches(x):
    show_groups = [1]
    rounds = []
    tic = time.perf_counter()

    print('Calling the API')
    try:
        response = r.get(
            'https://raw.githubusercontent.com/openfootball/euro.json/master/2024/euro.json', timeout=8)
        print(f'Response status code: {response.status_code}')
        rounds = response.json()['rounds']
        # UNCOMMENT FOR TESTING
        # with open('tests/matches.json', 'r') as f:
        #     rounds = json.load(f)['rounds']
    except:
        print('API call failed, no stored matches fallback for now')

    tac = time.perf_counter()
    print(f'API call ended in {tac - tic} seconds.')

    tic = time.perf_counter()

    for round in rounds:
        round['matches'] = sorted(round['matches'], key=lambda x: datetime.strptime(
            x['date'] + ' ' + x['time'], '%Y-%m-%d %H:%M'))

    match_rows = []
    added_matches = []

    for round in rounds:
        for match in round['matches']:
            home_team = TEAMS_EN_ES.get(
                match['team1']['name'], match['team1']['name'])
            away_team = TEAMS_EN_ES.get(
                match['team2']['name'], match['team2']['name'])
            home_flag = f"assets/country-flags/{match['team1']['code']}.png"
            away_flag = f"assets/country-flags/{match['team2']['code']}.png"
            score = match.get('score', {}).get('ft', None)
            home_score = score[0] if score else None
            away_score = score[1] if score else None
            match_tag = f"{home_team}-{away_team}"
            date = datetime.strptime(
                match['date'] + ' ' + match['time'], '%Y-%m-%d %H:%M')

            if match_tag == 'Croacia-Albania':
                home_score = 2
                away_score = 2
            elif match_tag == 'Alemania-Hungría':
                home_score = 2
                away_score = 0
            elif match_tag == 'Escocia-Suiza':
                home_score = 1
                away_score = 1
            elif match_tag == 'Eslovenia-Serbia':
                home_score = 1
                away_score = 1
            elif match_tag == 'Dinamarca-Inglaterra':
                home_score = 1
                away_score = 1
            elif match_tag == 'España-Italia':
                home_score = 1
                away_score = 0

            row = {
                'date': date.strftime('%a, %d %b, %H:%M').title(),
                'match': f"![home_flag]({home_flag}) **{home_team}** vs **{away_team}** ![away_flag]({away_flag})",
                'match_key': match_tag,
                'home_team': home_team,
                'away_team': away_team,
                'tag': match_tag,
                'result': 'Not started' if home_score is None else f'{home_score} - {away_score}',
                'type': match['group']
            }

            if match_tag not in added_matches and home_team != '--' and away_team != '--':
                match_rows.append(row)
                added_matches.append(match_tag)

    styles = [
        {
            "if": {"state": "selected"},
            "backgroundColor": "none",
            "border": "1px solid rgb(211, 211, 211)",
        }
    ]

    pred_rows = []

    for file, clean_preds in PREDICTIONS.items():
        pred_row = {
            'nombre': file.split('.')[0].title(),
            'total': 0,
            'res_exacto': 0,
            'res_partido': 0,
            'octavos': 0,
            'cuartos': 0,
            'semis': 0,
            'final': 0,
            'campeon': 0,
        }

        group_stage_preds = clean_preds[:36]  # 36 group stage predictions
        octavos_teams = clean_preds[76:84]  # teams advancing to knockout stage
        cuartos_teams = clean_preds[92:96]  # quarter-finalists
        semis_teams = clean_preds[100:102]  # semi-finalists
        final_teams = clean_preds[102:104]  # finalists
        champion_team = clean_preds[106]  # winner

        for match in match_rows:
            if match['date'] == '-':
                continue
            try:
                match_idx = MATCH_TAGS.index(match['tag'])

                pred_result = [int(goals) for goals in group_stage_preds[match_idx].split('|')[
                    1].split('-')]
                match[file] = f'{pred_result[0]} - {pred_result[1]}'

                if match['type'] == 'R16':
                    if match['home_team'] in octavos_teams:
                        pred_row['octavos'] += 1
                    if match['away_team'] in octavos_teams:
                        pred_row['octavos'] += 1

                if match['type'] == 'QR':
                    if match['home_team'] in cuartos_teams:
                        pred_row['cuartos'] += 1
                    if match['away_team'] in cuartos_teams:
                        pred_row['cuartos'] += 1

                if match['type'] == 'semi':
                    if match['home_team'] in semis_teams:
                        pred_row['semis'] += 1
                    if match['away_team'] in semis_teams:
                        pred_row['semis'] += 1

                if match['type'] == 'FIN':
                    if match['home_team'] in final_teams:
                        pred_row['final'] += 1
                    if match['away_team'] in final_teams:
                        pred_row['final'] += 1
                    if champion_team == '':
                        pred_row['campeon'] += 1

                if match['result'] != 'Not started':
                    real_result = [int(goals)
                                   for goals in match['result'].split('-')]
                    real_res_symbol = get_res_symbol(real_result)
                    pred_res_symbol = get_res_symbol(pred_result)

                    if real_result[0] == pred_result[0] and real_result[1] == pred_result[1]:
                        pred_row['res_exacto'] += 1
                        styles.append({
                            'if': {
                                'filter_query': '{match} = "' + match['match'] + '"' + ' && {date} = "' + match['date'] + '"',
                                'column_id': file
                            },
                            'backgroundColor': '#92ff9273',
                        })
                    elif real_res_symbol == pred_res_symbol:
                        pred_row['res_partido'] += 1
                        styles.append({
                            'if': {
                                'filter_query': '{match} = "' + match['match'] + '"' + ' && {date} = "' + match['date'] + '"',
                                'column_id': file
                            },
                            'backgroundColor': '#ffff0080',
                        })
                    else:
                        styles.append({
                            'if': {
                                'filter_query': '{match} = "' + match['match'] + '"' + ' && {date} = "' + match['date'] + '"',
                                'column_id': file
                            },
                            'backgroundColor': '#ff3e3e59',
                        })

            except Exception as e:
                log.info(
                    f'Error parsing {pred_row["nombre"]} predictions: {e}')

        pred_row['total'] = pred_row['res_exacto'] * 10 + \
            pred_row['res_partido'] * 5 + \
            pred_row['octavos'] * 6 + \
            pred_row['cuartos'] * 12 + \
            pred_row['semis'] * 24 + \
            pred_row['final'] * 48 + \
            pred_row['campeon'] * 50

        pred_rows.append(pred_row)

    pred_rows.sort(key=lambda x: x['total'], reverse=True)

    for i, row in enumerate(pred_rows):
        row['position'] = i + 1

    if len(show_groups) == 0:
        match_rows = [row for row in match_rows if row['type'] != 'group']

    tac = time.perf_counter()
    print(f'Total data postprocessing took {tac - tic} seconds.')

    return match_rows, pred_rows, styles


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8080, use_reloader=False)

from dash import Dash, html, dcc

# from git_analytics.utilities import read, load_config
# from git_analytics.fig_generation import FigGenerator
from utilities import read, load_config
from fig_generation import FigGenerator


import pandas as pd
from plotly.express import line
gif = line(pd.DataFrame([[1, 3], [1, 4]], columns=['x', 'y']), x='x',y='y')
gif = dcc.Graph(
    figure= gif
)

CONFIG_FILE_NM = 'figs'

def main():

    config = load_config(CONFIG_FILE_NM)

    df_commits = read('commits')
    df_commits_files = read('commits_files')

    source_data_nm_to_df = {
        'commits':df_commits,
        'commits_files':df_commits_files
    }

    figs = []

    for _, fig_config in config.items():

        fig_gen = FigGenerator(**fig_config['fig_gen_arg'])
        fig = fig_gen.get_fig(source_data_nm_to_df[fig_config['source_df_nm']])
        figs.append(dcc.Graph(figure=fig))


    app = Dash(__name__)
    app.layout = html.Div(
        children=[
            html.Div(id='figs', children=figs)
            ]
        )
    app.run(debug=True)


if __name__ == '__main__':

    main()

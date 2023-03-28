from email.mime import application
import pandas as pd

from flask import Flask

from dash import Dash, html, dcc, Output, Input

from utilities import read, load_config
from fig_generation import FigGenerator

CONFIG_FILE_NM = 'figs'

MIN_PROP_OF_TOP_TO_BE = 0.01


class WebApp:

    def __init__(self, config) -> None:

        self.config = config

        self.df_commits_base = read('commits')
        self.df_commits_files_base = read('commits_files')

        print(__name__)
        server = Flask(__name__)
        self.app = Dash(__name__, server=server)

    def get_commit_id(self, df_commits):

        return df_commits.id.values

    def get_period_slider(self):

        start = self.df_commits_base.index.min()
        end = self.df_commits_base.index.max()

        intervals = pd.date_range(start, end, freq='M')
        self.intervals = [
            "%s-%d" % (month, year)
            for month, year in zip(intervals.strftime('%b'), intervals.year)
        ][::4]

        return dcc.RangeSlider(
            0,
            len(self.intervals)-1,
            step=None,
            marks={i:dt for i,dt in enumerate(self.intervals)},
            allowCross=False,
            id='period_slider',
            value=[0, len(self.intervals)-1]
        )

    def set_layout(self):

        self.app.layout = html.Div(
        children=[
            html.Div(id='slider_div', children=self.get_period_slider()),
            html.Div(id='figs') 
            ]
        )

    def get_figs(self, df_commits, df_commits_files):

        source_data_nm_to_df = {
            'commits':df_commits,
            'commits_files':df_commits_files
        }

        figs = []

        for _, fig_config in self.config.items():

            fig_gen = FigGenerator(**fig_config['fig_gen_arg'])
            fig = fig_gen.get_fig(source_data_nm_to_df[fig_config['source_df_nm']])
            figs.append(dcc.Graph(figure=fig))

        return figs

    def filter_on_period(self, df, start_index, end_index):

        start = self.intervals[start_index]
        end = self.intervals[end_index]

        return df.loc[(df.index > start) & (df.index<end)]

    def focus_on_key(self, entity_nm, df):

        entity_vol = df.groupby(entity_nm).n_code_lines_inserted.sum().sort_values(ascending=False)
        top_entity_vol = entity_vol.iloc[0]

        key_entity_nms = entity_vol[entity_vol > MIN_PROP_OF_TOP_TO_BE*top_entity_vol].index.tolist()
        df = df.loc[df[entity_nm].isin(key_entity_nms)]
        df[entity_nm] = df[entity_nm].cat.set_categories(key_entity_nms)

        return df

    def set_callback(self):

        @self.app.callback(
            Output('figs', 'children'),
            [Input('period_slider', 'value')])
        def get_figs_on_period(interval_index):

            dfs = {}
            
            for nm, df in zip(['df_commits', 'df_commits_files'], [self.df_commits_base, self.df_commits_files_base]):
                
                df = df.copy(deep=True)
                df = self.filter_on_period(df, *interval_index)
                df = self.focus_on_key('author_nm', df)

                if nm == 'df_commits_files':
                    df = self.focus_on_key('module_nm', df)

                dfs[nm] = df

            figs = self.get_figs(**dfs)

            return figs
        
    def run_server(self):

        self.app.run(debug=True)


if __name__ == '__main__':
    config = load_config(CONFIG_FILE_NM)
    web_app = WebApp(config)
    web_app.set_layout()
    web_app.set_callback()
    web_app.run_server()
from numpy import zeros
import pandas as pd

from flask import Flask

from dash import Dash, html, dcc, Output, Input

from utilities import read, load_config
from fig_generation import FigGenerator

CONFIG_FILE_NM = 'figs'
MIN_PROP_OF_TOP_TO_BE = 0.1
INPUT_PERSISTENCE_LOCATION = False


class WebApp:

    ENTITY_INPUT_NMS = ["module_nm", "component_nm", "author_nm", "ext"]

    def __init__(self, config) -> None:

        self.config = config
        self.df_base = read('commits_files')

        server = Flask(__name__)
        self.app = Dash(__name__, server=server)

        self.set_initial_selection()

    def set_initial_selection(self):
        
        self.selection = {
            entity_nm:{"value":None, "filter":self.get_base_filter(), "focus":False}
            for entity_nm in self.ENTITY_INPUT_NMS+["period"]
            }
        
    def get_base_filter(self):

        base_filter = zeros((len(self.df_base), ), dtype="bool")
        base_filter[:] = True

        return base_filter

    def get_key_labels(self, entity_nm, df=None):

        if df is None:
            df = self.df_base

        key_labels = (
            df
            .groupby(entity_nm)
            .n_code_lines_inserted
            .sum()
            .sort_values(ascending=False)
            .pipe(lambda srx: (
                srx
                .loc[srx > MIN_PROP_OF_TOP_TO_BE*srx.iloc[0]]
                .index
                .tolist()
            ))
        )

        return key_labels

    def get_period_slider(self):

        start = self.df_base.index.min()
        end = self.df_base.index.max()
        intervals = pd.date_range(start, end, freq='M')
        self.intervals = [
            "%s-%d" % (month, year)
            for month, year in zip(intervals.strftime('%b'), intervals.year)
        ][::4]
        n_intervals = len(self.intervals)-1

        self.selection["period"]["value"] = [0, n_intervals]

        return dcc.RangeSlider(
            0,
            n_intervals-1,
            step=None,
            marks={i:dt for i,dt in enumerate(self.intervals)},
            allowCross=False,
            id='period_slider',
            value=self.selection["period"]["value"],
            persistence=INPUT_PERSISTENCE_LOCATION
        )

    def get_entity_selection_dropdown(self, entity_nm):

        labels = self.df_base[entity_nm].unique().tolist()
        key_labels = self.get_key_labels(entity_nm)
        self.selection[entity_nm]['value'] = key_labels
        self.selection[entity_nm]['focus'] = True
        self.update_filter(entity_nm, key_labels)

        return dcc.Dropdown(
            id='%s_selection' % entity_nm,
            options=labels,
            value=key_labels,
            multi=True,
            persistence=INPUT_PERSISTENCE_LOCATION
        )

    def set_layout(self):

        entity_selection_dropdown = [
            self.get_entity_selection_dropdown(entity_nm)
            for entity_nm in self.ENTITY_INPUT_NMS
        ]

        self.app.layout = html.Div(
        children=[
            html.Div(id='slider_div', children=self.get_period_slider()),
            *entity_selection_dropdown,
            html.Div(id='figs') 
            ]
        )

    def get_figs(self, df):

        figs = []

        for _, fig_config in self.config.items():

            fig_gen = FigGenerator(**fig_config['fig_gen_arg'])
            fig = fig_gen.get_fig(df)
            figs.append(dcc.Graph(figure=fig))

        return figs

    def get_fired_input(self, *args):

        for input_nm, input_val in zip(self.ENTITY_INPUT_NMS+['period'], args):
            if input_val != self.selection[input_nm]["value"]:
                return (input_nm, input_val)

    def update_selection(self, input_nm, input_val):
        self.selection[input_nm]["value"] = input_val

    def get_period_as_date(self, period):

        start = self.intervals[period[0]]
        end = self.intervals[period[1]]

        return [start, end]

    def update_filter(self, input_nm, input_val):

        if input_nm == "period":
            period = self.get_period_as_date(input_val)
            self.selection[input_nm]["filter"] = (
                (self.df_base.index >= period[0])
                & (self.df_base.index >= period[1])
            )
        else:
            self.selection[input_nm]["filter"] = self.df_base[input_nm].isin(input_val)

    def get_selection_df(self):

        selection_filter = self.get_base_filter()
        for selection in self.selection.values():
            selection_filter = selection_filter & selection["filter"]

        return self.df_base.loc[selection_filter]

    def get_input_val(self):
        return [
            v["value"]
            for k, v in self.selection.items()
            if k != "period"
            ]

    def focus_on_key_element(self, df):

        for entity_nm in self.ENTITY_INPUT_NMS:
            if self.selection[entity_nm]['focus'] == False:
                key_labels = self.get_key_labels(entity_nm, df)
                self.update_selection(entity_nm, key_labels)
                self.update_filter(entity_nm, key_labels)

        return self.get_selection_df()

    def reset_focus_state(self):
        
        for entity_nm in self.ENTITY_INPUT_NMS:
            self.selection[entity_nm]['focus'] = False

    def update_is_an_add(self, entity_nm, new_selection):

        current_selection = self.selection[entity_nm]['value']
        if len(new_selection) > len(current_selection):
            return True

        return False


    def set_callback(self):

        entity_inputs = [
            Input('%s_selection' % entity_nm, 'value')
            for entity_nm in self.ENTITY_INPUT_NMS
        ]

        entity_outputs = [
            Output('%s_selection' % entity_nm, 'value')
            for entity_nm in self.ENTITY_INPUT_NMS
        ]

        @self.app.callback(
            [
                Output('figs', 'children'),
                *entity_outputs
            ],
            [
                *entity_inputs,
                Input('period_slider', 'value')
            ]
        )
        def gen_figs_based_on_input(*args):

            element_added = False #assume not by default and update otherwise
            fired_input = self.get_fired_input(*args)

            if fired_input is not None:
                element_added = self.update_is_an_add(*fired_input)
                self.update_selection(*fired_input)
                self.reset_focus_state()
                self.update_filter(*fired_input) 
            
            df = self.get_selection_df() 
            
            if not element_added:
                df = self.focus_on_key_element(df)

            figs = self.get_figs(df)
            input_val = self.get_input_val()
            return figs, *input_val
        
    def run_server(self):

        self.app.run(debug=True)


if __name__ == '__main__':
    config = load_config(CONFIG_FILE_NM)
    web_app = WebApp(config)
    web_app.set_layout()
    web_app.set_callback()
    web_app.run_server()



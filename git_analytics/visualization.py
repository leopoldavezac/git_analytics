from numpy import zeros
import pandas as pd

from flask import Flask

from dash import Dash, html, dcc, Output, Input, callback_context
from dash_bootstrap_components import Container, Col, Row
from dash_bootstrap_components.themes import BOOTSTRAP

from git_analytics.utilities import read
from git_analytics.cmd_chaining import run_predessor_if_needed
from git_analytics.fig_generation import FigGenerator
from git_analytics.config_management import ConfigManager

CMD_NM = 'visualize'

MIN_PROP_OF_TOP_TO_BE = 0.1
INPUT_PERSISTENCE_LOCATION = False

VIEW_NMS = ['overview', 'coding_activity', 'knowledge_perenity']

class Dashboard:

    ENTITY_INPUT_NMS = ["module_nm", "component_nm", "author_nm", "ext"]

    def __init__(self, specs:dict, codebase_nm:str) -> None:

        self.specs = specs
        self.codebase_nm = codebase_nm
        self.df_base = read(codebase_nm, 'commits_files')

        self.view_nm = 'overview'
        self.view_memory = [0, 0, 0]

        self.app = Dash(__name__, external_stylesheets=[BOOTSTRAP])

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
    
    def get_fig_space_layout(self, figs):

        rows = []

        for row_stat_ids in self.specs[self.view_nm]['layout']:
            rows.append(
                Row(children=[Col(id=col_stat_id, children=figs.pop()) for col_stat_id in row_stat_ids])
            )

        return Container(children=rows)


    def set_initial_layout(self):

        entity_selection_dropdown = [
            self.get_entity_selection_dropdown(entity_nm)
            for entity_nm in self.ENTITY_INPUT_NMS
        ]

        df = self.focus_on_key_element(self.df_base)
        figs = self.get_figs(df) 
        fig_space = self.get_fig_space_layout(figs)

        self.app.layout = Container(
        children=[
            html.Div([
                html.Div(
                    html.Button(nm, id='%s_view' % nm, n_clicks=0)
                ) for nm in VIEW_NMS
            ]),
            html.Div(id='slider_div', children=self.get_period_slider()),
            *entity_selection_dropdown,
            html.Div(id='figs', children=fig_space) 
            ]
        )

    def get_figs(self, df=None):

        if df is None:
            df = self.df_base

        figs = []

        for id, stat in self.specs[self.view_nm]['stats'].items():

            fig_gen = FigGenerator(**stat['def'])
            fig = fig_gen.get_fig(df)
            figs.append(dcc.Graph(figure=fig))

        return figs

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

        df = df.copy(deep=True)

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

        view_inputs = [
            Input('%s_view' % nm, 'n_clicks')
            for nm in VIEW_NMS
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
                *view_inputs,
                Input('period_slider', 'value')
            ],
            prevent_initial_call=True
        )
        def gen_figs_based_on_input(*args):

            triggered_id = callback_context.triggered_id
            new_values = [
                input_val['value']
                for input_val in callback_context.args_grouping
                if input_val['triggered']
            ][0]

            if triggered_id[-4:] == 'view':

                self.view_nm = triggered_id[:-5]
                df = self.focus_on_key_element(self.df_base)
                figs = self.get_figs(df) 
                fig_space = self.get_fig_space_layout(figs)

                input_val = self.get_input_val()

                return fig_space, *input_val

            entity_nm = triggered_id[:-10]

            element_added = False #assume not by default and update otherwise
        
            element_added = self.update_is_an_add(entity_nm, new_values)
            self.update_selection(entity_nm, new_values)
            self.reset_focus_state()
            self.update_filter(entity_nm, new_values) 
            
            df = self.get_selection_df() 
            
            if not element_added:
                df = self.focus_on_key_element(df)

            figs = self.get_figs(df)
            input_val = self.get_input_val()

            fig_space = self.get_fig_space_layout(figs)

            return fig_space, *input_val
        
        
        # @self.app.callback(
        #     Output('figs', 'children'),
        #     [*view_inputs],
        #     prevent_initial_call=True
        # )
        # def gen_figs_based_on_input(*args):

        #     view_state = args
        #     for nm, state_nclicks, memory_ncliks in zip(VIEW_NMS, view_state, self.view_memory): 
        #         if state_nclicks != memory_ncliks:
        #             self.view_nm = nm

        #     figs = self.get_figs(self.df_base)

        #     return html.Div(figs)  



    def get_app_server(self):

        return self.app.server
        
    def run_server(self):
        #host="0.0.0.0", port="8050"
        self.app.run(debug=True)


def visualize(config_manager:ConfigManager) -> Dashboard:

    run_predessor_if_needed(CMD_NM, config_manager)
    web_app = Dashboard(config_manager['dashboard_specs'], config_manager['codebase_nm'])
    web_app.set_initial_layout()
    web_app.set_callback()

    return web_app
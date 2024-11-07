from numpy import zeros
import pandas as pd

from flask import Flask

from dash import Dash, html, dcc, Output, Input, callback_context
from dash_bootstrap_components import Container, Col, Row, Button, Offcanvas, Navbar
from dash_bootstrap_components.themes import BOOTSTRAP

from src.utilities import read
from src.cmd_chaining import run_predessor_if_needed
from src.fig_generation import FigGenerator
from src.config_management import ConfigManager

CMD_NM = 'visualize'

MIN_PROP_OF_TOP_TO_BE = 0.1
INPUT_PERSISTENCE_LOCATION = False

VIEW_NMS = ['overview', 'coding_activity', 'knowledge_perenity']

class Dashboard:

    entity_input_nms = ["module_nm", "author_nm", "ext"]

    def __init__(self, specs:dict, codebase_nm:str, has_components:bool) -> None:

        self.specs = specs
        self.codebase_nm = codebase_nm
        self.has_components = has_components
        self.df_base = read(codebase_nm, 'commits_files')

        # test that component nm exists if not update entity input names
        if self.has_components:
            self.entity_input_nms.append('component_nm')

        self.view_nm = 'overview'
        self.view_memory = [0, 0, 0]

        self.app = Dash(__name__, external_stylesheets=[BOOTSTRAP])

        self.set_initial_selection()

    def set_initial_selection(self):
        
        self.selection = {
            entity_nm:{"value":None, "filter":self.get_base_filter(), "focus":False}
            for entity_nm in self.entity_input_nms+["period"]
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

        intervals = pd.date_range(start, end, freq='2W')
        self.intervals = [
            "%s %s-%d" % (day, month, year)
            for day, month, year 
            in zip(intervals.strftime('%d'), intervals.strftime('%b'), intervals.year)
        ]

        n_intervals = len(self.intervals)

        self.selection["period"]["value"] = [0, n_intervals]

        return dcc.RangeSlider(
            0,
            n_intervals-1,
            step=None,
            marks={i:dt for i,dt in enumerate(self.intervals)},
            allowCross=False,
            id='period_selection',
            value=self.selection["period"]["value"],
            persistence=INPUT_PERSISTENCE_LOCATION
        )

    def get_entity_selection_dropdown(self, entity_nm):

        labels = self.df_base[entity_nm].dropna().unique().tolist()
        key_labels = self.get_key_labels(entity_nm)
        self.selection[entity_nm]['value'] = key_labels
        self.selection[entity_nm]['focus'] = True
        self.update_filter(entity_nm, key_labels)

        return  html.Div([
            html.H5(entity_nm),
            dcc.Dropdown(
                id='%s_selection' % entity_nm,
                options=labels,
                value=key_labels,
                multi=True,
                persistence=INPUT_PERSISTENCE_LOCATION
            ),
            html.Br()
        ])
    
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
            for entity_nm in self.entity_input_nms
        ]
        
        df = self.focus_on_key_element(self.df_base)
        figs = self.get_figs(df) 
        fig_space = self.get_fig_space_layout(figs)

        navbar = Navbar(
            Container([Button(html.H5("Filter results"), id='filter_panel_button', color="light", style={'width': '50%', 'margin':'auto'}, n_clicks=0)]
            ),
            fixed='bottom', color="#FFFFFF"
        )


        self.app.layout = Container(
        children=[
            html.H1('LibPerenity', style={'textAlign': 'center'}),
            html.H3('Make sure your dependencies are reliable', style={'textAlign': 'center'}),
            html.Br(),
            html.Div(
                Row(
                    children=[
                        Col(html.Div(
                            Button(html.H5(nm), id='%s_view' % nm, n_clicks=0, style={'width': '100%'}, color="light")
                        )) for nm in VIEW_NMS
                    ],
                ),
            ),
            html.Br(),
            html.Div(id='slider_div', children=[self.get_period_slider()], className="p-3 bg-light border rounded-3",),
            html.Br(),
            Offcanvas([*entity_selection_dropdown], id='filter_panel', style={'height':'80%'}, className="p-3 bg-light border rounded-3", is_open=False, placement='bottom'),
            html.Div(id='figs', children=fig_space),
            navbar
            ]
        )

    def get_figs(self, df=None):

        if df is None:
            df = self.df_base

        figs = []

        for stat in self.specs[self.view_nm]['stats'].values():

            fig_gen = FigGenerator(title=stat['nm'], **stat['def'])
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

        for entity_nm in self.entity_input_nms:
            if self.selection[entity_nm]['focus'] == False:
                key_labels = self.get_key_labels(entity_nm, df)
                self.update_selection(entity_nm, key_labels)
                self.update_filter(entity_nm, key_labels)

        return self.get_selection_df()

    def reset_focus_state(self):
        
        for entity_nm in self.entity_input_nms:
            self.selection[entity_nm]['focus'] = False

    def update_is_an_add(self, entity_nm, new_selection):

        current_selection = self.selection[entity_nm]['value']
        if len(new_selection) > len(current_selection):
            return True

        return False


    def set_callback(self):

        entity_inputs = [
            Input('%s_selection' % entity_nm, 'value')
            for entity_nm in self.entity_input_nms
        ]

        view_inputs = [
            Input('%s_view' % nm, 'n_clicks')
            for nm in VIEW_NMS
        ]

        entity_outputs = [
            Output('%s_selection' % entity_nm, 'value')
            for entity_nm in self.entity_input_nms
        ]

        @self.app.callback(
            [
                Output('figs', 'children'),
                *entity_outputs
            ],
            [
                *entity_inputs,
                *view_inputs,
                Input('period_selection', 'value')
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

        @self.app.callback(
            Output('filter_panel', 'is_open'),
            [
                Input('filter_panel_button', 'n_clicks')
            ],
            prevent_initial_call=True
        )
        def open_filter_panel(n_clicks):

            return True
        

    def get_app_server(self):

        return self.app.server
        
    def run_server(self):
        self.app.run(debug=True)


def visualize(config_manager:ConfigManager) -> Dashboard:

    run_predessor_if_needed(CMD_NM, config_manager)
    web_app = Dashboard(config_manager['dashboard_specs'], config_manager['codebase_nm'], config_manager['has_components'])
    web_app.set_initial_layout()
    web_app.set_callback()

    return web_app
from numpy import zeros
import pandas as pd

from flask import Flask

from dash import Dash, html, dcc, Output, Input, callback_context
from dash_bootstrap_components import Container, Col, Row, Button, Offcanvas, Navbar
from dash_bootstrap_components.themes import BOOTSTRAP

from src.utilities import read
from src.fig_generation import FigGenerator
from src.config_management import ConfigManager

CMD_NM = 'visualize'

INPUT_PERSISTENCE_LOCATION = False

class Dashboard:

    VIEW_NMS = ['overview', 'coding_activity', 'knowledge_perenity']

    analysis_axis = ["module_nm", "author_nm", "ext"]

    def __init__(self, specs, codebase_nm) -> None:

        self.specs = specs
        self.codebase_nm = codebase_nm
       
        self.df_base = read(codebase_nm, 'commits_files')
        self.df_current = self.df_base.copy(deep=True)

        if 'component_nm' in self.df_base.columns:
            # entity could be better named
            self.analysis_axis.append('component_nm')

        self.current_view_nm = 'overview'

        self.app = Dash(__name__, external_stylesheets=[BOOTSTRAP])

        self.init_filter()


    def init_filter(self):
        
        self.filter_state = {
            axis:{"value":None, "mask":self.get_base_mask()}
            for axis in self.analysis_axis+["period"]
        }
        

    def get_base_mask(self):

        return pd.Series([True] * len(self.df_base)).values
    

    def set_initial_layout(self):

        self.app.layout = Container(
            children=[
            self.get_header(),
            self.get_view_buttons(),
            self.get_period_slider(),
            self.get_graphs_space(first_run=True),
            self.get_filter_navbar(),
            self.get_filter_selection_panel()

        ])    

    def get_header(self):

        return html.Div(
            [
                html.H1('LibPerenity', style={'textAlign': 'center'}),
                html.H3('Make sure your dependencies are reliable', style={'textAlign': 'center'}),
                html.Br(),
            ]
        )

    def get_view_buttons(self):

        return html.Div(
            [
                Row(
                    children=[
                        Col(html.Div(
                            Button(
                                html.H5(nm), id='%s_view' % nm, n_clicks=0,
                                style={'width': '100%'},
                                color="light"
                            )
                        )) for nm in self.VIEW_NMS
                    ],
                ),
                html.Br()
            ]
        )
    

    def get_period_slider(self):

        max_nb_of_intervals = 13
        interval_display_format = '%d %b %Y'

        start = self.df_base.index.min()
        end = self.df_base.index.max()

        self.intervals = (
            [start.strftime(interval_display_format)]
            + pd.date_range(start, end, freq='2W').strftime(interval_display_format).tolist()
            + [end.strftime(interval_display_format)]
        )

        n_intervals = len(self.intervals)
        show_every_n = round(n_intervals / (max_nb_of_intervals - 2)) #-2 to account for first & last interval

        if show_every_n > 0:
            self.intervals = [
                interval for i, interval in enumerate(self.intervals)
                if ((i % show_every_n) == 0) or (i == n_intervals - 1)
            ]
            n_intervals = len(self.intervals)

        self.filter_state["period"]["value"] = [0, n_intervals]

        period_slider = dcc.RangeSlider(
            0,
            n_intervals-1,
            step=None,
            marks={i:dt for i,dt in enumerate(self.intervals)},
            allowCross=False,
            id='period_selection',
            value=self.filter_state["period"]["value"],
            persistence=INPUT_PERSISTENCE_LOCATION
        )

        period_slider = html.Div(
            id='slider_div',
            children=[
                period_slider,
                html.Br()
            ],
            className="p-3 bg-light border rounded-3"
        )

        return period_slider
    

    def get_graphs_space(self, first_run=False, filter_update=True):

        if first_run:
            self.focus_on_key_labels()
        else:
            if filter_update:
                self.update_current_df()
    
        graphs = self.gen_graphs() 
        graph_layout = self.insert_graphs_in_layout(graphs) 

        return graph_layout
    

    def focus_on_key_labels(self):

        for axis in self.analysis_axis:

            key_labels = self.compute_key_labels(axis)
            self.update_filter_state(axis, key_labels)

        self.update_current_df()
    

    def compute_key_labels(self, axis):

        min_prop_of_max = 0.1

        key_labels = (
            self.df_base
            .groupby(axis)
            .n_code_lines_inserted.sum()
            .sort_values(ascending=False)
            .pipe(lambda srx: srx.loc[srx > min_prop_of_max*srx.iloc[0]].index.tolist())
        )

        return key_labels


    def update_filter_state(self, axis_nm, filter_on):

        self.filter_state[axis_nm]["value"] = filter_on

        if axis_nm == "period":
            self.update_period_mask(filter_on)
        else:
            self.filter_state[axis_nm]["mask"] = self.df_base[axis_nm].isin(filter_on)


    def update_period_mask(self, filter_on):

        period = self.get_period_as_date(filter_on)
        self.filter_state["period"]["mask"] = (
            (self.df_base.index >= period[0])
            & (self.df_base.index <= period[1])
        )


    def get_period_as_date(self, period):

        start = self.intervals[period[0]]
        end = self.intervals[period[1]]

        return [start, end]
    
    def update_current_df(self):

        mask = self.get_base_mask()
        for selection in self.filter_state.values():
            mask = mask & selection["mask"]

        self.df_current = self.df_base.loc[mask]

    
    def gen_graphs(self):

        graphs = []

        for stat in self.specs[self.current_view_nm]['stats'].values():

            fig_gen = FigGenerator(title=stat['nm'], **stat['def'])
            fig = fig_gen.get_fig(self.df_current)
            graphs.append(dcc.Graph(figure=fig))

        return graphs
    

    def insert_graphs_in_layout(self, graphs):

        rows = []

        for row_stat_ids in self.specs[self.current_view_nm]['layout']:
            rows.append(
                Row(children=[
                    Col(id=col_stat_id, children=graphs.pop())
                    for col_stat_id in row_stat_ids
                ])
            )

        return html.Div(id='graphs', children=Container(children=rows))
    


    def get_filter_navbar(self):

        navbar = Navbar(
            Container([
                Button(
                    html.H5("Filter results"),
                    id='filter_panel_button',
                    color="light",
                    style={'width': '50%', 'margin':'auto'},
                    n_clicks=0)
                ]
            ),
            fixed='bottom', color="#FFFFFF"
        )
        
        navbar = html.Div([html.Br(), html.Br(), html.Br(), navbar])
        
        return navbar
    

    def get_filter_selection_panel(self):

        axis_label_selection_dropdown = [
            self.get_axis_label_selection_dropdown(axis)
            for axis in self.analysis_axis
        ]

        axis_label_selection_dropdown = Offcanvas(
            [*axis_label_selection_dropdown],
            id='filter_panel',
            style={'height':'80%'},
            className="p-3 bg-light border rounded-3",
            is_open=False,
            placement='bottom'
        )

        return axis_label_selection_dropdown
    
    def get_axis_label_selection_dropdown(self, axis):

        labels = self.df_base[axis].dropna().unique().tolist()
        key_labels = self.filter_state[axis]['value']

        return  html.Div([
            html.H5(axis),
            dcc.Dropdown(
                id='%s_selection' % axis,
                options=labels,
                value=key_labels,
                multi=True,
                persistence=INPUT_PERSISTENCE_LOCATION
            ),
            html.Br()
        ])


    def set_callbacks(self):

        filter_axis_label_input = [
            Input('%s_selection' % entity_nm, 'value')
            for entity_nm in self.analysis_axis
        ]

        view_inputs = [
            Input('%s_view' % nm, 'n_clicks')
            for nm in self.VIEW_NMS
        ]

        filter_axis_label_output = [
            Output('%s_selection' % entity_nm, 'value')
            for entity_nm in self.analysis_axis
        ]

        @self.app.callback(
            [
                Output('graphs', 'children'),
                *filter_axis_label_output
            ],
            [
                *filter_axis_label_input,
                *view_inputs,
                Input('period_selection', 'value')
            ],
            prevent_initial_call=True
        )
        def update_graph_space_based_on_input(*args):
            
            triggered_input_nm = callback_context.triggered_id

            input_values = [
                input_val['value']
                for input_val in callback_context.args_grouping
                if input_val['triggered']
            ][0]

            # hanle with case : view_change / axis_filter_update / period_filter
            input_is_view_change = triggered_input_nm[-4:] == 'view'
            if input_is_view_change:

                self.current_view_nm = triggered_input_nm[:-5]
                graph_space = self.get_graphs_space(filter_update=False)
            
            # case input is filter update
            else:
                filter_axis = triggered_input_nm[:-10]
                self.update_filter_state(filter_axis, input_values)                

            graph_space = self.get_graphs_space()

            return graph_space, *self.get_current_axis_filter_state()

        @self.app.callback(
            Output('filter_panel', 'is_open'),
            [
                Input('filter_panel_button', 'n_clicks')
            ],
            prevent_initial_call=True
        )
        def open_filter_panel(n_clicks):

            return True
        

    def get_current_axis_filter_state(self):
        return [
            v["value"]
            for k, v in self.filter_state.items()
            if k != "period"
            ]


    def test_update_is_add(self, entity_nm, new_selection):

        current_selection = self.selection[entity_nm]['value']
        if len(new_selection) > len(current_selection):
            return True

        return False
    

    def get_app_server(self):

        return self.app.server
        
    def run_server(self):
        self.app.run(debug=True)


def visualize(config_manager:ConfigManager) -> Dashboard:

    web_app = Dashboard(config_manager['dashboard_specs'], config_manager['codebase_nm'])
    web_app.set_initial_layout()
    web_app.set_callbacks()

    return web_app

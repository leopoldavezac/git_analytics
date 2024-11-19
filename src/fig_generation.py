from plotly.express import imshow, line, bar, pie

from copy import deepcopy


class UnknownOperation(Exception):
    pass

class Transformer:

    CONCEPT_TO_OPERATION_SUITE = {
        'stability' : ['groupby', 'resample', 'agg', 'unstack', 'normalize', 'T', 'round', 'replace'],
        'evolution' : ['resample', 'agg', 'reset_index'],
        'specialization' : ['groupby', 'agg', 'unstack', 'normalize', 'T', 'round', 'replace'],
        'size' : ['groupby', 'agg', 'reset_index'],
        'repartition' : ['groupby', 'agg', 'reset_index']
    }

    OPERATION_NM_TO_ARG_NM = {
        'groupby':'entity',
        'resample':'freq',
        'agg':'mesure',
        'unstack':'unstack_level',
        'normalize':'normalize_axis',
        'reset_index':'NONE',
        'sum':'NONE',
        'nunique':'NONE',
        'count':'NONE',
        'replace':'REPLACE_ARG',
        'round':'ROUND_ARG',

    }

    REPLACE_ARG = {0:None}
    ROUND_ARG = 2
    NONE = None

    def __init__(
        self,
        concept,
        mesure,
        entity=None,
        normalize_axis=1,
        aggfunc='sum',
        freq='M',
        unstack_level=0
        ):

        self.concept = concept
        self.mesure = mesure
        self.entity = entity
        self.normalize_axis = normalize_axis
        self.aggfunc = aggfunc
        self.freq = freq
        self.unstack_level = unstack_level
        
        self.operations = deepcopy(self.CONCEPT_TO_OPERATION_SUITE[concept]) #why ?
        self.__fill_agg_placeholder_operation(aggfunc, mesure)

    def __fill_agg_placeholder_operation(self, aggfunc, mesure):

        agg_index = self.operations.index('agg')
        self.operations.insert(agg_index, aggfunc)
        self.operations.insert(agg_index, mesure)
        self.operations.pop(agg_index+2)

    def __get_operation_arg(self, operation_nm):
        
        arg_nm = self.OPERATION_NM_TO_ARG_NM[operation_nm]
        if arg_nm:
            arg_value = getattr(self, arg_nm)
            return arg_value
        else:
            return None

    def __get_operation_result(self, df, operation_nm):
        
        try:
            arg_value = self.__get_operation_arg(operation_nm)
        except KeyError: #operation is transpose == attribute not a method -> no corresponding key in OPERATION_NM_TO_ARG_NM
            return getattr(df, operation_nm) 

        try:
            if arg_value is not None:
                return getattr(df, operation_nm)(arg_value)
            else:
                return getattr(df, operation_nm)()
            
        except AttributeError: 
            if operation_nm == 'normalize':
                return df.pipe(lambda dfx: dfx.divide(dfx.sum(axis=arg_value), axis=(not bool(arg_value))))
            else:
                raise UnknownOperation(f'Operation: {operation_nm} is not supported')

    def get_transformed(self, df):

        for operation_nm in self.operations:
            df = self.__get_operation_result(df, operation_nm)

        return df


class FigGenerator(Transformer):

    CONCEPT_TO_FIG = {
        'stability':imshow,
        'evolution':line,
        'specialization':imshow,
        'repartition':pie,
        'size':bar
    }

    CONCEPT_TO_FIG_ARG_STRUCT = {
        'specialization':{'title':'title'},
        'stability':{'title':'title'},
        'evolution':{'x':'time', 'y':'mesure', 'title':'title'},
        'size':{'x':'mesure', 'y':'entity', 'orientation':'$h', 'title':'title'},
        'repartition':{'names':'entity', 'values':'mesure', 'title':'title'}
    }

    CONCEPT_TO_FIG_CUSTOM_DIMS = {
        'stability':['height'],
        'specialization':['height'],
        'evolution':[],
        'repartition':[],
        'size':['height'],
    }

    DIM_NM_TO_AXIS_NM = {
        'height':'y',
        'width':'x'
    }

    CONCEPT_TO_BASE_LAYOUT = {
        'stability':{'yaxis':{'tickmode':'linear'}},
        'specialization':{'yaxis':{'tickmode':'linear'}, 'xaxis':{'tickmode':'linear'}},
        'evolution':{},
        'repartition':{},
        'size':{'yaxis':{'tickmode':'linear'}}
    }

    GENERIC_LAYOUT_ARG = {'template':'plotly_white', 'font':{'size':13}}

    def __init__(
        self,
        concept,
        mesure,
        title='titile',
        entity=None,
        normalize_axis=1,
        aggfunc='count',
        freq='M',
        unstack_level=0,
        xaxis_title='',
        yaxis_title=''
        ):

        super().__init__(concept, mesure, entity, normalize_axis, aggfunc, freq, unstack_level)
        self.title = title
        self.xaxis_title = xaxis_title
        self.yaxis_title = yaxis_title

        self.fig_func = self.CONCEPT_TO_FIG[concept]
        self.fig_arg_struct = self.CONCEPT_TO_FIG_ARG_STRUCT[concept]
        self.custom_dims = self.CONCEPT_TO_FIG_CUSTOM_DIMS[concept]
        self.base_layout = self.CONCEPT_TO_BASE_LAYOUT[concept]
        self.base_layout.update(self.GENERIC_LAYOUT_ARG)



        self.time = 'creation_dt' # fig_gen allow for dynamic time var_nm but transformer does not yet

    def __get_fig_arg(self):

        fig_arg = {}
        for k, v in self.fig_arg_struct.items():
            if v[0] == '$':
                fig_arg[k] = v[1:]
            else:
                fig_arg[k] = getattr(self, v)

        return fig_arg

    def __get_dim_size(self, n_ticks, tick_font_size=13):

        return ((300 * n_ticks) // tick_font_size) + 200


    def __get_layout_arg(self, df, fig_arg):

        layout_arg = {}            

        for dim_nm in self.custom_dims:

            axis_nm = self.DIM_NM_TO_AXIS_NM[dim_nm]

            if len(fig_arg) == 1:
                n_ticks = df.shape[axis_nm == 'x']
            else:
                var_nm = fig_arg[axis_nm]
                n_ticks = df[var_nm].nunique()

            dim_size = self.__get_dim_size(n_ticks)

            layout_arg[dim_nm] = dim_size

        return layout_arg
    
    def __update_axis_titles(self, fig, fig_arg):

        if fig_arg['title'] != 'language repartition':

            fig.update_layout({'xaxis_title':self.xaxis_title, 'yaxis_title':self.yaxis_title})

    def get_fig(self, df):
        
        df = self.get_transformed(df)        
        fig_arg = self.__get_fig_arg()

        if self.concept in ['specialization', 'stability']:        
            fig = self.fig_func(df, **fig_arg, aspect='auto', zmax=1, zmin=0, color_continuous_scale='tealgrn')
        else:
            fig = self.fig_func(df, **fig_arg, color_discrete_sequence=['skyblue'])
            
        layout_arg = self.__get_layout_arg(df, fig_arg)
        layout_arg.update(self.base_layout)
        fig.update_layout(layout_arg)

        self.__update_axis_titles(fig, fig_arg)

        return fig
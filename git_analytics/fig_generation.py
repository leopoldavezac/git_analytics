from plotly.express import imshow, line, bar, pie

from copy import deepcopy

CONCEPT_TO_FIG_ARG_STRUCT = {
    'specialization':{},
    'stability':{},
    'evolution':{'x':'time', 'y':'mesure'},
    'size':{'x':'mesure', 'y':'entity', 'orientation':'$h'},
    'repartition':{'names':'entity', 'values':'mesure'}
}

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

CONCEPT_TO_FIG = {
    'stability':imshow,
    'evolution':line,
    'specialization':imshow,
    'repartition':pie,
    'size':bar
}

CONCEPT_TO_FIG_CUSTOM_DIMS = {
    'stability':['height'],
    'specialization':['height', 'width'],
    'specialization':[],
    'evolution':[],
    'repartition':[],
    'size':['height']
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

class UnknownOperation(Exception):
    pass

class Transformer:

    _REPLACE_ARG = {0:None}
    _ROUND_ARG = 2
    _NONE = None

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

        self._concept = concept
        self._mesure = mesure
        self._entity = entity
        self._normalize_axis = normalize_axis
        self._aggfunc = aggfunc
        self._freq = freq
        self._unstack_level = unstack_level
        
        self.operations = deepcopy(CONCEPT_TO_OPERATION_SUITE[concept]) #why ?
        self.__fill_agg_placeholder_operation(aggfunc, mesure)

    def __fill_agg_placeholder_operation(self, aggfunc, mesure):

        agg_index = self.operations.index('agg')
        self.operations.insert(agg_index, aggfunc)
        self.operations.insert(agg_index, mesure)
        self.operations.pop(agg_index+2)

    def __get_operation_arg(self, operation_nm):

        arg_nm = OPERATION_NM_TO_ARG_NM[operation_nm]
        if arg_nm:
            arg_value = getattr(self, '_%s' % arg_nm)
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
        except AttributeError: #custom operation
            if operation_nm == 'normalize':
                return df.pipe(lambda dfx: dfx.divide(dfx.sum(axis=arg_value), axis=(not bool(arg_value))))
            else:
                raise UnknownOperation('Operation: %s is not supported' % operation_nm)

    def get_transformed(self, df):

        for operation_nm in self.operations:
            df = self.__get_operation_result(df, operation_nm)

        return df


class FigGenerator(Transformer):

    def __init__(
        self,
        concept,
        mesure,
        entity=None,
        normalize_axis=1,
        aggfunc='count',
        freq='M',
        unstack_level=0
        ):
        
        self._time = 'creation_dt' # fig_gen allow for dynamic time var_nm but transformer does not yet

        self.fig = CONCEPT_TO_FIG[concept]
        self.fig_arg_struct =  CONCEPT_TO_FIG_ARG_STRUCT[concept]

        self.base_layout = CONCEPT_TO_BASE_LAYOUT[concept]
        self.custom_dims = CONCEPT_TO_FIG_CUSTOM_DIMS[concept]

        Transformer.__init__(self, concept, mesure, entity, normalize_axis, aggfunc, freq, unstack_level)

    def __get_fig_arg(self):

        fig_arg = {}

        for k, v in self.fig_arg_struct.items():
            
            if v[0] == '$':
                fig_arg[k] = v[1:]
            else:
                fig_arg[k] = getattr(self, '_%s' % v)

        return fig_arg

    def __get_dim_size(self, n_ticks, tick_font_size=12):

        COEF = 300
        size = COEF * n_ticks / tick_font_size

        return size if size > 250 else 250


    def __get_layout_arg(self, df, fig_arg):

        layout_arg = {}            

        for dim_nm in self.custom_dims:

            axis_nm = DIM_NM_TO_AXIS_NM[dim_nm]

            if len(fig_arg) == 0:
                n_ticks = df.shape[axis_nm == 'x']
            else:
                var_nm = fig_arg[axis_nm]
                n_ticks = df[var_nm].nunique()

            dim_size = self.__get_dim_size(n_ticks)

            layout_arg[dim_nm] = dim_size

        return layout_arg


    def get_fig(self, df):
        
        df = self.get_transformed(df)        
        fig_arg = self.__get_fig_arg()

        if self._concept in ['specialization', 'stability']:        
            fig = self.fig(df, **fig_arg, aspect='auto')
        else:
            fig = self.fig(df, **fig_arg)
        layout_arg = self.__get_layout_arg(df, fig_arg)
        layout_arg.update(self.base_layout)
        fig.update_layout(layout_arg)

        return fig

from os.path import join

from yaml import load, FullLoader

from pandas import (
    read_parquet,
    to_datetime,
    DataFrame, 
    concat,
    read_csv
)

VAR_NM_TO_REF_TYPE = {
    'id':'string',
    'creation_dt':'datetime69[ns]',
    'msg':'string',
    'author_nm':'string',
    'file_nm':'string',
    'n_code_lines_inserted':'uint32',
    'n_code_lines_deleted':'uint32',
    'commit_id':'string',
    'ext':'string',
    'is_src':'bool',
    'is_test':'bool',
    'module_nm':'string',
    'component_nm':'string'
}

DATA_PATH = './data'
CONFIG_PATH = './config'



def get_parsed_git_log(codebase_nm:str, log_level:str) -> DataFrame:
    
    file_path = join(DATA_PATH, '%s_raw_%s.csv' % (codebase_nm, log_level))
    return read_csv(file_path)

def save_as_parquet(df:DataFrame, codebase_nm:str, log_level:str) -> None:

    file_path = join(DATA_PATH, '%s_clean_%s.parquet' % (codebase_nm, log_level))
    df.to_parquet(file_path, engine='pyarrow', version="2.4")


def read(codebase_nm:str, log_level:str) -> DataFrame:

    file_path = join(DATA_PATH, '%s_clean_%s.parquet' % (codebase_nm, log_level))
    df = read_parquet(file_path, engine='pyarrow')
    return df.set_index('creation_dt')


def load_config(scope_nm):

    file_path = join(CONFIG_PATH, '%s.yaml' % scope_nm)

    with open(file_path, 'r') as f:
        config = load(f, Loader=FullLoader)

    return config


def add_agg_column_on_id(df_commits, df_commits_files, aggfunc, agg_var_nm):

    return df_commits.merge(
        (
            df_commits_files
            .groupby('commit_id')
            [agg_var_nm]
            .agg(aggfunc)
            .reset_index()
            .rename(columns={'commit_id':'id'})
        ),
        on = 'id',
        how = 'left',
        validate = '1:1'
    ).fillna(0)

def denormalize_cols_on_id(df_commits_files, df_commits, col_nms):

    return (
        df_commits_files
        .merge(
            df_commits[['id'] + col_nms],
            left_on = 'commit_id',
            right_on = 'id',
            how = 'left',
            validate='m:1'
        )
        .drop(columns='id')
    )

def update_with_ref_types(df):

    for col_nm in df.columns:

        if 'dt' in col_nm:
            df[col_nm] = to_datetime(df[col_nm], utc=True)
        else:
            df[col_nm] = df[col_nm].astype(VAR_NM_TO_REF_TYPE[col_nm])
    

    return df


def fix_new_to_newest(dfx):

    return (
        dfx
        .drop_duplicates()
        .merge(
            dfx,
            left_on='new',
            right_on='old',
            how='left'
        )
        .drop(columns='old_y')
        .rename(columns={'old_x':'old', 'new_x':'old_new', 'new_y':'new'})
        .assign(new = lambda dfy: dfy.new.fillna(dfy.old_new))
        [['old', 'new']]
    )

def handle_root_files(dfx):

    root_file_filter = dfx.root_file == False

    if root_file_filter.sum() == 0:
        return dfx.drop(columns='root_file')
    
    dfx.loc[root_file_filter, 'old'] = dfx.loc[root_file_filter, 'prefix']
    dfx.loc[root_file_filter, 'prefix'] = ""

    return dfx.drop(columns='root_file')


def handle_file_renaming(df_commits_files):

    regex_rename = r'([A-z\./0-9\-_]*){{0,1}([A-z\./0-9\-_]*) => ([A-z\./0-9\-_]*)}{0,1}([A-z\./0-9\-_]*)'

    filter_renaming_file = df_commits_files.file_nm.str.contains(' => ')

    if filter_renaming_file.sum() == 0:
        return df_commits_files

    mapping = (
        df_commits_files
        .loc[filter_renaming_file]
        .pipe(lambda dfx: (
            dfx
            .file_nm.str.extract(regex_rename)
            .set_axis(['prefix', 'old', 'new', 'suffix'], axis=1)
            .assign(root_file = lambda _: (
                dfx
                .file_nm.str.split(' => ', expand=True).iloc[:,0]
                .str.contains('/')
            ))
        ))
        .pipe(handle_root_files)
        .assign(
            old = lambda dfx: dfx.prefix + dfx.old + dfx.suffix,
            new = lambda dfx: dfx.prefix + dfx.new + dfx.suffix,
        )
        [['old', 'new']]
        .assign(old = lambda dfx: dfx.old.str.replace('//', '/', regex=True))
        .assign(new = lambda dfx: dfx.new.str.replace('//', '/', regex=True))
    )

    df_commits_files.loc[mapping.index, 'file_nm'] = mapping.new.values

    mapping = fix_new_to_newest(mapping)

    df_commits_files['file_nm'] = df_commits_files.file_nm.replace(
        {v[0]:v[1] for _, v in mapping.iterrows()}
        )

    return df_commits_files

def get_n_code_lines_only(df_commits_files):

    for action_nm in ['inserted', 'deleted']:

        n_all_lines_action_nm = 'n_lines_%s' % action_nm
        n_code_lines_action_nm = 'n_code_lines_%s' % action_nm

        df_commits_files[n_code_lines_action_nm] = (
            df_commits_files[n_all_lines_action_nm].where(
                df_commits_files.ext != 'other', 0
            )
        )
        df_commits_files.drop(columns=n_all_lines_action_nm, inplace=True)

    return df_commits_files

class AuthorNameGrouper:

    # H: there always the fnm lnm format and is represented for all the authors

    _REGEX_BASE_FORMAT = '([a-z\-]*) ([a-z\-]*)'
    _SUPPORTED_FORMATS = ['fnm lnm', 'fnm[0].lnm', 'fnm', 'fnm[0].lnm@domain.ext', 'fnm.lnm@domain.ext']

    def __init__(self) -> None:
        pass

    def remove_email_domain_ext(self, nms):

        return nms.str.split('@', expand=True).iloc[:,0]

    def fit(self, author_nms):

        author_nms = author_nms.str.lower()
        author_nms = self.remove_email_domain_ext(author_nms)

        unique_author_nms = (
                author_nms.str.extract(self._REGEX_BASE_FORMAT)
                .set_axis(['fnm', 'lnm'], axis=1)
        )

        unique_author_nms['fnm lnm'] = unique_author_nms.fnm + ' ' + unique_author_nms.lnm
        unique_author_nms['fnm[0].lnm'] = unique_author_nms.fnm.str.slice(0,1) + '.' + unique_author_nms.lnm
        unique_author_nms['fnm'] = unique_author_nms.fnm
        unique_author_nms['fnm.lnm'] = unique_author_nms.fnm + '.' + unique_author_nms.lnm

        author_nm_mapper = DataFrame()

        for nm_format in ['fnm[0].lnm', 'fnm', 'fnm.lnm']:
            author_nm_mapper = concat([
                (
                    unique_author_nms[['fnm lnm', nm_format]]
                    .set_axis(['target', 'source'], axis=1)
                ),
                author_nm_mapper
                ])

        self.mapper = {}
        for _, val in author_nm_mapper.iterrows():
            self.mapper[val['source']] = val['target']

    def transform(self, author_nms):

        author_nms = author_nms.str.lower()
        author_nms = self.remove_email_domain_ext(author_nms)

        return author_nms.replace(self.mapper)
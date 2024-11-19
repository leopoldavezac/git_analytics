from re import sub

class CommitFilesTagger:

    LANGS = ['py', 'php', 'cpp', 'cs', 'java', 'js', 'ts', 'csproj']

    def __init__(
        self,
        src_path,
        module_depth,
        component_nms=None,
        component_depth=None
        ):
                
        self.src_struct = {
            'path': src_path,
            'module_depth':module_depth,
            'component':{'depth':component_depth, 'nms':component_nms}
        }

        if self.src_struct['component']['nms'] is not None:
            self.src_struct['component_and_module_aligned'] = (
                self.src_struct['component']['depth'] == self.src_struct['module_depth']
            )
        else:
            self.src_struct['component_and_module_aligned'] = False

    def tag_file_ext(self, df):

        lang_regex = '\\.(%s)$' % '|'.join(self.LANGS)
        df['ext'] = df.file_path.str.extract(lang_regex) 
        df.ext.fillna('other', inplace=True)

        return df

    def tag_src_file(self, df) -> None:

        path = self.src_struct['path']
        path = sub('^\\./|^/', '', path) # cleanup path of special char

        if path == '.':
            df['is_src'] = True
        else:
            df['is_src'] = df.file_path.str.slice(
                0, len(path)
            ) == path

        return df


    def __get_component_nms_regex(self, component_struct):

        return '(%s)' % '|'.join(component_struct['nms'])


    def tag_component(self, df) -> None:

        component_struct = self.src_struct['component']
        component_nms_regex = self.__get_component_nms_regex(component_struct)

        df.loc[df['is_src'], 'component_nm'] = (
            df
            .loc[df['is_src']]
            .file_path.str.split('/', expand=True)
            .iloc[:,component_struct['depth']]
            .str.extract(component_nms_regex)
            .values
        )

        df.component_nm.fillna('other', inplace=True)

        return df
    

    def remove_component_nm_from_module_nm(self, df):

        component_nms_regex = self.__get_component_nms_regex(self.src_struct['component'])
        df.loc[df.is_src, 'module_nm'] = (
            df.loc[df.is_src]
            # remove component nm from module
            .module_nm.str.replace(component_nms_regex, '', regex=True)
            .str.replace('(\\.|_|-)$', '', regex=True)
            .values
        )

        return df


    def tag_module(self, df):

        df.loc[df.is_src, 'module_nm'] = (
            df.loc[df.is_src]
            # get module nm using file path
            .file_path.str.split('/', expand=True).iloc[:,self.src_struct['module_depth']]
            # remove extensions (case where module is at file level)
            .str.replace('(\\.%s)$' % '|\\.'.join(self.LANGS), '', regex=True)
            .values
        )

        if self.src_struct['component_and_module_aligned']:
            df = self.remove_component_nm_from_module_nm(df)

        return df   
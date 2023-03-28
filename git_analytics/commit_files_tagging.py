from re import sub

LANGS = ['py', 'php', 'cpp', 'cs', 'java', 'js', 'ts', 'csproj']

class CommitFilesTagger:

    def __init__(
        self,
        df,
        src_path,
        module_depth,
        component_nms,
        component_depth
        ) -> None:
        
        self.src_path = src_path
        self.df = df

        self.src_struct = {
            'path':src_path,
            'module_depth':module_depth,
            'component':{'depth':component_depth, 'nms':component_nms}
        }

        if self.src_struct['component']['nms'] is not None:
            self.src_struct['component_and_module_aligned'] = (
                self.src_struct['component']['depth'] == self.src_struct['module_depth']
            )
        else:
            self.src_struct['component_and_module_aligned'] = False

    def __tag_file_ext(self):

        lang_regex = '\\.(%s)$' % '|'.join(LANGS)
        self.df['ext'] = self.df.file_nm.str.extract(lang_regex) 
        self.df.ext.fillna('other', inplace=True)

    def __tag_type(self) -> None:

        path = self.src_struct['path']
        path = sub('^\\./|^/', '', path)
        
        self.df['is_src'] = self.df.file_nm.str.slice(
            0, len(path)
        ) == path

    def __get_component_nms_regex(self, component_struct):

        return '(%s)' % '|'.join(component_struct['nms'])

    def __tag_component(self) -> None:

        component_struct = getattr(self, 'src_struct')['component']
        component_depth = component_struct['depth']
        component_nms_regex = self.__get_component_nms_regex(component_struct)

        self.df.loc[self.df['is_src'], 'component_nm'] = (
            self.df
            .loc[self.df['is_src']]
            .file_nm
            .str.split('/', expand=True)
            .iloc[:,component_depth]
            .str.lower()
            .str.extract(component_nms_regex)
            .values
        )

        self.df.component_nm.fillna('other', inplace=True)

    def __tag_module(self):

        repo_struct = getattr(self, 'src_struct')

        self.df.loc[self.df.is_src, 'module_nm'] = (
            self.df
            .loc[self.df.is_src]
            .file_nm
            .str.split('/', expand=True)
            .iloc[:,repo_struct['module_depth']]
            .str.lower()
            .str.replace('(\\.%s)$' % '|\\.'.join(LANGS), '', regex=True)
            .values
        )

        if repo_struct['component_and_module_aligned']:
            component_nms_regex = self.__get_component_nms_regex(repo_struct['component'])
            self.df.loc[self.df.is_src, 'module_nm'] = (
                self.df
                .loc[self.df.is_src]
                .module_nm
                .str.replace(component_nms_regex, '', regex=True)
                .str.replace('(\\.|_|-)$', '', regex=True)
                .values
            )
       
    def __tag(self):

        self.__tag_file_ext()
        self.__tag_type()
            
        if self.src_struct['component']['nms'] is not None:
            self.__tag_component()

        self.__tag_module()

        

    def get_tagged_files(self):

        try:
            self.df['module_nm']
        except KeyError:
            self.__tag()
        
        return self.df
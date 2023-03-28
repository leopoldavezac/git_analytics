from re import sub

LANGS = ['py', 'php', 'cpp', 'cs', 'java', 'js', 'ts']

class CommitFilesTagger:

    def __init__(
        self,
        df,
        repo_struct,
        ) -> None:
        
        self.src_struct = repo_struct['src']
        self.df = df

        if self.src_struct['component'] is not None:
            self.src_struct['component_and_module_aligned'] = (
                self.src_struct['component']['depth'] == self.src_struct['module_depth']
            )
        else:
            self.src_struct['component_and_module_aligned'] = False

        if 'test' in repo_struct.keys():
            self.test_struct = repo_struct['test']
            self.test_struct['component_and_module_aligned'] = (
                self.test_struct['component']['depth'] == self.test_struct['module_depth']
            )
        else:
            self.test_struct = None

    def __tag_file_ext(self):

        lang_regex = '\\.(%s)$' % '|'.join(LANGS)
        self.df['ext'] = self.df.file_nm.str.extract(lang_regex) 
        self.df.ext.fillna('other', inplace=True)

    def __tag_type(self, type_nm:str) -> None:

        path = getattr(self, '%s_struct' % type_nm)['path']
        path = sub('^\\./|^/', '', path)
        
        self.df['is_%s' % type_nm] = self.df.file_nm.str.slice(
            0, len(path)
        ) == path

    def __get_component_nms_regex(self, component_struct):

        return '(%s)' % '|'.join(component_struct['nms'])

    def __tag_component(self, type_nm:str) -> None:

        filter_type = self.df['is_%s' % type_nm]

        component_struct = getattr(self, '%s_struct' % type_nm)['component']
        component_depth = component_struct['depth']
        component_nms_regex = self.__get_component_nms_regex(component_struct)

        self.df.loc[filter_type, 'component_nm'] = (
            self.df
            .loc[filter_type]
            .file_nm
            .str.split('/', expand=True)
            .iloc[:,component_depth]
            .str.extract(component_nms_regex)
            .values
        )

        self.df.component_nm.fillna('other', inplace=True)

    def __tag_module(self, type_nm):

        repo_struct = getattr(self, '%s_struct' % type_nm)
        filter_type = self.df['is_%s' % type_nm]

        self.df.loc[filter_type, 'module_nm'] = (
            self.df
            .loc[filter_type]
            .file_nm
            .str.split('/', expand=True)
            .iloc[:,repo_struct['module_depth']]
            .str.replace('(\\.%s)$' % '|\\.'.join(LANGS), '', regex=True)
            .values
        )

        if repo_struct['component_and_module_aligned']:
            component_nms_regex = self.__get_component_nms_regex(repo_struct['component'])
            self.df.loc[filter_type, 'module_nm'] = (
                self.df
                .loc[filter_type]
                .module_nm
                .str.replace(component_nms_regex, '', regex=True)
                .str.replace('(\\.|_|-)$', '', regex=True)
                .values
            )
       
    def __tag(self):

        type_nms = ['src']
        type_nms += ['test'] if self.test_struct else []

        self.__tag_file_ext()

        for type_nm in type_nms:
            self.__tag_type(type_nm)
            
            if self.src_struct['component'] is not None:
                self.__tag_component(type_nm)

            self.__tag_module(type_nm)

        

    def get_tagged_files(self):

        try:
            self.df['module_nm']
        except KeyError:
            self.__tag()
        
        return self.df
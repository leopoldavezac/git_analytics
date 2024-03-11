from typing import Union

from os.path import join
import sys

from argparse import Namespace

from yaml import load, FullLoader
    
from argparse import ArgumentParser, Namespace
    
DEBUG_CODEBASE_NM = 'pydici'

class CLIArgumentParser:

    _CMD_NM_TO_DESC = {
        'parse_git':'parse the git log of a codebase into a tabular format.',
        'prep_data':'clean, format & enrich parsed log.',
        'visualize':'parse the git log of a codebase into a tabular format'
    }

    _ARGS_SPEC = {
       'codebase_nm':{
            'type':str,
            'nargs':None,
            'help':'identifier for the the codebase for which you wanna parse the git',
            'flags':[], #no flags -> arg is always required
            'arg_type_to_cmds':{
                'required':['parse_git', 'prep_data', 'visualize'],
                'option':[]
            },
        },
        'path_to_repo':{
            'type':str,
            'nargs':None,
            'help':'local path to the codebase repository',
            'flags':['--path_to_repo', '-pr'],
            'arg_type_to_cmds':{
                'required':['parse_git'],
                'option':['visualize']
            },
        },
        'src_path':{
            'type':str,
            'nargs':None,
            'help':'path to the source code from the root of the directory',
            'flags':['--src_path', '-sp'],
            'arg_type_to_cmds':{
                'required':['prep_data'],
                'option':['visualize']
            },
        },
        'module_depth':{
            'type':int,
            'nargs':None,
            'help':'depth of the modules from the the root of the source directory',
            'flags':['--module_depth', '-md'],
            'arg_type_to_cmds':{
                'required':['prep_data'],
                'option':['visualize']
            },
        },
        'component_nms':{
            'type':str,
            'nargs':'*',
            'help':'list describing the components.',
            'flags':['--component_nms', '-cn'],
            'arg_type_to_cmds':{
                'required':[],
                'option':['prep_data', 'visualize']
            },
        },
        'component_depth':{
            'type':int,
            'nargs':None,
            'help':'depth of the components from the the root of the source directory',
            'flags':['--component_depth', '-cd'],
            'arg_type_to_cmds':{
                'required':[],
                'option':['prep_data', 'visualize']
            },
        },
        'custom_stats':{
            'type':bool,
            'nargs':None,
            'help':'indicates whether a custom config for stats must be used (config/<codebase_nm>_stats.yaml)',
            'flags':['--custom_stats', '-cs'],
            'arg_type_to_cmds':{
                'required':[],
                'option':['visualize']
            },
        },
        'rerun':{
            'type':bool,
            'nargs':None,
            'help':'force rerun of predecessor(s) commands',
            'flags':['--rerun', '-r'],
            'arg_type_to_cmds':{
                'required':[],
                'option':['prep_data', 'visualize']
           },
        }
    }

    def __init__(self, cmd_nm:str) -> None:

        self.cmd_nm = cmd_nm

        cmd_desc = self._CMD_NM_TO_DESC[cmd_nm]
        self.parser = ArgumentParser(description=cmd_desc)
        
        for arg_nm, arg_spec in self._ARGS_SPEC.items():

                if cmd_nm in arg_spec['arg_type_to_cmds']['required']:

                    del arg_spec['arg_type_to_cmds'], arg_spec['flags']
                    self.parser.add_argument(arg_nm, **arg_spec)
                
                elif cmd_nm in arg_spec['arg_type_to_cmds']['option']:

                    del arg_spec['arg_type_to_cmds']
                    flags = arg_spec.pop('flags')
                    self.parser.add_argument(*flags, **arg_spec)

    def handle_debug_mode_args(self) -> None:

        # sys.args is updated to avoid conflict with flask arg parser
        if sys.argv[1] == 'run':
            sys.argv = [sys.argv[0], DEBUG_CODEBASE_NM]

    def parse_args(self) -> None:

        if self.cmd_nm == 'visualize':
            self.handle_debug_mode_args()

        self.args = self.parser.parse_args()
        
    def get_args(self) -> Namespace:
        return self.args

def get_args_from_cli(cmd_nm:str):

    parse_git_arg_parser = CLIArgumentParser(cmd_nm)
    parse_git_arg_parser.parse_args()

    return parse_git_arg_parser.get_args()


class ConfigManager(dict):

    _CMD_NM_TO_REQUIRED_PARAM_NMS = {
        'parse_git':['codebase_nm', 'path_to_repo'],
        'prep_data':['codebase_nm', 'src_path', 'module_depth'],
        'visualize':['codebase_nm']
    }

    codebase_nm = None
    path_to_repo = None
    src_path = None
    module_depth = None
    component_nms = None
    component_depth = None

    custom_stats = False

    rerun = False

    def set_config_with_cli_args(self, args:Namespace) -> None:

        args = vars(args)
        for arg_nm, arg_val in args.items():
            try:
                setattr(self, arg_nm, arg_val)
            except TypeError: #if arg_val is NoneType
                pass

    def check_completion_for(self, cmd_nm:str):

        required_param_nms = self._CMD_NM_TO_REQUIRED_PARAM_NMS[cmd_nm]
        for param_nm in required_param_nms:
            if getattr(self, param_nm) is None:
                return False
        
        return True

    def set_dashboard_specs_from_config(self) -> None:

        template_path = join('config', 'dashboard_specs.yaml')
        with open(template_path, 'r') as f:
            self.dashboard_specs = load(f, Loader=FullLoader)

    def __getitem__(self, param_nm) -> Union[str, int]:

        return getattr(self, param_nm)

def instanciate_config_manager(cmd_nm:str) -> ConfigManager:

    config_manager = ConfigManager()
    cli_args = get_args_from_cli(cmd_nm)
    config_manager.set_config_with_cli_args(cli_args)

    if cmd_nm == 'visualize':
        config_manager.set_dashboard_specs_from_config()

    return config_manager
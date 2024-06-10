"""
Purpose: General Tools
Author: Andy
"""


import os
import yaml
import shutil
from IPython import embed

def create_folder(path):

    if not os.path.exists(path):
        os.makedirs(path)

    else:
        print(f"path {path} already exists.")

def load_yaml(argument):

    return yaml.load(open(argument), Loader=yaml.FullLoader)


def parse_args(all_args):

    tags = ["--", "-"]

    all_args = all_args[1:]

    if len(all_args) % 2 != 0:
        print("Argument '%s' not defined" % all_args[-1])
        exit()

    results = {}

    i = 0
    while i < len(all_args) - 1:
        arg = all_args[i].lower()
        for current_tag in tags:
            if current_tag in arg:
                arg = arg.replace(current_tag, "")
        results[arg] = all_args[i + 1]
        i += 2
    
    return results


def load_config(sys_args):

    args = parse_args(sys_args)
    
    params = load_yaml(args["config"])
    for key, item in args.items():
        if key in params:
            params[key] = int(item)
    
    return params 

# launching jobs for copying data using rclone / s3 buckets
# to run this script: python3 launch_jobs.py -config ../../configs/config.yaml
#                     from general_3x3/kubernetes/gen_data
#                     using container kovaleskilab/meep_ml:launcher 

import os
import sys
import yaml
import time
import shutil
import atexit
import datetime
import subprocess
import pickle

from dateutil.tz import tzutc
from kubernetes import client, config
from jinja2 import Environment, FileSystemLoader

sys.path.append("../")
from k8s_support import exit_handler, create_folder, save_file, load_file, keep_val, parse_args, load_config



def launch_copydata(params):

    template = load_file(params['kube']['copy_job']['paths']['template'])
    tag = params['kube']['copy_job']['paths']['template'].split("/")[-1]
    folder = params['kube']['copy_job']['paths']['template'].replace("/%s" % tag, "")
    environment = Environment(loader = FileSystemLoader(folder))
    template = environment.get_template(tag)

    create_folder(params['kube']['datagen_job']['paths']['job_files'])

    vals = list(range(5,6))

    folder_names = [str(val).zfill(4) for val in vals]

    sim_nums = [str(val).zfill(5) for val in vals] 

    for folder_name, sim_num, val in zip(folder_names, sim_nums, vals):

        job_name = "%s-%s" % (params['kube']['copy_job']['kill_tag'], str(val).zfill(4))

        template_info = {"job_name": job_name, 
                         "folder_name": folder_name,
                         "sim_num": sim_num,
                        }

        filled_template = template.render(template_info)

        path_job = os.path.join(params['kube']['datagen_job']['paths']['job_files'], 
                                job_name + ".yaml") 

        save_file(path_job, filled_template)

        subprocess.run(["kubectl", "apply", "-f", path_job])


if __name__=="__main__":

    kill = False
    #kill = True

    params = load_config(sys.argv)

    if kill == False:

        launch_copydata(params)

    else:

        exit_handler(params,"copy_job")

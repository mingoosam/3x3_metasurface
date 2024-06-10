# This script launches jobs to generate the dataset. One job launches a single
# pod that runs a single simulation.

# To run: python3 launch_jobs.py -config ../../configs/config.yaml

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



def launch_datagen(params):

    template = load_file(params['kube']['datagen_job']['paths']['template'])
    tag = params['kube']['datagen_job']['paths']['template'].split("/")[-1]
    folder = params['kube']['datagen_job']['paths']['template'].replace("/%s" % tag, "")
    environment = Environment(loader = FileSystemLoader(folder))
    template = environment.get_template(tag)

    create_folder(params['kube']['datagen_job']['paths']['job_files'])

    counter = params['kube']['datagen_job']['start_group_id']
 
    current_group = []

    include_list = [704, 705, 826, 827, 828, 829, 830]

    while(counter < params['kube']['datagen_job']['num_sims']):

        if(len(current_group) < params['kube']['datagen_job']['num_parallel_ops']):

            num_to_launch = params['kube']['datagen_job']['num_parallel_ops'] - len(current_group)
            print(f"launching {num_to_launch} jobs with counter = {counter}")

            for i in range(counter, counter + num_to_launch):

                if counter in include_list:
                    job_name = "%s-%s" % (params['kube']['datagen_job']['kill_tag'], str(counter).zfill(4))

                    current_group.append(job_name)
                        
                    template_info = {"job_name": job_name, 
                                     "n_index": str(counter),
                                     "num_cpus": str(params['kube']['datagen_job']['num_cpus']),
                                     "num_mem_lim": str(params['kube']['datagen_job']['num_mem_lim']),
                                     "num_mem_req": str(params['kube']['datagen_job']['num_mem_req']),
                                     "pvc_name": str(params['kube']['pvc_name']),
                                     "path_out_sims": params['kube']['datagen_job']['paths']['simulations'],
                                     "path_image": params['kube']['datagen_job']['paths']['image'],
                                     "path_logs": params['kube']['datagen_job']['paths']['logs']}

                    filled_template = template.render(template_info)

                    path_job = os.path.join(params['kube']['datagen_job']['paths']['job_files'], job_name + ".yaml") 

                    save_file(path_job, filled_template)

                    subprocess.run(["kubectl", "apply", "-f", path_job])

                counter += 1 
        # -- Wait for a processes to finish

        else:

            k = 0
            check_time_min = 2
            wait_time_sec = 10

            while(len(current_group) == params['kube']['datagen_job']['num_parallel_ops']): 

                time.sleep(wait_time_sec)

                # --- Check progress every k minutes

                if(k % check_time_min == 0): 

                    # --- Gather kubernetes information

                    config.load_kube_config()
                    v1 = client.CoreV1Api()
                    pod_list = v1.list_namespaced_pod(namespace = params['kube']['namespace'], timeout_seconds = 300)
            
                    if(k == 0):
                        print()

                    pod_list = [item for item in pod_list.items if(params['kube']['datagen_job']['kill_tag'] in item.metadata.name)]

                    pod_names = [item.metadata.name for item in pod_list]
                    pod_statuses = [item.status.phase for item in pod_list]

                    # --- Remove pods that have finished. Jobs and pods share the same name.
                    pod_progress = [1 if(phase == "Succeeded") else 0 for phase in pod_statuses]
                    #pod_progress = [1 if(phase == "Succeeded" or phase == "Error" or phase == "Failed") else 0 for phase in pod_statuses]

                    remove_group = []

                    for i, (job_name, remove_flag) in enumerate(zip(current_group, pod_progress)):
                        
                        if(remove_flag==1):
                            remove_group.append(job_name)

                    if len(remove_group) > 0:

                        for job in remove_group:

                            print(f"removing job {job}...")
                            
                            subprocess.run(["kubectl", "delete", "job", job])
                            current_group.remove(job)
                            
                            time.sleep(wait_time_sec)

                    print("Log: Elapsed Time = %s minutes, Group Size = %s, Total (In Progress) = %s / %s" % ((wait_time_sec * (k + 1)) / 60, len(current_group), counter, params['kube']['datagen_job']['num_sims']))

                    if(sum(pod_progress) > 0):
                        print("\nUpdating...\n")
                        break                    

                k += 1
    
    print("\nData Generation Complete\n")


if __name__=="__main__":

    kill = False
    #kill = True

    params = load_config(sys.argv)

    if kill == False:

        launch_datagen(params)

    else:

        exit_handler(params,"datagen_job")

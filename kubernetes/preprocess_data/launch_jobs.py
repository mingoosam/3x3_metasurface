# /general_3x3/kubernetes/preprocess_data/launch_jobs.py

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

# Create: Response, Program Exit

def exit_handler(): # always run this script after this file ends.

    config.load_kube_config()   # python can see the kube config now. now we can run API commands.

    v1 = client.CoreV1Api()   # initializing a tool to do kube stuff.

    pod_list = v1.list_namespaced_pod(namespace = params["namespace"])    # get all pods currently running (1 pod generates a single meep sim) 

    current_group = [ele.metadata.owner_references[0].name for ele in pod_list.items if(params["kill_tag"] in ele.metadata.name)]    # getting the name of the pod

    current_group = list(set(current_group))    # remove any duplicates

    for job_name in current_group:
        subprocess.run(["kubectl", "delete", "job", job_name])    # delete the kube job (a.k.a. pod)

    print("\nCleaned up any jobs that include tag : %s\n" % params["kill_tag"])   

# Create: Results Folders

#def create_folder(path):
#
#    if(os.path.exists(path)):
#        shutil.rmtree(path)
#
#    os.makedirs(path)

# Save: Template File

def save_file(path, data):

    try:
        with open(path, "w") as data_file:

            data_file.write(data) 
            data_file.close()
            print(f"File saved at {path}.\n")

    except IOError as e:
        print(f"Error saving the file: {e}")
    except Exception as e:
        print(f"Unexpected error while saving file.")

# Load: Template File

def load_file(path):

    data_file = open(path, "r")
    
    info = ""

    for line in data_file:
        info += line

    data_file.close()

    return info

# Run: Parallelized Physics Simulatiion
#def keep_val(val):
#
#    last_digit = val % 10
#    return last_digit in [0, 1, 2]    

def run_generation(params):

    # Load job template

    template = load_file(params["path_template"])
    
    tag = params["path_template"].split("/")[-1]
    folder = params["path_template"].replace("/%s" % tag, "")
    environment = Environment(loader = FileSystemLoader(folder))
    template = environment.get_template(tag)

    # Launch Simulation Jobs

    #create_folder(params["path_sim_job_files"])

    # - Begin data generation

    print("\nLaunching Jobs for Buffer Study\n")
    counter = params['start_group_id']
 
    current_group = []

    while(counter < params['num_sims']):

        if(len(current_group) < params['num_parallel_ops']):

            num_to_launch = params['num_parallel_ops'] - len(current_group)

            for i in range(counter, counter + num_to_launch):
                #if keep_val(i) is True: # just a quick and dirty way to only run certain sims. don't use this for large scale datagen!
                if True:
                    #print(i)
                    job_name = "%s-%s" % (params['kill_tag'], str(counter).zfill(4))

                    current_group.append(job_name)
                    
                    template_info = {"job_name": job_name, 
                                     "n_index": str(counter),
                                     "num_cpus": str(params["num_cpus"]),
                                     "num_mem_lim": str(params["num_mem_lim"]),
                                     "num_mem_req": str(params["num_mem_req"]),
                                     "pvc_name": str(params["pvc_name"]),
                                     "path_out_sims": params["path_simulations"], "path_image": params["path_image"], "path_logs": params["path_logs"]}

                    filled_template = template.render(template_info)

                    path_job = os.path.join(params["path_sim_job_files"], job_name + ".yaml") 

                    if(sys.platform == "win32"):
                        path_job = path_job.replace("\\", "/").replace("/", "\\")

                    # --- Save simulation job file

                    save_file(path_job, filled_template)

                    # --- Launch simulation job

                    subprocess.run(["kubectl", "apply", "-f", path_job])

                counter += 1 
                print(f"counter = {counter}")
        # -- Wait for a processes to finish

        else:
            
            k = 0
            check_time_min = 2
            wait_time_sec = 60

            while(len(current_group) == params["num_parallel_ops"]): 

                time.sleep(wait_time_sec)

                # --- Check progress every n minutes

                if(k % check_time_min == 0): 

                    # --- Gather kubernetes information

                    config.load_kube_config()
                    v1 = client.CoreV1Api()
                    pod_list = v1.list_namespaced_pod(namespace = params["namespace"], timeout_seconds = 300)
            
                    if(k == 0):
                        print()

                    pod_list = [item for item in pod_list.items if(params["kill_tag"] in item.metadata.name)]

                    pod_names = [item.metadata.name for item in pod_list]
                    pod_statuses = [item.status.phase for item in pod_list]

                    # --- Remove pods that have finished. Jobs and pods share the same name.
                    print(pod_statuses)               
                    for phase in pod_statuses:
                        print(phase)
                    pod_progress = [1 if(phase == "Succeeded" or phase == "Error" or phase == "Failed") else 0 for phase in pod_statuses]
                    print(f"pod status update: {pod_statuses}")
                    print(f"pod progress update (remove flags): {pod_progress}")
                    for i, (job_name, remove_flag) in enumerate(zip(current_group, pod_progress)):
                        print(i, job_name,remove_flag)
                        if(remove_flag):
                            print()
                            #time.sleep(wait_time_sec)
                            subprocess.run(["kubectl", "delete", "job", job_name])
                            print(f"removed job {job_name}")
                            current_group.pop(i)
                            print()

                    print("Log: Elapsed Time = %s minutes, Group Size = %s, Total (In Progress) = %s / %s" % ((wait_time_sec * (k + 1)) / 60, len(current_group), counter, params["num_sims"]))

                    if(sum(pod_progress) > 0):
                        print("\nJobs Finished. Updating...\n")
                        break                    

                k += 1
    
        print("\nData Generation Complete\n")

# Validate: Configuration File

def load_config(argument):

    try:
        return yaml.load(open(argument), Loader = yaml.FullLoader) 

    except Exception as e:
        print("\nError: Loading YAML Configuration File") 
        print("\nSuggestion: Using YAML file? Check File For Errors\n")
        print(e)
        exit()        

# Parse: Command-line Arguments

def parse_args(all_args, tags = ["--", "-"]):

    all_args = all_args[1:]

    if(len(all_args) % 2 != 0):
        print("Argument '%s' not defined" % all_args[-1])
        exit()

    results = {}

    i = 0
    while(i < len(all_args) - 1):
        arg = all_args[i].lower()
        for current_tag in tags:
            if(current_tag in arg):
                arg = arg.replace(current_tag, "")                
        results[arg] = all_args[i + 1]
        i += 2

    return results

# Main: Load Configuration File
def preprocess_job(params):

    template = load_file(params["path_template"])
    
    tag = params["path_template"].split("/")[-1]
    folder = params["path_template"].replace("/%s" % tag, "")
    environment = Environment(loader = FileSystemLoader(folder))
    template = environment.get_template(tag)

    job_name = "%s" % (params['kill_tag'])

    template_info = {"job_name": job_name, 
                     "num_cpus": str(params["num_cpus"]),
                     "num_mem_lim": str(params["num_mem_lim"]),
                     "num_mem_req": str(params["num_mem_req"]),
                     "path_out_sims": params["path_simulations"], "path_image": params["path_image"], "path_logs": params["path_logs"]}

    filled_template = template.render(template_info)

    path_job = os.path.join(params["path_sim_job_files"], job_name + ".yaml") 

    if(sys.platform == "win32"):
        path_job = path_job.replace("\\", "/").replace("/", "\\")

    # --- Save simulation job file

    (path_job, filled_template)

    # --- Launch simulation job

    subprocess.run(["kubectl", "apply", "-f", path_job])


if __name__ == "__main__":

    args = parse_args(sys.argv)

    params = load_config(args["config"]) 
    #exit_handler();exit()
    # time is in seconds
    minutes = 45
    seconds = 60 * minutes
   
    template = load_file(params["path_template"])
    
    tag = params["path_template"].split("/")[-1]
    folder = params["path_template"].replace("/%s" % tag, "")
    environment = Environment(loader = FileSystemLoader(folder))
    template = environment.get_template(tag)

    ### charlie's code
    job_name = "%s" % (params['kill_tag'])

    template_info = {"job_name": job_name, 
                         "num_cpus": str(params["num_cpus"]),
                         "num_mem_lim": str(params["num_mem_lim"]),
                         "num_mem_req": str(params["num_mem_req"]),
                         "pvc_data": str(params["pvc_data"]),
                         "pvc_results": str(params["pvc_results"]),
                         #"path_out_sims": params["path_simulations"],
                         "path_image": params["path_image"],
                         "path_logs": params["path_logs"]}

    filled_template = template.render(template_info)

    path_job = os.path.join(params["path_sim_job_files"], job_name + ".yaml") 

    # --- Save simulation job file

    save_file(path_job, filled_template)

    ## end charlie's code

    subprocess.run(["kubectl", "apply", "-f", path_job])
  
    #atexit.register(exit_handler)  # this is how we clean up jobs. 

# collect volumes from h5py files

import h5py
import numpy as np
import torch
import pickle
import os
import re
import yaml


def get_volumes(params,meta_data,dft_data):

    loc_z_timedep_mon = 0.14500000000000013
    wl_list = params['monitor']['wavelength_list']
    #z_top = params['loc_z_timedep_mon']
    z_top = loc_z_timedep_mon
    z_bottom = z_top - 0.775
   
    x, y, z, w = meta_data
    z_loc1 = np.where(z > z_top)[0][0] + 1 
    z_loc2 = np.where(z > z_bottom)[0][0]

    volumes = {}
    for i, wl in enumerate(wl_list):

        # this gets complex field

        #x_field = np.asarray(dft_data[f'ex_{i}.r']) + 1j*np.asarray(dft_data[f'ex_{i}.i'])
        #y_field = np.asarray(dft_data[f'ey_{i}.r']) + 1j*np.asarray(dft_data[f'ey_{i}.i'])
        #z_field = np.asarray(dft_data[f'ez_{i}.r']) + 1j*np.asarray(dft_data[f'ez_{i}.i'])

        #x_vol = x_field[:,:,z_loc2:z_loc1]
        #y_vol = y_field[:,:,z_loc2:z_loc1]
        #z_vol = z_field[:,:,z_loc2:z_loc1]

        # this keeps real and imaginary components separate

        # x component
        x_real = np.asarray(dft_data[f'ex_{i}.r'])
        x_imag = np.asarray(dft_data[f'ex_{i}.i'])

        x_real_vol = x_real[:,:,z_loc2:z_loc1]
        x_imag_vol = x_imag[:,:,z_loc2:z_loc1]

        x_vol = [x_real_vol,x_imag_vol]
        x_vol = np.asarray(x_vol)

        # y component
        y_real = np.asarray(dft_data[f'ey_{i}.r'])
        y_imag = np.asarray(dft_data[f'ey_{i}.i'])

        y_real_vol = y_real[:,:,z_loc2:z_loc1]
        y_imag_vol = y_imag[:,:,z_loc2:z_loc1]

        y_vol = [y_real_vol,y_imag_vol]
        y_vol = np.asarray(y_vol)

        # z component
        z_real = np.asarray(dft_data[f'ez_{i}.r'])
        z_imag = np.asarray(dft_data[f'ez_{i}.i'])

        z_real_vol = z_real[:,:,z_loc2:z_loc1]
        z_imag_vol = z_imag[:,:,z_loc2:z_loc1]

        z_vol = [z_real_vol,z_imag_vol]
        z_vol = np.asarray(z_vol)
 
        volumes[wl] = [x_vol, y_vol, z_vol] 

    return volumes 

def dump_volumes(volumes,idx,dump_path):

    filename = str(idx).zfill(4)
    filename = filename + ".pkl"

    with open(os.path.join(dump_path,filename),'wb') as f:
        pickle.dump(volumes, f)
        print(f"{filename} dumped successfully.", flush=True)

def run(params):    

    if params['deployment_mode'] == 0: 
        path_data = params['paths']['data'] 
        path_dump = params['paths']['dump']
        exclude = ['volumes','reduced_data','pt','preprocessed_data','preprocessed_data_copy','volumes_temp']
    elif params['deployment_mode'] == 1:
        path_data = params['kube']['reduce_job']['paths']['data'] 
        dump_path = params['kube']['reduce_job']['paths']['dump']  # this is the dft-volumes pvc
        exclude = ['current_logs', 'slices', 'volumes']
        include = [val for val in range(0,1501)]
        include = [str(val).zfill(4) for val in include]
    else:
        raise NotImplementedError

    print(f"path_data = {path_data}")
    print(f"path_results = {path_dump}")

    print("Scanning directories in path_data...")

    with os.scandir(path_data) as entries:
         
        for entry in entries:

            if entry.is_dir() and entry.name not in exclude:
            #if entry.is_dir() and entry.name in include:
                             
                with os.scandir(entry.path) as files:
                     
                    for file_entry in files:

                        if file_entry.is_file():
                        
                            match = re.search(r'\d+',file_entry.name)
                            idx = int(match.group())
                            
                            if file_entry.name.endswith(".h5"):
                                try: 
                                   
                                    h5_path = os.path.join(path_data, entry, file_entry)
                                    h5_file = h5py.File(h5_path)

                                except:
        
                                    print("h5py File Error")

                            elif file_entry.name.endswith(".pkl") and 'metadata' in file_entry.name:
                                try:
                                    pkl_path = os.path.join(path_data, entry, file_entry)
                                    print("pickle path:")
                                    print(pkl_path)
                                    pkl_file = pickle.load(open(pkl_path, "rb"))
                            
                                except:
                                    print("pickle error")
                    volumes = get_volumes(params,pkl_file,h5_file)
                    dump_volumes(volumes,idx,path_dump)

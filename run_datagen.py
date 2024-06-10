import os
import yaml
import pickle
import meep as mp
import numpy as np
import time
import h5py

from meep_utils import field_monitors, simulation

from utils.general import create_folder
from utils.meep_helpers import get_z_location, mod_dft_fields, get_slice_from_metadata, get_vis


def run(params):

    idx = params['idx'] 
    if idx == None:
        err_message = "Need to pass -idx {int value} as command line argument."
        raise NotImplementedError(err_message)

    path_library = params['paths']['library']

    if params['deployment_mode'] == 0:
        path_data = params['paths']['data']
    elif params['deployment_mode'] == 1:
        path_data = params['kube']['datagen_job']['paths']['data']
    else:
        raise NotImplementedError

    folder_name = f"{str(idx).zfill(4)}"
    create_folder(os.path.join(path_data, folder_name))

    #subfolder_name = "slices"
    #create_folder(os.path.join(path_data, subfolder_name))

    ## folder for dumping metadata (.pkl file) and dft data (.h5 file)
    path_data = os.path.join(path_data, folder_name)
    
    print("loading in neighbors library...")
    neighbors_library = pickle.load(open(path_library,"rb"))
       
    print(f"assigning neighborhood for idx {idx}...")
    radii = list(neighbors_library[idx])
    radii = np.array(radii).reshape(3,3)
    radii = np.flip(radii,axis=0).flatten()
    radii = list(radii)
   
    # This is how we are arranging the raddi:
 
    #6 7 8  -->  0 1 2
    #3 4 5       3 4 5
    #0 1 2       6 7 8

    #radii = [0.18664, 0.09511, 0.13333,
    #         0.16552, 0.19670, 0.13635,
    #         0.20876, 0.10517, 0.09009]
    #radii = [0.20876, 0.10517, 0.09009, 0.16552, 0.19670, 0.13635, 0.18664, 0.09511, 0.13333]
    
    print("building sim...")
    sim, dft_obj, flux_obj, params = simulation.build_sim(params, radii = radii)

    start_time = time.time()
    
    #sim = get_vis(params,until,sim,path_results,idx,animation=True,image=True)

    ## Do not run this if sim = get_vis() is called. (You'll extraneously run the simulation twice)
    sim.run(until=params['simulation']['until'])
    
    meta_data = sim.get_array_metadata(dft_cell = dft_obj)
    print("dumping metadata...")
    pickle.dump(meta_data, open(os.path.join(path_data, 'metadata_{}.pkl'.format(str(idx).zfill(5))), 'wb'))

    eps_data = sim.get_epsilon()
    print("dumping eps data...")
    pickle.dump(eps_data, open(os.path.join(path_data, 'epsdata_{}.pkl'.format(str(idx).zfill(5))), 'wb'))

    # this outputs a 3GB file   
    print("outputting full dft volume...")
    sim.output_dft(dft_obj, os.path.join(path_data, 'dft_{}'.format(str(idx).zfill(5))))


    ## Everything we need to train the surrogate model goes in the 'slices' folder ##
    ##-----------------------------------------------------------------------------##

    #dft_fields = h5py.File(os.path.join(path_data,'dft_{}.h5'.format(str(idx).zfill(5))))
    #z_slice = get_slice_from_metadata(params,meta_data,dft_fields)
    #z_slice = mod_dft_fields(params,dft_fields,eps_data)

    #training_data = {'slices': z_slice,
    #                 'radii':  radii,
    #                }                  
    #print(f"dumping surrogate model training data to {subfolder_name}...")
    #filename = os.path.join(path_data, '../slices', f'{str(idx).zfill(5)}.pkl')
    #with open(filename,'wb') as f:
    #    pickle.dump(training_data, f)
 
    end_time = round((time.time() - start_time) / 60, 3)
    print(f"all done. elapsed time: {end_time} minutes.")




import numpy as np
import yaml
from IPython import embed
import pickle
import matplotlib.pyplot as plt

def get_random_radii(params):

    list_len = 9
    
    library = {} 
    library['std_dev'] = []
    library['percent_of_range'] = []
    library['radii'] = [] 

    rows, cols = 3, 3
   
    i = 0 
    _min = params['geometry']['radius_min']
    _max = params['geometry']['radius_max']
    
    while i < 40: 

        #initial_value = params['geometry']['radius_max'] / 2 
        initial_value = np.random.uniform(0.075, 0.250)
        std_dev = 0.0025 * (i + 1)
        library['std_dev'].append(std_dev)
        library['percent_of_range'].append((std_dev / (0.250-0.075)) * 100)

        for j in range(3):
            if j == 0:
                rad_list = []

            radii = [initial_value + np.random.normal(0, std_dev) for _ in range(9)]

            radii = np.clip(radii, _min, _max)
            
            # Ensure no duplicates in the sublist
            while len(set(radii)) < len(radii):
                radii = [initial_value + np.random.normal(0, std_dev) for _ in range(9)]
                radii = np.clip(radii, _min, _max)

            # Append the generated sublist to the list of lists
            rad_list.append(list(radii))
            
            if j == 2:
                library['radii'].append(rad_list)
                print(f"appended to library['radii']: list length = {len(rad_list)}")
        i += 1
         
    #pickle.dump(library, open("buffer_study_library.pkl", "wb"))
    return library

def visualize(library):

    std_dev = library['std_dev']
    percent_of_range = library['percent_of_range']
    radii = library['radii']
    
    #fig, ax = plt.subplots(2, int(len(radii[0])/2), figsize=(8,8))
    fig, ax = plt.subplots(1, int(len(radii)))
    #embed() 
    for i, (rad_list, sd) in enumerate(zip(radii,std_dev)):
        std_dev = np.std(rad_list, ddof=1)
        print(f"np calculated: {std_dev}, compare to {sd} - error = {np.abs(std_dev-sd)}") 
       
        ax[i] = plt.boxplot(rad_list)        
        
    plt.show()

def rad_inc_with_y(params):

    # max   max   max
    # 0.125 0.125 0.125
    # min   min   min

    list_len = 6
    
    library = {} 
    library['std_dev'] = []
    library['percent_of_range'] = []
    library['radii'] = [] 
                                                                                         
    rows, cols = 3, 3
                                                                                         
    i = 0 
    _min = params['geometry']['radius_min']
    _max = params['geometry']['radius_max']
    
    num_groups = 30
    while i < num_groups: 
    
        # fix this                                              
        initial_value = params['geometry']['radius_max'] / 2 # central row
        #std_dev = 0.0025 * (i + 1)
        #library['std_dev'].append(std_dev)
        #library['percent_of_range'].append((std_dev / (0.250-0.075)) * 100)

        epsilon = 0.1 # adjust this to change your window
                                                                                        
        for j in range(5):
            if j == 0:
                rad_list = []
           
            radii_mid = [initial_value for _ in range(3)] 

            # could make this increase deterministic: ((max - mean) / num_groups) = delta  -- let max = mean + delta, min = mean-delta
            #val = np.random.normal(0, std_dev)                                                                             
            delta = (_max*epsilon - initial_value) / num_groups 
            val = i * delta
            
            radii_min = [round(initial_value - val,5) for _ in range(3)]
            radii_max = [round(initial_value + val,5) for _ in range(3)]
            
            radii = [radii_max,radii_mid,radii_min] 
            radii = [item for sublist in radii for item in sublist]
            
            rad_list.append(list(radii))
            
            if j == 4: 
                library['radii'].append(rad_list)
                #print(f"appended to library['radii']: list length = {len(rad_list)}")
        i += 1
         
    #pickle.dump(library, open("buffer_study_inc_y.pkl", "wb"))
    return library



if __name__=="__main__":

    params = yaml.load(open("config.yaml", 'r'), Loader = yaml.FullLoader)

    #expected_val = params['geometry']['radius_max'] / 2
    #library = rad_inc_with_y(params)

    library = get_random_radii(params) 
    #visualize(library)
    #pickle.dump(library, open("buffer_study_random.pkl","wb"))
    embed()


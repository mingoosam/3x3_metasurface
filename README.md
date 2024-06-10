# 3x3_metasurface

This is the codebase for building the custom dataset used for the study presented in the publication, [Time-series neural networks to predict electromagnetic wave propagation](https://www.spiedigitallibrary.org/conference-proceedings-of-spie/13042/1304206/Time-series-neural-networks-to-predict-electromagnetic-wave-propagation/10.1117/12.3013488.full).

__________________________________


A library of 3x3 pillar radii between 75 nm and 250 nm is generated using [generate_radii.py](radii/generate_radii.py). This generates a file called `neighbors_library_allrandom.pkl`. This file stores a numpy array with len(5000). Each index contains a list of 9 radii. 

Running [main.py](main.py) allows the user to either generate data or reduce the data into volumes, as presented in the paper linked above.

1. Generate data. To run a single simulation:

   - Set the [config file](configs/config.yaml) parameter, `task` to 0.
   - Create an instance of the Docker image, [v3_lightning](https://hub.docker.com/layers/kovaleskilab/meep/v3_lightning/images/sha256-e550d12e2c85e095e8fd734eedba7104e9561e86e73aac545614323fda93efb2?context=repo).
   - From `/develop/code/3x3_metasurface`, run:
     ```
     mpirun --allow-run-as-root -np {num_cpu_cores} python3 main.py -config configs/config.yaml -idx {neighbors library index}
     ```

2. Reduce data.

   - Set the [config file](configs/config.yaml) parameter, `task` to 0.
   - Running the same Docker container in (1), from `/develop/code/3x3_metasurface`, run:
     ```
     python3 reduce_data.py
     ```

____________________________________
## Using Kubernetes

1. Generate data. To launch many simulations:

  - Set the [config file](configs/config.yaml) parameters.
    - `task` : 0
    - `deployment_mode` : 1
    - `kube.datagen_job.num_sims` : 1500
    - `kube.datagen_job.start_group_id` : 0
    - `kube.datagen_job.num_parallel_ops` : {your preference}
  - Running an instance of the Docker image, [kubernetes launcher](https://hub.docker.com/layers/kovaleskilab/meep_ml/launcher/images/sha256-464ec5f4310603229e96b5beae9355055e2fb2de2027539c3d6bef94b7b5a4f1?context=repo), navigate to `kubernetes/gen_data/` and run
    ```
    python3 launch_jobs.py
    ```
    
2. Reduce data.

  - Set the [config file](configs/config.yaml) parameters.
     - `task` : 1
     - `deployment_mode` : 1
  - From `kubernetes/reduce_data`, run:
     ```
     python3 launch_jobs.py
     ```
    

#!/bin/bash

source="nautilus:andys-bucket"
destination="/home/agkgd4/Documents/data/meep-dataset-v2"

for i in {2..20}; do

    folder=$(printf "%04d" $i)
    file=$(printf "%05d" $i)

    source_path="${source}/${folder}/epsdata_${file}.pkl"
    destination_path="${destination}/${folder}/"

    echo $source_path
    echo $destination_path
    rclone copy --progress --copy-links "$source_path" "$destination_path"    
done

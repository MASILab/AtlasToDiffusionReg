#!/bin/bash

#name that you wll give the rest of the files based on the diffusion input names
    #there must be a better way to do this. Perhaps put the variable name into a variable outside the script, receiving it as input in some way?
name=$(find /INPUTS -type f | grep .bval | head -n 1 | awk -F '/' '{print $(NF)}' | sed -E 's/(.*)\.bval/\1/g')

#inputs/intermediates
epi_transform="/OUTPUTS/${name}%ANTS_t1tob0.txt"
#epi_inv_transform="/OUTPUTS/${name}%ANTS_b0tot1.txt"

t1_to_template_affine="/OUTPUTS/${name}%0GenericAffine.mat"
t1_to_template_invwarp="/OUTPUTS/${name}%1InverseWarp.nii.gz"

b0="/OUTPUTS/${name}%b0.nii.gz"

#outputs are in the loop

echo "Applying transforms to atlases..."
#have to apply the transforms to each atlas/labelmap that is input
find /INPUTS -type f | grep -i 'atlas' | while IFS= read -r line; do
    atlas_name=$(echo $line | awk -F '/' '{print $(NF)}' | sed -E 's/\.nii.*//g')
    #applies the 3 transforms in sequence
    antsApplyTransforms -d 3 -i ${line} -r ${b0} -n NearestNeighbor \
    -t ${epi_transform} -t [${t1_to_template_affine},1] -t ${t1_to_template_invwarp} -o /OUTPUTS/${name}%${atlas_name}.nii.gz
done

echo "**********************************"
echo "FINISHED ALL REGISTRATIONS"
echo "**********************************"


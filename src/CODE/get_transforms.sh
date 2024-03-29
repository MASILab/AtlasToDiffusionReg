#!/bin/bash

#name that you wll give the rest of the files based on the diffusion input names
name=$(find /INPUTS -type f | grep .bval | head -n 1 | awk -F '/' '{print $(NF)}' | sed -E 's/(.*)\.bval/\1/g')


#INPUTS
t1_template=/INPUTS/template.nii.gz #input template --> should this already exist in the singularity? That way it doesnt need to be in every input
    #just bind it in every time as: -B /path/to/atlas:/INPUTS/template.nii.gz
t1=/INPUTS/t1.nii.gz
bval=/INPUTS/${name}.bval
bvec=/INPUTS/${name}.bvec
dwi=/INPUTS/${name}.nii.gz

#INTERMEDIATES
b0="/OUTPUTS/${name}%b0.nii.gz"
t1_bet="/OUTPUTS/${name}%t1BET.nii.gz"

#OUTPUTS
fsl_transform="/OUTPUTS/${name}%FSL_t1tob0.mat"
fsl_inv_transform="/OUTPUTS/${name}%FSL_b0tot1"
converted_transform="/OUTPUTS/${name}%ANTS_t1tob0.txt"
converted_inv_transform="/OUTPUTS/${name}%ANTS_b0tot1.txt"

#prefix for all the files you will be creating
name_prefix="/OUTPUTS/${name}%"

#get the brain extraction for the t1
if [[ $(find /INPUTS/T1_seg.nii.gz) ]]; then  #if the SLANT segmentation is in input
    echo "Found T1 segmentation in the inputs. Using that to create a mask.."
    t1_mask="/OUTPUTS/${name}%t1_mask.nii.gz"
    echo "Creating a mask for brain extraction..."
    fslmaths /INPUTS/T1_seg.nii.gz -div /INPUTS/T1_seg.nii.gz ${t1_mask}
    echo "Done creating the structural mask."
    echo "Using the mask to do brain extraction..."
    fslmaths ${t1} -mul ${t1_mask} ${t1_bet}
else                                            #SLANT segmentation is not in the input
    echo "Did not find T1 segmentation in the INPUTS. Using bet for brain extraction."
    echo "Performing Brain Extraction..."
    bet ${t1} ${t1_bet} -R -f 0.5 -g 0 -m
fi
echo "Finished brain extraction."

#gets the affine and nonlinear transforms from template to subject T1 space
echo "Computing transform of template to t1..."
antsRegistrationSyN.sh -d 3 -f ${t1_template} -m ${t1} -o ${name_prefix}
#extract b0
echo "Performing b0 Extraction..."
dwiextract ${dwi} -fslgrad ${bvec} ${bval} - -bzero | mrmath - mean ${b0} -axis 3

#get the FSL transform from b0 to T1 space
echo "Computing transform of t1 to b0..."
epi_reg --epi=${b0} --t1=${t1} --t1brain=${t1_bet} --out=${fsl_inv_transform}
#get the FSL transform from T1 to diffusion space
convert_xfm -omat ${fsl_transform} -inverse ${fsl_inv_transform}.mat
#convert the FSL transforms into ants format                            #-ref b0 -src T1 t1tob0.mat
echo "Converting FSL transforms to ants format..."
c3d_affine_tool -ref ${b0} -src ${t1} ${fsl_transform} -fsl2ras -oitk ${converted_transform}
c3d_affine_tool -ref ${t1} -src ${b0} ${fsl_inv_transform}.mat -fsl2ras -oitk ${converted_inv_transform}

echo "**********************************"
echo "FINISHED COMPUTING ALL TRANSFORMS"
echo "**********************************"
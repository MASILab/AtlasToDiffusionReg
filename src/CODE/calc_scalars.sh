#!/bin/bash


name=$(find /INPUTS -type f | grep .bval | head -n 1 | awk -F '/' '{print $(NF)}' | sed -E 's/(.*)\.bval/\1/g')

#inputs/intermediates
dwi_firstshell="/OUTPUTS/${name}%firstshell.nii.gz"
bval="/OUTPUTS/${name}%firstshell.bval"
bvec="/OUTPUTS/${name}%firstshell.bvec"
b0="/OUTPUTS/${name}%b0.nii.gz"

#outputs
mask_name="/OUTPUTS/${name}%"
mask="/OUTPUTS/${name}%_mask.nii.gz"
tensors="/OUTPUTS/${name}%tensor.nii.gz"
#predicted_signal: reconst="/OUTPUTS/${name}%reconst_from_tensor.nii.gz"
fa="/OUTPUTS/${name}%fa.nii.gz"
md="/OUTPUTS/${name}%md.nii.gz"
rd="/OUTPUTS/${name}%rd.nii.gz"
ad="/OUTPUTS/${name}%ad.nii.gz"

echo "Calculating the dwi mask..."
#calculate the brain mask
bet ${b0} ${mask_name} -f 0.25 -m -n -R

echo "Calculating the tensors..."
#calculate tensors and reconstruction from dwi, mask, bvec, bval
dwi2tensor ${dwi_firstshell} ${tensors} -fslgrad ${bvec} ${bval} -mask ${mask} #-predicted_signal tensor_test/dwmri_reconst_from_tensor.nii.gz

#now, use the tensors, dwi, and mask to compute scalars
echo "Calculating the scalars..."
#FA
tensor2metric ${tensors} -fa ${fa} -mask ${mask}
#MD
tensor2metric ${tensors} -adc ${md} -mask ${mask}
#RD
tensor2metric ${tensors} -rd ${rd} -mask ${mask}
#AD
tensor2metric ${tensors} -ad ${ad} -mask ${mask}

echo "****************************************"
echo "FINISHED CALCULATING DIFFUSION SCALARS"
echo "****************************************"

#ONlY 1500 AND BELOW FOR THE DWI
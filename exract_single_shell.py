THRESHOLD = 1500

import numpy as np
import nibabel as nib
from pathlib import Path
import re


file_name = [x for x in Path("/INPUTS").glob('*.bval*')][0].name
name_match = re.search("^(.*).bval$", file_name)
name = name_match.group(1)

#inputs
dwi = Path("/INPUTS/{}.nii.gz".format(name))
bval_file = Path("/INPUTS/{}.bval".format(name))
#bvec_file = Path("/INPUTS/{}.bvec".format(name))

#output
output_file = Path("/OUTPUTS/{}%firstshell.nii.gz")

#dwi = Path("/home-local/kimm58/AtlasToDiffusionReg/data/BLSA_test/inputs/dwmri.nii.gz")
#bval_file = Path("/home-local/kimm58/AtlasToDiffusionReg/data/BLSA_test/inputs/dwmri.bval")
#bvec_file = Path("/home-local/kimm58/AtlasToDiffusionReg/data/BLSA_test/inputs/dwmri.bvec")

#must extract the volumes less than 1500 bval from the diffusion image
nii = nib.load(dwi)
img = nii.get_fdata()

bval = np.loadtxt(bval_file)
#bvec = np.loadtxt(bvec_file)

#extract the volumes
new_bval = bval[bval<THRESHOLD]
new_bvec = bvec[:, bval<THRESHOLD]
print("Extracting volumes from {} with bvals less than 1500...".format(dwi.name))
new_img = img[:, :, :, bval<THRESHOLD]

#save the extracted volumes
nii2 = nib.Nifti1Image(new_img, nii.affine)
print("Saving extracted volumes to {}...".format(output_file))
nib.save(nii2, output_file)

print("**********************************")
print("FINISHED EXTRACTING FIRST SHELL VOLUMES")
print("*********************************")


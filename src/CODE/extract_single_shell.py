THRESHOLD = 1500

import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
import re


def get_new_bvecs(new_bvec):
    bdirs = []      #bdirs will be the new bvec list
    for x in new_bvec:
        r = x[0]
        l = []
        for y in r:
            l.append(str(y))
        bdirs.append(l)

    #nbdirs will be the new bvec list with the zeroes as '0' not '0.0'
    nbdirs = []
    for x in bdirs:
        a = []
        for d in x:
                f = float(d)
                if f == 0:
                        a.append('0')
                else:
                        a.append(str(f))
        nbdirs.append(a)
    return nbdirs

#at the end of EVERY value (even terminal ones) there are 2 spaces
    #at the end of EVERY line, there is a newline
def get_new_bvec_txt(new_bvec):
    bvectxt = ''
    for line in new_bvec:
        s = "  ".join(line)
        s = s + '\n'
        bvectxt = bvectxt + s
    return bvectxt

def get_bval_str(new_bval):
    e = []
    for x in new_bval:
        f = float(x)
        if f == 0:
                e.append('0')
        else:
                e.append(str(f))
    s = ' '.join(e)
    s = s + '\n'
    return s

file_name = [x for x in Path("/INPUTS").glob('*.bval*')][0].name
name_match = re.search("^(.*).bval$", file_name)
name = name_match.group(1)

#inputs
dwi = Path("/INPUTS/{}.nii.gz".format(name))
bval_file = Path("/INPUTS/{}.bval".format(name))
bvec_file = Path("/INPUTS/{}.bvec".format(name))

#outputs
output_file = Path("/OUTPUTS/{}%firstshell.nii.gz".format(name))
bval_new_file = Path("/OUTPUTS/{}%firstshell.bval".format(name))
bvec_new_file = Path("/OUTPUTS/{}%firstshell.bvec".format(name))

#dwi = Path("/home-local/kimm58/AtlasToDiffusionReg/data/BLSA_test/inputs/dwmri.nii.gz")
#bval_file = Path("/home-local/kimm58/AtlasToDiffusionReg/data/BLSA_test/inputs/dwmri.bval")
#bvec_file = Path("/home-local/kimm58/AtlasToDiffusionReg/data/BLSA_test/inputs/dwmri.bvec")

#must extract the volumes less than 1500 bval from the diffusion image
nii = nib.load(dwi)
img = nii.get_fdata()

bval = np.loadtxt(bval_file)
bvec = np.loadtxt(bvec_file)

#get indices of volumes to extract
indices = np.where(bval<THRESHOLD)

#extract the volumes
new_bval = bval[bval<THRESHOLD]

dirs = []
for x in bvec:
    new_dir = np.take(x, indices)
    dirs.append(new_dir)
new_bvec = np.stack(dirs, axis=0)

new_bvec = get_new_bvecs(new_bvec)      #gets bvecs into a list of lists of strings
bvectxt = get_new_bvec_txt(new_bvec)
#now, bvectxt can be output to a text file
    #must do the same for bvals
bvaltxt= get_bval_str(new_bval)


#new_bvec = bvec[:, bval<THRESHOLD]
print("Extracting volumes from {} with bvals less than 1500...".format(dwi.name))
new_img = img[:, :, :, bval<THRESHOLD]

#save the extracted volumes
nii2 = nib.Nifti1Image(new_img, nii.affine)
print("Saving extracted volumes to {}...".format(output_file))
nib.save(nii2, output_file)

#write the new bvals/bvecs
print("Saving new bvec and bval files...")
with open(bvec_new_file, 'w') as f:
    f.write(bvectxt)
with open(bval_new_file, 'w') as f:
    f.write(bvaltxt)

print("**********************************")
print("FINISHED EXTRACTING FIRST SHELL VOLUMES")
print("*********************************")


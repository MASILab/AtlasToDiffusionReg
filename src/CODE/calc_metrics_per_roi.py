import nibabel as nib
from pathlib import Path
import numpy as np
import pandas as pd
import re
from tqdm import tqdm

#ATLASES need to be called:
    #"Atlas_<NAME>.nii.gz" where <NAME> is the name of the atlas
#Corresponding labels need to be called:
    #"Labels_<NAME>.txt"


def create_atlas_dictionary(path_to_atlas_desc_file):
    atlas_doc = np.loadtxt(path_to_atlas_desc_file, dtype=str, delimiter='\n')
    atlas_dict = dict()
    for label in atlas_doc[1:]:   #assuming that the labelmap desciption must have a header
        splits = label.split(" ")
        atlas_dict[int(splits[0])] = splits[1]
    return atlas_dict

#get list of atlas names from the inputs folder
def get_atlas_names(path):
    atlases = []
    for f in [x.name for x in path.glob('*')]:
        name_match = re.search("^(Atlas.*).nii.*$", f, re.IGNORECASE)
        if name_match:
            atlases.append(name_match.group(1))
    return atlases

#get list of label names from the inputs folder
def get_label_file_names(path, atlas_names):
    labels = []
    for atlas_name in atlas_names:
        atlas_match = re.search("^Atlas_(.*)$",atlas_name, re.IGNORECASE)
        atlas = atlas_match.group(1)
        label_match = re.compile("^(Labels.*{}.txt)$".format(atlas))
        for f in [x.name for x in path.glob('*')]:
            #print(f)
            mat = label_match.match(f)
            #print(mat)
            if mat:
                labels.append(f)
    return labels

def calc_scalars(atlas_name, roi, key, label, df, scalars, scalar_prefixes, idx):
    row = [atlas_name, roi]
    numPixels = np.sum(label == key)
    if numPixels == 0:
        row = row + [np.nan]*len(scalars)*2   #*2 for mean and std dev
        df.loc[idx] = row
        return
    for scalar,scalar_prefix in zip(scalars, scalar_prefixes):
        if np.sum(np.isnan(scalar[label == key])) > 0.5 * numPixels:
            row.append(np.nan) #mean
            row.append(np.nan)  #std
        else:
            row.append(np.nanmean(scalar[label == key]))
            row.append(np.nanstd(scalar[label == key]))
    df.loc[idx] = row
    return

#################################################################################

#inp = Path("/home-local/kimm58/AtlasToDiffusionReg/data/inputs")
#out = Path("/home-local/kimm58/AtlasToDiffusionReg/data/outputs")
inp = Path("/INPUTS/")
out = Path("/OUTPUTS/")
file_name = [x for x in inp.glob('*.bval*')][0].name
name_match = re.search("^(.*).bval$", file_name)
name = name_match.group(1)

#inputs/intermediates
fa = out/("{}%{}.nii.gz".format(name, 'fa'))
md = out/("{}%{}.nii.gz".format(name, 'md'))
ad = out/("{}%{}.nii.gz".format(name, 'ad'))
rd = out/("{}%{}.nii.gz".format(name, 'rd'))

#GAMEPLAN
    #loop through atlases
        #loop through each region of each atlas
            #loop through each scalar
                #in this loop, append a new row to the dataframe

#preloading all the scalar files
scalar_files = [fa, md, ad, rd]
scalar_niftis = [nib.load(x) for x in scalar_files]
scalars = [x.get_fdata() for x in scalar_niftis]
scalar_prefixes = ['fa','md','ad','rd']

#setting up df
cols = ["Atlas Name", "ROI NAME"]
for p in scalar_prefixes:
    cols.append(p+'-mean')
    cols.append(p+'-std')
df = pd.DataFrame(columns=[cols])

#get atlas names
atlas_names = get_atlas_names(inp)
#get the atlases in a list
atlases = []
atlas_dicts = []
for atlas_name in atlas_names:
    #labelmap/atlas
    label_file = out/("{}%{}.nii.gz".format(name, atlas_name))
    label_nifti = nib.load(label_file)
    atlases.append(label_nifti)
    #dictionary for the labels

#set up atlas dictionaries
label_names = get_label_file_names(inp, atlas_names)
atlas_dicts = []
for label_name in label_names:
    dictionary_file = inp/(label_name)
    atlas_dict = create_atlas_dictionary(dictionary_file)
    atlas_dicts.append(atlas_dict)

#actually calculating the rois
idx =0
for atlas_name,label_nifti,atlas_dict in zip(atlas_names, atlases, atlas_dicts):
    label = label_nifti.get_fdata()
    print("Calculating mean and std for diffusion scalars of {}....".format(atlas_name))
    for key,roi in tqdm(atlas_dict.items()):
        calc_scalars(atlas_name, roi, key, label, df, scalars, scalar_prefixes, idx)
        idx += 1

print("Finished calculating mean and std for all ROIs of all atlases")
print("Outputting csv...")
df.to_csv(out/("{}%diffusionmetrics.csv".format(name)), index=False)

print("*********************************")
print("FINISHED CREATING CSV")
print("*********************************")


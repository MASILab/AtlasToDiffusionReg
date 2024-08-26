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
#Brain segmentation must be called "T1_seg.nii.gz" (if there is one)
    #the label file must be called "T1_seg.txt"

#turns the atlas label files into dictionaries
def create_atlas_dictionary(path_to_atlas_desc_file):
    atlas_doc = np.loadtxt(path_to_atlas_desc_file, dtype=str) #removed delimiter='\n'
    atlas_dict = dict()
    for label in atlas_doc[1:]:   #assuming that the labelmap desciption must have a header
        #splits = label.split(" ")
        atlas_dict[int(label[0])] = label[1] #changed with delimiter='\n' removal
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

def calc_volume(key, label, label_nifti):
    (sx,sy,sz) = label_nifti.header.get_zooms()[:3]    #get the voxel dimensions
    if np.sum(label == key) == 0:
        return np.nan                               #returns nan if the volume is zero
    return np.sum(label == key) * sx * sy * sz      #this will give the volume of the ROI


def calc_scalars(atlas_name, roi, key, label, df, scalars, scalar_prefixes, idx, label_nifti, mask):
    row = [atlas_name, roi]
    numPixels = np.sum(label == key)
    voxels_mask = np.logical_and(label == key, mask)
    #get the voxels we want to consider for calculating scalars
    if numPixels == 0:
        row = row + [np.nan]*(len(scalars)*3+1)   #*3 for mean and std dev and median
        df.loc[idx] = row
        return
    for scalar,scalar_prefix in zip(scalars, scalar_prefixes):
        if np.sum(np.isnan(scalar[voxels_mask])) > 0.5 * numPixels:    
            row.append(np.nan) #median
            row.append(np.nan) #mean
            row.append(np.nan)  #std
        else:
            row.append(np.nanmedian(scalar[voxels_mask]))
            row.append(np.nanmean(scalar[voxels_mask]))
            row.append(np.nanstd(scalar[voxels_mask]))
    #note that we are separating the volume calculation from the scalar calculation because the ROIs come from the T1 image, which
    #usually has a better FOV than the diffusion image. The best to calculate the volume is to use only the applied transform for the
    #T1 image, but no one ever seems to use the volume anyway and it would only affect the regions near the brainstem
    volume = calc_volume(key, label, label_nifti) 
    row.append(volume)
    df.loc[idx] = row   #actually adding the row to the dataframe
    return

#################################################################################

#inp = Path("/home-local/kimm58/AtlasToDiffusionReg/data/inputs")
#out = Path("/home-local/kimm58/AtlasToDiffusionReg/data/outputs")
inp = Path("/INPUTS/")
out = Path("/OUTPUTS/")
file_name = [x for x in inp.glob('*.bval*')][0].name
name_match = re.search("^(.*).bval$", file_name)
name = name_match.group(1)
#get the mask from PreQual
mask_file = inp/("mask.nii.gz")
mask_nii = nib.load(mask_file)
mask = mask_nii.get_fdata()

#inputs/intermediates
fa = out/("{}%{}.nii.gz".format(name, 'fa'))
md = out/("{}%{}.nii.gz".format(name, 'md'))
ad = out/("{}%{}.nii.gz".format(name, 'ad'))
rd = out/("{}%{}.nii.gz".format(name, 'rd'))
seg = out/("{}%T1_seg_to_dwi.nii.gz".format(name))

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

#setting up the dataframe (df)
    #sets up the column names here
cols = ["Labelmap Name", "ROI NAME"]
for p in scalar_prefixes:
    cols.append(p+'-median')
    cols.append(p+'-mean')
    cols.append(p+'-std')
cols.append("Volume_(mm^3)")
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

#add in segmentation map if it exists as well
path_to_seg_labels = inp/("T1_seg.txt")
if seg.exists() and path_to_seg_labels.exists():
    atlas_names.append("T1_segmentation")   #add the segmentation to the list of atlases/labelmap names
    seg_nifti = nib.load(seg)
    atlases.append(seg_nifti)           #add the nifti to the list of labelmaps
    label_doc = np.loadtxt(path_to_seg_labels, dtype=str)   #removed delimiter='\n'
    label_dict = dict()
    for label in label_doc[1:]:
        #splits = re.split(r'[,\s]+', label)  #splits by comma or space #.split(',')
        label_dict[int(label[0])] = label[1]        #changed with delimiter='\n' removal
    atlas_dicts.append(label_dict)                  #add the label dicitonary to the list of labelmap dictionaries

#actually calculating the rois
idx =0
for atlas_name,label_nifti,atlas_dict in zip(atlas_names, atlases, atlas_dicts):    #loops through all the atlases
    label = label_nifti.get_fdata()
    print("Calculating volume and median, mean, std for diffusion scalars of {}....".format(atlas_name))
    for key,roi in tqdm(atlas_dict.items()):                            #loops through each ROI for the current atlas
        calc_scalars(atlas_name, roi, key, label, df, scalars, scalar_prefixes, idx, label_nifti, mask)
        idx += 1

print("Finished calculating volume and median, mean, std for all ROIs of all atlases")
print("Outputting csv...")
df.to_csv(out/("{}%diffusionmetrics.csv".format(name)), index=False)

print("*********************************")
print("FINISHED CREATING CSV")
print("*********************************")


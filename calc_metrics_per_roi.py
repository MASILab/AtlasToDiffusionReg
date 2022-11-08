import pandas as pd
import nibabel as nib
from tqdm import tqdm
import re
from pathlib import Path #may have to run pip install while in the singularity sandbox in order to install these

file_name = [x for x in Path("/INPUTS").glob('*.bval*')][0].name
name_match = re.search("^(.*).bval$", file_name)
name = name_match.group(1)

#inputs/intermediates
fa = Path("/OUTPUTS/{}%fa.nii.gz".format(name))
md = Path("/OUTPUTS/{}%md.nii.gz".format(name))
ad = Path("/OUTPUTS/{}%ad.nii.gz".format(name))
rd = Path("/OUTPUTS/{}%rd.nii.gz".format(name))

#outputs: just the csv file?






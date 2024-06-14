import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import nibabel as nib
import matplotlib.colors as colors
import os
from tqdm import tqdm
import re

def get_slice(img, dim, slicenum):
    if dim==0:
        return img[slicenum,:,:]
    elif dim==1:
        return img[:,slicenum,:]
    else:
        return img[:,:,slicenum]

def get_aspect_ratio(dim, vox_dim):
    if dim == 0:
        vox_ratio = vox_dim[2]/vox_dim[1]
    elif dim == 1:
        vox_ratio = vox_dim[2]/vox_dim[0]
    elif dim == 2:
        vox_ratio = vox_dim[1]/vox_dim[0]
    return vox_ratio


#creates a png for one atlas
def create_seg_png(segdata, imgdata, cmap, outfile, atlas_name, imghd):
    #create the plt figure
    f, ax = plt.subplots(3,3,figsize=(10.5, 8), constrained_layout=True)
    
    #loop through sag, coronal, axial slices
    for dim in range(3):
        #get the center slice
        slice=segdata.shape[dim]//2
        for i,slice_offput in enumerate(range(-10, 20, 10)):
            #get the aspect ratio for plotting purposes
            vox_dims = imghd.get_zooms()
            ratio = get_aspect_ratio(dim, vox_dims)
            #get the slices we want to show
            img_slice = np.rot90(get_slice(imgdata, dim, slice+slice_offput), k=1)
            seg_slice = np.rot90(get_slice(segdata, dim, slice+slice_offput), k=1)
            #plot the slices
            ax[dim,i].imshow(img_slice, cmap='gray', aspect=ratio)
            ax[dim,i].imshow(seg_slice, alpha=0.6, cmap=cmap, aspect=ratio, interpolation='nearest')
            ax[dim,i].axis('off')
    #save the slices
    #print(outdir)
    f.suptitle(atlas_name)
    plt.savefig(outfile, bbox_inches='tight')
    plt.close('all')

#setup to creating the png and creating the png
def setup_and_make_png(lut_file, imgfile, segfile, atlas_name, outdir, skip_header=1):

    lut_data = np.genfromtxt(lut_file, skip_header=skip_header, dtype=str)

    # Extract the indices, colors, and labels from the LUT data
    lut_indices = lut_data[:, 0].astype(int)
    #print(lut_data)
    #print(lut_data[:, 2:])
    lut_colors = lut_data[:, 2:].astype(int) / 255.0
    lut_labels = lut_data[:, 1]

    # Create a colormap from the LUT
    cmap = colors.ListedColormap(lut_colors)

    #load in segmentation file
    segim = nib.load(segfile)
    segdata = np.squeeze(segim.get_fdata()[:,:,:])
    #load in image file
    img = nib.load(imgfile)
    imgdata = np.squeeze(img.get_fdata()[:,:,:])

    ##if you want to reorient to LAS prior to plotting the images, use the following code:
    #new_affine = nib.orientations.apply_orientation(affine, nib.orientations.axcodes2ornt('LAS'))
    #reoriented_img = nib.Nifti1Image(img.get_fdata(), new_affine)

    assert segdata.shape == imgdata.shape, "{} and {} are not the same dimensions: {} and {}".format(str(imgfile), str(segfile), str(imgdata.shape), str(segdata.shape))

    #create the png
    create_seg_png(segdata, imgdata, cmap, outdir, atlas_name, img.header)

#for SLANT segmentation
def setup_and_make_png_seg(lut_file, imgfile, segfile, atlas_name, outfile, skip_header=1):

    lut_data = np.genfromtxt(lut_file, skip_header=skip_header, dtype=str)
    #print(lut_data)
    # Extract the indices, colors, and labels from the LUT data
    #print(lut_data)
    lut_indices = lut_data[:, 0].astype(int)
    #print(lut_data)
    #print(lut_data[:, 2:])
    #print(atlas_name)

    lut_colors = lut_data[:, 2:].astype(int) / 255.0
    lut_labels = lut_data[:, 1]

    # Create a colormap from the LUT
    cmap = colors.ListedColormap(lut_colors)
    colours = cmap.colors
    colours[:, 3] = 1 - colours[:, 3]
    cmap = colors.ListedColormap(colours)

    #load in segmentation file
    segim = nib.load(segfile)
    segdata = np.squeeze(segim.get_fdata()[:,:,:])
    #load in image file
    img = nib.load(imgfile)
    imgdata = np.squeeze(img.get_fdata()[:,:,:])

    assert segdata.shape == imgdata.shape, "{} and {} are not the same dimensions: {} and {}".format(str(imgfile), str(segfile), str(imgdata.shape), str(segdata.shape))

    #create the png
    create_seg_png(segdata, imgdata, cmap, outfile, atlas_name, img.header)

#get the name of the atlases
file_name = [x for x in Path("/INPUTS").glob('*.bval*')][0].name
name_match = re.search("^(.*).bval$", file_name)
name = name_match.group(1)

print("Now making QA PNGs...")

##inputs
fa = Path("/OUTPUTS/{}%fa.nii.gz".format(name))#FA map
seg = Path("/OUTPUTS/{}%T1_seg_to_dwi.nii.gz".format(name)) #check if it exists

atlases = [x for x in Path('/OUTPUTS').glob("dwmri%Atlas*")]
labels = []
for atlas in atlases:
    atlas_name = atlas.name.split('%')[1].split('.')[0]
    ogname = atlas_name.split('_', 1)[1]
    labelfile = Path("/INPUTS/Labels_{}.txt".format(ogname))
    labels.append(labelfile)


#outputs
pngs = []
for atlas in atlases:
    atlas_name = atlas.name.split('%')[1].split('.')[0]
    pngs.append(Path("/OUTPUTS/{}.png".format(atlas_name)))

#conditional input and output if seg exists
if seg.exists():
    atlases.append(seg)
    labels.append(Path("/INPUTS/T1_seg.txt"))
    pngs.append(Path("/OUTPUTS/T1_seg.png"))


#loop through all of the atlases, create a png for each one
    #have to do a special one for the SLANT segmentation maybe?
for atlas,label,png in zip(atlases, labels, pngs):
    atlas_name = atlas.name.split('%')[1].split('.')[0]
    #print(np.genfromtxt(label, skip_header=1, dtype=str)[:,0].astype(int))
    if atlas_name == "T1_seg_to_dwi":
        setup_and_make_png_seg(label, fa, atlas, atlas_name, png, skip_header=4)
    else:
        setup_and_make_png(label, fa, atlas, atlas_name, png)

#for atlas
# def setup_and_make_png(lut_file, imgfile, segfile, atlas_name, outdir, skip_header=1):

#     lut_data = np.genfromtxt(lut_file, skip_header=skip_header, dtype=str)

#     # Extract the indices, colors, and labels from the LUT data
#     lut_indices = lut_data[:, 0].astype(int)
#     #print(lut_data)
#     #print(lut_data[:, 2:])
#     lut_colors = lut_data[:, 2:].astype(int) / 255.0
#     lut_labels = lut_data[:, 1]

#     # Create a colormap from the LUT
#     cmap = colors.ListedColormap(lut_colors)

#     #load in segmentation file
#     segim = nib.load(segfile)
#     segdata = np.squeeze(segim.get_fdata()[:,:,:])
#     #load in image file
#     img = nib.load(imgfile)
#     imgdata = np.squeeze(img.get_fdata()[:,:,:])

#     assert segdata.shape == imgdata.shape, "{} and {} are not the same dimensions: {} and {}".format(str(imgfile), str(segfile), str(imgdata.shape), str(segdata.shape))

#     #create the png
#     create_seg_png(segdata, imgdata, cmap, outdir, atlas_name, img.header)



####
def create_WMAtlas_pdfs(matches):

    out_root = Path("/home-local/kimm58/Diff_MRI_Harmonization/data/Harmonization/wmatQA")
    if not out_root.exists():
        os.mkdir(out_root)

    x=0

    for match in tqdm(matches):
        for i,session in enumerate(match):
            splits = session.split('_')
            sub = splits[0]
            ses = splits[1]
            site = site_dic[i]

            #specify the root path
            root = Path("/nfs2/kimm58/WMAtlas/{}/{}/{}".format(site, sub, ses))
            fa = root/("dwmri%fa.nii.gz")
            if not fa.exists():
                print(fa)
                continue
            label_path = Path("/nfs2/kimm58/AtlasInputs/")

            outdir = out_root/(session)
            if not outdir.exists():
                os.mkdir(outdir)

            atlases = []
            labels = []

            #collect all tha atlases
            for f in label_path.glob('Atlas*'):
                atlas_name = f.name.split('.')[0]
                ogname = atlas_name.split('_', 1)[1]
                labelfile = label_path/("Labels_{}.txt".format(ogname))
                atlases.append(atlas_name)
                labels.append(labelfile)

            #loop through all of the atlases to generate pngs
            for i,(lut_file,atlas_name) in enumerate(zip(labels,atlases)):
                atlas_file = root/("dwmri%{}.nii.gz".format(atlas_name))
                if not atlas_file.exists():
                    continue
                #print(type(outdir/("{}.png".format(atlas_name))))
                if (outdir/("{}.png".format(atlas_name))).exists():
                    #print(outdir)
                    continue
                setup_and_make_png(lut_file, fa, atlas_file, atlas_name, outdir)

            #now that the pngs are geenrated, concat them all into a PDF
            pngs = [x for x in outdir.glob('*.png')]
            pngs.sort()
            outpdf = outdir/("QA.pdf")
            pdf_paths = []
            for png in pngs:
                pdf_file = Path(str(png).replace('.png', '.pdf'))
                pdf_paths.append(pdf_file)
                # with open(png, 'rb') as f:
                #     image = f.read()
                #     pdf = img2pdf.convert(image)
                #     with open(pdf_file, 'wb') as output:
                #         output.write(pdf)
            #concatenate them all into one
            # with open(outpdf, 'wb') as output:
            #     if len(pdf_paths) == 0:
            #         break
            #     print(type(pdf_paths[0]))
            #     outdata = img2pdf.convert([str(x) for x in pdf_paths])
            #     output.write(outdata)
            #print(outdir)

            for pdf_file in pdf_paths:
                if pdf_file.exists():
                    os.remove(pdf_file)

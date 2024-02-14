# AtlasToDiffusionReg v1.1
Singularity to register a structural atlas to the diffusion space of a subject

author: Michael Kim


# TO DOs:

-QA of the registered atlases into diffusion space

	-overlay of atlases on an FA map

	-perhaps something else as well

-Possibly options

	-just calculating the transforms and not applying them
	
	-only keeping certain outputs
	
-have the outputs more organized than just in one outputs folder

-checks to make sure that the inputs are correct and the output directory is valid as well


# TO RUN:

	singularity run -B /path/to/inputs/:/INPUTS -B /path/to/outputs:/OUTPUTS WMAtlas.simg (or whatever the singularity image is called)

# INPUTS:

Atlases you want to register

	-must have "Atlas_" at the beginning of the filename, followed by the atlas name
	
		-i.e. "Atlas_JHU_MNI_WMPM_Type_I.nii.gz"
		
			-Name of the Atlas is then "JHU_MNI_WMPM_Type_I"
			
Labels for each Atlas in the inputs

	-the corresponding labels must be named: "Labels_<Atlas_Name>.txt"
	
		-if we use the atlas above, the label file should be called "Labels_JHU_MNI_WMPM_Type_I.txt"
		
	-the label files should have the following structure:
	
		#INTENSITY/Integer_label Region_Of_Interest_Name

		0 Background			
		1 Superior_Parietal_Lobule_left
		2 Cingulate_Gyrus_left
		3 Middle_Frontal_Gyrus_left
		...
		
	- In other words, each line should have an intensity value of the labelmap and the corresponding name of the label delimited by a space
	
	- The first line of the text file should be the background with intensity of zero
	
	- The names if the ROIs in the labelmap should not contain any spaces: the only spaces should be between the intensity and corresponding ROI name
Structural Template that the atlases are in the space of

	-needs to be named "template.nii.gz"
	
		-if it is not named this you can specify so by adding the following option in the singularity call:
		
			singularity run -B ...:/INPUTS -B ...:/OUTPUTS -B /path/to/the/template/:/INPUTS/template.nii.gz WMAtlas
			
Structural T1 scan of the subject

	-needs to be named "t1.nii.gz"
	
		-like with the template, can specify an additional line if it is not named so:
		
			"-B /path/to/t1:/INPUTS/t1.nii.gz"
			
	-CANNOT already be skull stripped
	
Diffusion data for the subject (dwmri scan, bval, bvec)

	-Name can be whatever you want, but they must all have the same name
	
		-i.e if the name you want to give it is "dwmri"
		
			dwmri.nii.gz
			dwmri.bval
			dwmri.bvec
			
		-note that all outputs will use this name you provide
		
T1 segmentation from SLANT (optional)

	-needs to be named "T1_seg.nii.gz"
	
	-can technically also be a brain mask
	
	-like with the template, can specify an additional line if it is not named so:
	
		"-B /path/to/t1:/INPUTS/T1_seg.nii.gz"
		
	-If this input is not included, then fsl's bet will be used for the brain extraction and the mask (not recommended)

# OUTPUTS are:

	- the transformations
	
		- see below in Notes for how to use them yourself
		
	-the registered atlases
	
		- <dwiname>%<atlas_name>.nii.gz
		
	-skull stripped t1 and the extracted b0
	
	-diffusion scalar maps
	
		-e.g. <dwiname>%fa.nii.gz
		
	-the single shell dwi and its bval/bvec files
	
	-the csv file containing the calculations
	
# Steps:
- T1 is registered to the template using ANTs to obtain both the affine and nonlinear transformations
- T1 is skull stripped and b0 is extracted
- Transformation from diffusion to t1 space is calculated using FSL
- FSL transformations are converted to ANTs format using c3d
- Atlases are registered to diffusion space using the transforms
- The first shell diffusion scans are extracted from the dwi file
- FA, MD, AD, RD maps are calculated from the first shell
- Mean and std dev are calculated for the diffusion metrics for each ROI for each atlas and placed in a csv file



# The singularity assumptions: 

-all imaging files provided are gzpied niftis (.nii.gz) 

-the bvals/bvecs are iun FSL format (can be otherwise, but not guaranteed to work)

-the dwi data have already been preprocessed for distortion correction, to remove noise, artifacts, etc.

-the t1 is NOT skull stripped



# Notes

- if you  would like to apply the transformations yourself, this is the following ANTs command to do so:

	antsApplyTransforms -d 3 -i <atlas_file> -r <b0_file> -n NearestNeighbor \
	-t <t1_to_b0_transform> -t [<t1_to_template_affine_transform>,1] \
	-t <t1_to_template_inv_warp> -o <output_file_name>

		-t1_to_b0 tranform is called 			...%ANTS_t1tob0.txt
		-t1_to_template_affine is called		...%0GenericAffine.mat
		-t1_to_template_inv_warp is called		...%1InverseWarp.nii.gz
		-do not have to use the b0 as reference, can use anything in the diffusion space (like the FA map)

- to move something from diffusion space into the template space, use a similar call, but reverse the order of the transformations

	

	-additionally, you must use the inverse of the transformations applied 






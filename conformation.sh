#define the name of the file 
xtc_file="md_solu.xtc"
tpr_file="md.tpr"
ndx_file="index.ndx"



# Define the output file names
rmsd_file="rmsd.xvg"
rmsf_file="rmsf.xvg"
rmsf_res_file="rmsf_res.xvg"
gyration_file="gyration.xvg"
energy_file="energy.xvg"
sasa_file="sasa.xvg"
hbond_file="hbond.xvg"
rgyr_file="rgyr.xvg"
salt_bridge_file="salt_bridge.xvg"
rotation_file="rotation.xvg"
covariance_file="covariance.xvg"



echo 0 0 | gmx_mpi covar -s $tpr_file -f $xtc_file -n $ndx_file -ascii -o $covariance_file 
### Perform PCA analysis
echo 0 0 | gmx_mpi anaeig -f $xtc_file -s $tpr_file -eig covariance.xvg -v eigenvec.trr -proj proj.xvg -first 1 -last 4 -n $ndx_file
##
### Perform PCA analysis with extreme values
echo 0 0 | gmx_mpi anaeig -f $xtc_file -v eigenvec.trr -eig covariance.xvg -s md.gro -first 1 -last 10 -extr extreme.pdb -n $ndx_file 
## # Perform PCA analysis with component contributions
echo 0 0 | gmx_mpi anaeig -f $xtc_file -v eigenvec.trr -eig covariance.xvg -s $tpr_file -first 1 -last 4 -comp pca_comp.xvg -n $ndx_file 
### Perform PCA analysis and generate 2D projection
echo 0 0 | gmx_mpi anaeig -f $xtc_file -v eigenvec.trr -eig covariance.xvg -s $tpr_file -first 1 -last 4 -2d pca_2d.xvg -n $ndx_file 
##
### PCA 2d with PC1 and PC2
echo 0 0 | gmx_mpi anaeig -f $xtc_file -s $tpr_file -eig covariance.xvg -v eigenvec.trr -proj proj_eig.xvg -2d 2d_proj.xvg -first 1 -last 2 -n $ndx_file 
### clcaulte the free energy
gmx_mpi sham -f 2d_proj.xvg -ls gibbs.xpm -notime #for free energy, "sham" module uses PC1 and PC2 file

cp ../xpm2txt.py . 
python xpm2txt.py -f gibbs.xpm -o gibbs.txt
rm *#*


#python xpm2txt.py -f gibbs.xpm -o gibbs.txt


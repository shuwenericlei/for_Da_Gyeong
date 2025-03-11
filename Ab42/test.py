#!/usr/bin/env python3

import os

def create_swissdock_script(SMILES, receptor, drug_name):
    """Generate a SLURM job script for each docking simulation."""
    script_content = f"""#!/bin/bash

# SMILES string
SMILES="{SMILES}"

# Define a name variable (adjust this as necessary)
name={drug_name}_{receptor}

# Define the name of the protein target 
protein={receptor}

# Execute the curl command to upload the ligand
output=$(curl -sg "https://swissdock.ch:8443/preplig?mySMILES=$SMILES")

# Extract the session number
session_number=$(echo "$output" | grep "Session number:" | sed 's/Session number: //')

# Check if the session number was extracted
if [ -z "$session_number" ]; then
    echo "Failed to extract session number."
    echo "Curl output: $output"
    exit 1
fi

# Print the session number
echo "Session number: $session_number"

# Export name and session number to CSV (APPEND)
echo "$name,$session_number" >> session.csv  # Use >> to append

echo "==================================================="
echo ""
# Upload the target PDB. The @ symbol is the correct way to upload a file
target_upload_output=$(curl -F "myTarget=@$protein" "https://swissdock.ch:8443/preptarget?sessionNumber=$session_number")
echo "Target upload output:"
echo "$target_upload_output"
echo "==================================================="
echo ""
# Calculate the box center of the molecule of interest
read cx cy cz <<< $(awk '/^ATOM/ {{x+=$7; y+=$8; z+=$9; n++}} END {{if (n>0) printf "%.3f %.3f %.3f", x/n, y/n, z/n; else print "0 0 0"}}' $protein)

# Calculate the range of each x, y, z to define the size of the docking box
read rx ry rz <<< $(awk '
    /^ATOM/ {{
        if (NR == 1) {{
            minx = maxx = $7;
            miny = maxy = $8;
            minz = maxz = $9;
        }} else {{
            if ($7 < minx) minx = $7;
            if ($7 > maxx) maxx = $7;
            if ($8 < miny) miny = $8;
            if ($8 > maxy) maxy = $8;
            if ($9 < minz) minz = $9;
            if ($9 > maxz) maxz = $9;
        }}
    }}
    END {{
        if (NR > 0) printf "%.3f %.3f %.3f", (maxx-minx), (maxy-miny), (maxz-minz);
        else print "0 0 0";
    }}
' $protein)

echo "Center of geometry: ($cx, $cy, $cz)"
echo "Range of the box: ($rx, $ry, $rz)"

box_center="${{cx}}_${{cy}}_${{cz}}"
box_size="${{rx}}_${{ry}}_${{rz}}"

echo "Session number: $session_number"
echo "Box center: $box_center"
echo "Box Size: $box_size"
echo "==================================================="
echo ""
# Set parameters with the correct format
set_params_output=$(curl -s "https://swissdock.ch:8443/setparameters?sessionNumber=$session_number&exhaust=60&cavity=70&ric=1&boxCenter=$box_center&boxSize=$box_size&name=$name")

echo "Set parameters output:"
echo "$set_params_output"
echo "==================================================="
echo ""
# Start docking
start_dock_output=$(curl "https://swissdock.ch:8443/startdock?sessionNumber=$session_number")
echo "Start docking output:"
echo "$start_dock_output"
echo "==================================================="
echo ""
# Start time
start_time=$(date +%s)

# Polling loop to check status (monitor for 2 minutes)
while true; do
    status_output=$(curl -sg "https://www.swissdock.ch:8443/checkstatus?sessionNumber=$session_number")
    echo "Status output:"
    echo "$status_output"

    # Check for "Docking Completed"
    if echo "$status_output" | grep -q "Docking Completed"; then
        echo "Docking completed!"
        break
    elif echo "$status_output" | grep -q "Error" || echo "$status_output" | grep -q "Failed"; then
        echo "An error or failure occurred during docking. Check the status output for details."
        break
    fi

    # Stop after 2 minutes (120 seconds)
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    if [ $elapsed_time -ge 120 ]; then
        echo "Monitoring stopped after 2 minutes."
        break
    fi

    sleep 60  # Wait 60 seconds before checking status again
done
"""
    script_name = f"swiss_dock_{drug_name}_{receptor}.sh"
    with open(script_name, 'w') as f:
        f.write(script_content)
    os.chmod(script_name, 0o755)


def main():
    # define the two drugs you hope to perform docking as a list 

    # List of protein targets (Fixed Commas)
    protein_lst = [
        "Dimer_5OQV_S1.pdb", "Dimer_5OQV_S2.pdb", "Dimer_5OQV_S3.pdb",
        "Dimer_8EZE_S1.pdb", "Dimer_8EZE_S2.pdb", "Dimer_8EZE_S3.pdb",
        "Hexa_5OQV.pdb", "Hexa_8EZE.pdb",
        "Monomer_1.pdb", "Monomer_2.pdb", "Monomer_3.pdb", "Monomer_4.pdb",
        "Monomer_5.pdb", "Monomer_6.pdb", "Monomer_7.pdb", "Monomer_8.pdb",
        "Monomer_9.pdb", "Monomer_10.pdb", "Monomer_11.pdb", "Monomer_12.pdb",
        "Monomer_13.pdb", "Monomer_14.pdb", "Monomer_15.pdb", "Monomer_16.pdb",
        "Monomer_17.pdb", "Monomer_18.pdb", "Monomer_19.pdb", "Monomer_20.pdb",
        "Monomer_21.pdb", "Monomer_22.pdb", "Monomer_23.pdb", "Monomer_24.pdb",
        "Monomer_25.pdb", "Monomer_26.pdb", "Monomer_27.pdb", "Monomer_28.pdb",
        "Tetra_5OQV_S1.pdb", "Tetra_5OQV_S2.pdb", "Tetra_8EZE_S1.pdb", "Tetra_8EZE_S2.pdb",
        "Trimer_1.pdb", "Trimer_2.pdb", "Trimer_3.pdb", "Trimer_4.pdb", "Trimer_5.pdb", "Trimer_6.pdb"
    ]
    #protein_lst=['Trimer_1.pdb']
    SMILES_lst=[
        r"""C[C@@]1([C@H]2[C@@H]([C@H]3[C@@H](C(=O)C(=C([C@]3(C(=O)C2=C(C4=C1C=CC=C4O)O)O)O)C(=O)N)N(C)C)O)O""",
        r"""CCN(CC)CCNC(=O)C1=C(NC(=C1C)/C=C\2/C3=C(C=CC(=C3)F)NC2=RhizolutinO)C""", 
        r"""CC[C@H]1C[C@H]2[C@@H](C=C(C=C[C@@H]3C[C@@H](CC(=O)O[C@H]3C=C2C)O)C)C(=O)O1""", 
        r"""C[C@H]1C[C@H](C[C@@H]([C@H](/C(=C\C=C\C[C@H](OC(=O)C[C@@H]([C@H](C1)C)O)[C@@H]2CCC[C@H]2C(=O)O)/C#N)O)C)C""", 
        r"""OC1=CC=C(C=C1)C1=COC2=C1C=C(OC)C(OCC(O)=O)=C2""", 
        r"""CCN(CC)CCCC(C)NC1=C2C=C(C=CC2=NC3=C1C=CC(=C3)Cl)OC""", 
        r"""BrC1=C(Br)C=C(N(C(C2=CC=CC=C2)=C(CC3=CC=C(Cl)C=C3)N4C5=CC=C4)C5=N6)C6=C1""",
        r"""FC1=CC=C(C=C1)C(=O)C1C(N=CC2=CC=CN12)C1=CC=CO1"""]
    drug_name_lst=[
        "Oxytetracycline", 
        "Sunitinib", 
        "Rhizolutin",
        "Borrelidin", 
        "YB-09", 
        "Quinacrine", 
        "YIAD-0205", 
        "YIAD-0121"]
    for drug_name, SMILES in zip(drug_name_lst, SMILES_lst):
        for protein in protein_lst:
            create_swissdock_script(SMILES, protein, drug_name)
    
    print("SLURM scripts generated. Run './submit_all.sh' to submit jobs.")

    # Generate submission script
    with open("submit_all.sh", "w") as f:
        f.write("""#!/bin/bash
for script in swiss_dock_*.sh; do
    bash "$script"
done
""")
    os.chmod("submit_all.sh", 0o755)

if __name__ == "__main__":
    main()


#!/bin/bash

# SMILES string
SMILES="C[C@@]1([C@H]2[C@@H]([C@H]3[C@@H](C(=O)C(=C([C@]3(C(=O)C2=C(C4=C1C=CC=C4O)O)O)O)C(=O)N)N(C)C)O)O"

# Define a name variable (adjust this as necessary)
name="Oxy_Trimer_1"

# Define the name of the protein target 
protein="Trimer_1.pdb"
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

# Upload the target PDB. The @ symbol is the correct way to upload a file
target_upload_output=$(curl -F "myTarget=@$protein" "https://swissdock.ch:8443/preptarget?sessionNumber=$session_number")
echo "Target upload output:"
echo "$target_upload_output"

# Calculate the box center of the molecule of interest
read cx cy cz <<< $(awk '/^ATOM/ {x+=$7; y+=$8; z+=$9; n++} END {if (n>0) printf "%.3f %.3f %.3f", x/n, y/n, z/n; else print "0 0 0"}' $protein)

# Calculate the range of each x, y, z to define the size of the water box
read rx ry rz <<< $(awk '
    /^ATOM/ {
        if (NR == 1) {
            minx = maxx = $7;
            miny = maxy = $8;
            minz = maxz = $9;
        } else {
            if ($7 < minx) minx = $7;
            if ($7 > maxx) maxx = $7;
            if ($8 < miny) miny = $8;
            if ($8 > maxy) maxy = $8;
            if ($9 < minz) minz = $9;
            if ($9 > maxz) maxz = $9;
        }
    }
    END {
        if (NR > 0) printf "%.3f %.3f %.3f", (maxx-minx), (maxy-miny), (maxz-minz);
        else print "0 0 0";
    }
' $protein)

echo "Center of geometry: ($cx, $cy, $cz)"
echo "Range of the box: ($rx, $ry, $rz)"

box_center="${cx}_${cy}_${cz}"
box_size="${rx}_${ry}_${rz}"

echo "Session number: $session_number"
echo "Box center: $box_center"
echo "Box Size: $box_size"

# Set parameters with the correct format
set_params_output=$(curl -s "https://swissdock.ch:8443/setparameters?sessionNumber=$session_number&exhaust=60&cavity=70&ric=1&boxCenter=$box_center&boxSize=$box_size&name=$name")

echo "Set parameters output:"
echo "$set_params_output"

# Start docking
start_dock_output=$(curl "https://swissdock.ch:8443/startdock?sessionNumber=$session_number")
echo "Start docking output:"
echo "$start_dock_output"

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
    if [ $elapsed_time -ge 60 ]; then
        echo "Monitoring stopped after 2 minutes."
        break
    fi

    sleep 60  # Wait 60 seconds before checking status again
done


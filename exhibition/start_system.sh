#!/bin/bash

# # Start muselsl in a new Mintty window and keep it open
# start "" "C:\Program Files\Git\usr\bin\mintty.exe" -h always -e bash -l -c "
# source ~/.bashrc;
# source ~/anaconda3/etc/profile.d/conda.sh;
# conda activate goofi-pipe || { echo 'Failed to activate conda environment'; read -n 1 -s; exit 1; }
# muselsl || { echo 'Failed to start muselsl'; read -n 1 -s; exit 1; }
# echo 'muselsl finished. Press any key to exit...';
# read -n 1 -s;
# bash --login
# "

# # Start goofi-pipe in another Mintty window and keep it open
# start "" "C:\Program Files\Git\usr\bin\mintty.exe" -h always -e bash -l -c "
# source ~/.bashrc;
# source ~/anaconda3/etc/profile.d/conda.sh;
# conda activate goofi-pipe || { echo 'Failed to activate conda environment'; read -n 1 -s; exit 1; }
# cd ~/Documents/github/LakotaNeuralDreams/exhibition/goofi || { echo 'Directory not found'; read -n 1 -s; exit 1; }
# goofi-pipe MoCNA_04.gfi || { echo 'Failed to run goofi-pipe'; read -n 1 -s; exit 1; }
# echo 'goofi-pipe finished. Press any key to exit...';
# read -n 1 -s;
# bash --login
# "

# # Open the TouchDesigner project
# start "" "C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe" "C:\Users\skite\Documents\Github\LakotaNeuralDreams\exhibition\TouchDesigner\installation.toe"

start "" "C:\Program Files\Git\usr\bin\mintty.exe" -h always -e bash -l -c "
echo 'Starting muselsl setup...';
source ~/.bashrc || { echo 'Failed sourcing .bashrc'; read -n 1 -s; exit 1; }
echo 'Sourced .bashrc successfully.';
source ~/anaconda3/etc/profile.d/conda.sh || { echo 'Failed sourcing conda.sh'; read -n 1 -s; exit 1; }
echo 'Sourced conda.sh successfully.';
conda activate goofi-pipe || { echo 'Failed to activate conda env'; read -n 1 -s; exit 1; }
echo 'Activated goofi-pipe env.';
muselsl || { echo 'Failed to run muselsl'; read -n 1 -s; exit 1; }
echo 'muselsl finished.';
echo 'Press any key to exit...';
read -n 1 -s;
bash --login
"

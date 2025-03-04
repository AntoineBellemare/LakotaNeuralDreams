@echo off
REM Launch muselsl
start "Muselsl" "C:\Program Files\Git\usr\bin\mintty.exe" -h always -e /usr/bin/bash -l -c ^
"source ~/.bashrc; source ~/miniconda3/etc/profile.d/conda.sh; conda activate goofi-pipe; muselsl stream; echo Press any key; read -n 1 -s; bash --login"

REM Launch goofi-pipe
start "Goofi" "C:\Program Files\Git\usr\bin\mintty.exe" -h always -e /usr/bin/bash -l -c ^
"source ~/.bashrc; source ~/miniconda3/etc/profile.d/conda.sh; conda activate goofi-pipe; cd ~/Documents/github/LakotaNeuralDreams/exhibition/goofi; goofi-pipe MoCNA_04.gfi; echo Press any key; read -n 1 -s; bash --login"

REM Open TouchDesigner
start "TouchDesigner" "C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe" ^
"C:\Users\skite\Documents\Github\LakotaNeuralDreams\exhibition\TouchDesigner\installation.toe"

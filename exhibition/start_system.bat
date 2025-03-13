@echo off
REM Launch GUI User Dual
start "GUI User Dual" "C:\Program Files\Git\usr\bin\mintty.exe" -h always -e /usr/bin/bash -l -c ^
"source ~/.bashrc; source ~/miniconda3/etc/profile.d/conda.sh; conda activate goofi-pipe; cd ~/Documents/github/LakotaNeuralDreams/exhibition; python gui_user_dual.py; echo Press any key; read -n 1 -s; bash --login"

start "Muselsl" "C:\Program Files\Git\usr\bin\mintty.exe" -h always -e /usr/bin/bash -i -c "~/Documents/github/LakotaNeuralDreams/exhibition/start_muse.sh"

REM Launch goofi-pipe
start "Goofi" "C:\Program Files\Git\usr\bin\mintty.exe" -h always -e /usr/bin/bash -l -c ^
"source ~/.bashrc; source ~/miniconda3/etc/profile.d/conda.sh; conda activate goofi-pipe; cd ~/Documents/github/LakotaNeuralDreams/exhibition/goofi; goofi-pipe MoCNA_04.gfi; echo Press any key; read -n 1 -s; bash --login"

@REM REM Open TouchDesigner
@REM start "TouchDesigner" "C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe" ^
@REM "C:\Users\skite\Documents\Github\LakotaNeuralDreams\exhibition\TouchDesigner\installation.toe"

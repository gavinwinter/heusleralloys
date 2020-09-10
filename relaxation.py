# -*- coding: utf-8 -*-
"""
Initial and additional relaxation runs. 
"""

#-----------------------------------------
#clear previous variables
for name in dir():
    if not name.startswith("_"):
        del globals()[name]

#-----------------------------------------
# Import modules
import numpy as np
import os
import subprocess
import time
import shutil
from mgmt import Name, write_output, fSubmitIn, fWait


        
def relax(homedir,name,job,status):
    name = Name(name.alloyasstr,name.tag,job)
    
    # Makes directory with alloy name and tag the current working directory
    os.chdir(homedir)
    os.chdir(name.alloy_tag)
    alloydir=os.getcwd()
    
    # Make directory for job (relaxation)
    if not os.path.exists(job):
        os.mkdir(job)
    
    os.chdir(job)
    jobdir = os.getcwd()
    
    # Length of time to wait for file to finish running
    max_wait = 10.**6   #seconds
    
    if status=="running":
        # Waits until job finishes if job is still running upon resume
        write_output(homedir,name,
                     "Waiting for {} to finish".format(name.alloy_tag_job))
        fWait(homedir,max_wait,name)
    
    else:       
        # Name of batch file for relaxation
        cmd = "sbatch batch"
        
        if os.path.exists("{}/CONTCAR".format(alloydir)):
            # Copies input files for relaxation into directory for job
            # Uses CONTCAR as POSCAR if previous relaxation already run
            in_files = ["CONTCAR", "POTCAR", "INCAR", "KPOINTS", "batch"]
            
            os.chdir(alloydir)
            
            for i in range(len(in_files)):
                shutil.copy(in_files[i], job)
                
            os.remove("CONTCAR")
            
            os.chdir(jobdir)
            
            os.rename("CONTCAR","POSCAR")

        else:
            # Copies input files for relaxation into directory for job
            in_files = ["POSCAR", "POTCAR", "INCAR", "KPOINTS", "batch"]
            
            os.chdir(alloydir)
            
            for i in range(len(in_files)):
                shutil.copy(in_files[i], job)
                
            os.chdir(jobdir)
        
        # Change job-name in batch file
        with open("batch","r") as f:
            lines=np.array(f.readlines(),dtype='object')
        for i in np.arange(len(lines)):
            if lines[i].startswith("#SBATCH --job-name=VASPrun"):
                lines[i]=lines[i].replace("VASPrun",name.alloy_tag_job, 1)
        with open("batch","w") as f:
            for i in lines:
                f.write(i)
        time.sleep(1)
        
        # Submit relaxation job
        write_output(homedir,name,"Submit {}".format(name.alloy_tag_job))
        fSubmitIn(cmd,homedir,max_wait,name)
    
    os.chdir(homedir) 
    if os.path.getsize("{}/error.error".format(jobdir)):
        write_output(homedir,name,
                     "{} contains errors".format(name.alloy_tag_job))
        return True
    
    os.chdir(jobdir)
    write_output(homedir,name,"Done with {}".format(name.alloy_tag_job))
    
    # Copy CONTCAR file from completed relaxation to parent directory
    shutil.copy("CONTCAR", alloydir)

    return
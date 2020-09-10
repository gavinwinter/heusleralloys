# -*- coding: utf-8 -*-
"""
Density of states determination.
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


        
def genwave_static_dos(homedir,name,job,status):    
    name = Name(name.alloyasstr,name.tag,job)
    
    # Makes directory with alloy name and tag the current working directory
    os.chdir(homedir)
    os.chdir(name.alloy_tag)
    alloydir=os.getcwd()
    
    # Make directory for job (DOS)
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
        # Name of batch file for DOS
        cmd = "sbatch batch"
        
        # Copies input files for DOS into directory for job
        in_files = ["CONTCAR", "POTCAR", "INCAR", "KPOINTS", "batch"]
        
        os.chdir(alloydir)
        
        for i in range(len(in_files)):
            shutil.copy(in_files[i], job)
        
        os.chdir(jobdir)
        
        os.rename("CONTCAR","POSCAR")
        
        # Change INCAR tags from template to prepare for DOS
        with open("INCAR","r") as f:
            lines=np.array(f.readlines(),dtype='object')
        for i in np.arange(len(lines)):
            if lines[i].startswith("ISIF"):
                lines[i]=lines[i].replace("ISIF","!ISIF", 1)
            elif lines[i].startswith("NSW"):
                lines[i]=lines[i].replace("NSW","!NSW", 1)
            elif lines[i].startswith("IBRION"):
                lines[i]=lines[i].replace("2","-1", 1)
            elif lines[i].startswith("LWAVE"):
                lines[i]=lines[i].replace(".FALSE.",".TRUE.", 1)
                break
        with open("INCAR","w") as f:
            for i in lines:
                f.write(i)
        time.sleep(1)
        
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
    
        # Submit DOS job
        write_output(homedir,name,"Submit {}".format(name.alloy_tag_job))
        fSubmitIn(cmd,homedir,max_wait,name)

    os.chdir(homedir) 
    if os.path.getsize("{}/error.error".format(jobdir)):
        write_output(homedir,name,
                     "{} contains errors".format(name.alloy_tag_job))
        return True

    os.chdir(jobdir)
    write_output(homedir,name,"Done with {}".format(name.alloy_tag_job))
    
    # Copy WAVECAR and IBZKPT files from DOS to parent directory
    shutil.copy("WAVECAR", alloydir)
    shutil.copy("IBZKPT", alloydir)
    
    return

def genwave_static_dos_soc(homedir,name,job,status):
    name = Name(name.alloyasstr,name.tag,job)
    
    # Makes directory with alloy name and tag the current working directory
    os.chdir(homedir)
    os.chdir(name.alloy_tag)
    alloydir=os.getcwd()
    
    # Make directory for job (DOS with SOC)
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
        # Name of batch file for DOS with SOC
        cmd = "sbatch batch"
        
        # Copies input files for DOS with SOC into directory for job
        in_files = ["CONTCAR", "POTCAR", "INCAR", "KPOINTS", "batch"]
        
        os.chdir(alloydir)
        
        for i in range(len(in_files)):
            shutil.copy(in_files[i], job)
        
        os.chdir(jobdir)
        
        os.rename("CONTCAR","POSCAR")
        
        # Change INCAR tags from template to prepare for DOS with SOC
        with open("INCAR","r") as f:
            lines=np.array(f.readlines(),dtype='object')
            lines=lines.astype('U256')
        noncolmagmom=""
        for i in np.arange(len(lines)):
            if lines[i].startswith("ISIF"):
                lines[i]=lines[i].replace("ISIF","!ISIF", 1)
            elif lines[i].startswith("NSW"):
                lines[i]=lines[i].replace("NSW","!NSW", 1)
            elif lines[i].startswith("IBRION"):
                lines[i]=lines[i].replace("2","-1", 1)
            elif lines[i].startswith("LWAVE"):
                lines[i]=lines[i].replace(".FALSE.",".TRUE.", 1)
            elif lines[i].startswith("!LSORBIT"):
                lines[i]=lines[i].replace("!LSORBIT","LSORBIT", 1)
                #lines=np.insert(lines,i+1,"LORBIT = 11\n")
                lines=np.insert(lines,i+2,"LORBMOM = .TRUE.\n")
                lines=np.insert(lines,i+3,"LMAXMIX = 4\n")
            elif lines[i].startswith("MAGMOM"):
                magmom=lines[i].strip("MAGMOM = ").rstrip("\n").split(" ")
                for m in range(len(magmom)):
                    nions=int(magmom[m].split("*")[0])
                    for n in range(nions):
                        noncolmagmom += "2*0 {} ".format(magmom[m].split("*")[1])
                    noncolmagmom += "   "
                lines[i]="MAGMOM = {}\n".format(noncolmagmom)
            elif lines[i].startswith("!SAXIS"):
                lines[i]=lines[i].replace("!SAXIS","SAXIS",1)
            #elif lines[i].startswith("NPAR   ="):
            #    lines[i]="NPAR   = 16\n"
            elif lines[i].startswith("KPAR   ="):
                lines[i]="KPAR   = 4\n"
                break
        with open("INCAR","w") as f:
            for i in lines:
                f.write(i)
        time.sleep(1)
        
        # Change job-name in batch file and request extra nodes/cores/memory
        with open("batch","r") as f:
            lines=np.array(f.readlines(),dtype='object')
        for i in np.arange(len(lines)):
            if lines[i].startswith("#SBATCH --job-name=VASPrun"):
                lines[i]=lines[i].replace("VASPrun",name.alloy_tag_job, 1)
    #        elif lines[i].startswith("#SBATCH --time="):
    #            lines[i]=lines[i].replace("24","48",1)
    #        elif lines[i].startswith("#SBATCH --partition "):
    #            lines[i]=lines[i].replace("short","long",1)
            elif lines[i].startswith("#SBATCH --nodes"):
                lines[i]=lines[i].replace("2","4",1)
            elif lines[i].startswith("#SBATCH --ntasks"):
                lines[i]=lines[i].replace("48","112",1)
            elif lines[i].startswith("#SBATCH --mem="):
                lines[i]=lines[i].replace("100Gb","250Gb",1)
            elif "-n 48" in lines[i]:
                lines[i]=lines[i].replace("48","112",1)
                break
        with open("batch","w") as f:
            for i in lines:
                f.write(i)
        time.sleep(1)
    
        # Submit DOS with SOC job
        write_output(homedir,name,"Submit {}".format(name.alloy_tag_job))
        fSubmitIn(cmd,homedir,max_wait,name)

    os.chdir(homedir) 
    if os.path.getsize("{}/error.error".format(jobdir)):
        write_output(homedir,name,
                     "{} contains errors".format(name.alloy_tag_job))
        return True

    os.chdir(jobdir)
    write_output(homedir,name,"Done with {}".format(name.alloy_tag_job))
    
    # Copy WAVECAR and IBZKPT files from DOS with SOC to parent directory
    shutil.copy("WAVECAR", alloydir)
    shutil.copy("IBZKPT", alloydir)
    
    return
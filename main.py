# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 10:24:04 2020

@author: Gavin
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
import genvaspinfiles
import relaxation
import dos
import bs
import analysis
import multiprocessing
from multiprocessing import Process, Lock
from mgmt import Name, write_output, check_exit_code, check_output
import sys
import time
import shutil

# Location of home directory with python files
homedir = os.getcwd()

print(homedir)


# Function for generic workflow
# lock is used to prevent issues when multiple processes working with same file
# name is an object that is instance of class Name()
# stop_code is the exit_code (checkpoint) at which the workflow will terminate
def automator(lock,name,stop_code):    
    # Get info about Process-# in multiprocessing
    lock.acquire()
    print("{} corresponds with: {}".format(multiprocessing.current_process(),
                                           name.alloy_tag))
    # Read exit_code to resume job at checkpoint (if existing)
    # Sets exit_code to 0 (if no existing job)
    exit_code, enmax_sorted = check_exit_code(name)
    print("exit_code = {}".format(exit_code))
    print("enmax_sorted = {}".format(enmax_sorted))
    lock.release()
    
    # Designate subfolder (based on alloy name and tag)
    if not os.path.exists(name.alloy_tag):
        os.mkdir(name.alloy_tag)
    os.chdir(name.alloy_tag)
    alloydir=os.getcwd()

    if exit_code<1 and exit_code<stop_code:        
        # Generate VASP input files
        genvaspinfiles.genbatch(homedir,alloydir)
        pot_tags, latparam = genvaspinfiles.genalloymetadata(name)
        enmax_sorted = genvaspinfiles.genpotcar(name,pot_tags,alloydir)
        genvaspinfiles.genposcar(name,enmax_sorted,latparam,homedir,alloydir)  
        genvaspinfiles.genkpts(name,homedir,alloydir)
        genvaspinfiles.genincar(name,enmax_sorted,homedir,alloydir)
        
        exit_code+=1
        write_output(homedir,name,
                     "{} exit_code: {}".format(name.alloy_tag,exit_code))
        write_output(homedir,name,
                     "{} generated input files".format(name.alloy_tag))
        write_output(homedir,name,
                     "{} enmax_sorted: {}".format(name.alloy_tag,enmax_sorted))

    
    if exit_code<2 and exit_code<stop_code:
        job, status = check_output(homedir,name,exit_code)
        # Regular workflow for relaxation
        if not "pstress" in name.tag:
            if status and status=="running":
                run=int(job.split("_")[1])
            elif status and status=="finished":
                run=int(job.split("_")[1])+1
            else:
                run=1
            
            # Always perform two relaxation runs, and additional (if needed).
            addlruns=True
            while addlruns:
                job = "Relaxation_{}".format(run)
                if run>2:
                    # Determine if further relaxation runs are needed
                    # Read in number of relaxation steps from OSZICAR 
                    with open("{}/{}/Relaxation_{}/OSZICAR"
                              .format(homedir,name.alloy_tag,(run-1),"r")) as f:
                        lines=np.array(f.readlines())
                    
                    count=0
                    for i in np.arange(len(lines)):
                        if lines[i].count(" F=") == 1:
                            count+=1
                            
                    if count > 1:
                        write_output(homedir,name,
                                     "Another relaxation run needed.")
                    else:
                        addlruns=False
                        write_output(homedir,name,
                                     "Done with relaxation runs.")
                        
                if addlruns:
                    return_value = relaxation.relax(homedir,name,job,status)
                    if return_value:
                        return
                    run+=1
        # Only perform one relaxation run for relaxing at new pstress value
        else:
                if not job:
                    job = "Relaxation"
            
                if not status=="finished":
                    return_value = relaxation.relax(homedir,name,job,status)
                    if return_value:
                        return
                
        exit_code+=1
        write_output(homedir,name,
                     "{} exit_code: {}".format(name.alloy_tag,exit_code))
        write_output(homedir,name,
                     "{} finished relaxation runs".format(name.alloy_tag))
    
    if exit_code<3 and exit_code<stop_code:
        job, status = check_output(homedir,name,exit_code)
        if not job:
            job = "DOS"
        
        if not status=="finished":
            # Density of states calculation
            return_value = dos.genwave_static_dos(homedir,name,job,status)
            if return_value:
                return
        
        exit_code+=1
        write_output(homedir,name,
                     "{} exit_code: {}".format(name.alloy_tag,exit_code))
        write_output(homedir,name,
                     "{} finished DOS run (no SOC)".format(name.alloy_tag))
        
    if exit_code<4 and exit_code<stop_code:
        job, status = check_output(homedir,name,exit_code)
        if not job:
            job = "BS"
        
        if not status=="finished":
            # Band structure calculation
            return_value = bs.static_bs(homedir,name,job,status)
            if return_value:
                return
        
        os.remove("{}/IBZKPT".format(alloydir))
        os.remove("{}/WAVECAR".format(alloydir))
        
        exit_code+=1
        write_output(homedir,name,
                     "{} exit_code: {}".format(name.alloy_tag,exit_code))
        write_output(homedir,name,
                     "{} finished BS run (no SOC)".format(name.alloy_tag))
        
    if exit_code<5 and exit_code<stop_code:
        # Executes all analysis
        analysis.analyzethat(lock,homedir,name,enmax_sorted)
    
        exit_code+=1
        write_output(homedir,name,
                     "{} exit_code: {}".format(name.alloy_tag,exit_code))
        write_output(homedir,name,
                     "{} finished analysis (no SOC)".format(name.alloy_tag))
    
    if exit_code<6 and exit_code<stop_code:
        job, status = check_output(homedir,name,exit_code)
        if not job:
            job = "DOS_SOC"
        
        if not status=="finished":
            # Density of states calculation with SOC
            return_value = dos.genwave_static_dos_soc(homedir,name,job,status)
            if return_value:
                return
        
        exit_code+=1
        write_output(homedir,name,
                     "{} exit_code: {}".format(name.alloy_tag,exit_code))
        write_output(homedir,name,
                     "{} finished DOS run (SOC)".format(name.alloy_tag))
        
    if exit_code<7 and exit_code<stop_code:
        job, status = check_output(homedir,name,exit_code)
        if not job:
            job = "BS_SOC"
        
        if not status=="finished":
            # Band structure calculation with SOC
            return_value = bs.static_bs_soc(homedir,name,job,status)
            if return_value:
                return
        
        os.remove("{}/CONTCAR".format(alloydir))
        os.remove("{}/IBZKPT".format(alloydir))
        os.remove("{}/WAVECAR".format(alloydir))
        
        exit_code+=1
        write_output(homedir,name,
                     "{} exit_code: {}".format(name.alloy_tag,exit_code))
        write_output(homedir,name,
                     "{} finished BS run (SOC)".format(name.alloy_tag))
        
    if exit_code<8 and exit_code<stop_code:
        # Executes all analysis for runs with SOC
        analysis.analyzethat_soc(lock,homedir,name,enmax_sorted)
        
        exit_code+=1
        write_output(homedir,name,
                     "{} exit_code: {}".format(name.alloy_tag,exit_code))
        write_output(homedir,name,
                     "{} finished analysis (SOC)".format(name.alloy_tag))
        
    else:
        write_output(homedir,name,"{} is already done!".format(name.alloy_tag))
    
    return

# Function for workflow involving incremental pstress
def pstress(lock,name,stop_code=8):
    # linspace arg: initial pstress, final pstress, number of increments    
    pstress = np.linspace(5,30,6)
    
    # Initial relaxation runs without pstress
    automator(lock,name,stop_code=2)
    
    # Performs relaxation and calculates BS/DOS at each new pstress
    # At each step, uses CONTCAR from previously relaxed run
    addltag=name.tag
    for i in range(len(pstress)):
        os.chdir(homedir)
        os.chdir(name.alloy_tag)
        contcardir = os.getcwd()
        name = Name(name.alloyasstr,"pstress{}kbar{}".format(int(pstress[i]),
                                                             addltag))
        os.chdir(homedir)
        if not os.path.exists(name.alloy_tag):
            os.chdir(homedir)
            os.mkdir(name.alloy_tag)
            shutil.copy("{}/CONTCAR".format(contcardir),name.alloy_tag)
        automator(lock,name,stop_code=5)
    
    return


#-----------------------------------------
# Chemical ordering for alloy along the (111) body diagonal
alloy = ["Cr-Ti-V-Al","Cr-V-Ti-Al","Cr-V-Al-Ti",
        "Cr-Ti-Nb-Al","Cr-Nb-Ti-Al","Cr-Nb-Al-Ti",
        "Cr-Ti-Ta-Al","Cr-Ta-Ti-Al","Cr-Ta-Al-Ti",
        "Cr-Zr-V-Al","Cr-V-Zr-Al","Cr-V-Al-Zr",
        "Cr-Zr-Nb-Al","Cr-Nb-Zr-Al","Cr-Nb-Al-Zr",
        "Cr-Zr-Ta-Al","Cr-Ta-Zr-Al","Cr-Ta-Al-Zr",
        "Cr-Hf-V-Al","Cr-V-Hf-Al","Cr-V-Al-Hf",
        "Cr-Hf-Nb-Al","Cr-Nb-Hf-Al","Cr-Nb-Al-Hf",
        "Cr-Hf-Ta-Al","Cr-Ta-Hf-Al","Cr-Ta-Al-Hf"]

# Tags for special runs
tag = ["","","",
       "","","",
       "","","",
       "","","",
       "","","",
       "","","",
       "","","",
       "","","",
       "","",""]

stop_code = 8

if not len(alloy) == len(tag):
    print("Number of tags does not match number of alloy names.")

# Lock required when reading/writing single file with multiple processes
lock = Lock()
# Embarassingly parallel processes for VASP runs and analysis for each alloy
# Each parallel process is completely independent
for n in range(len(alloy)):
    name = Name(alloy[n],tag[n])
    p = Process(target=automator,args=(lock,name,stop_code,))
    p.start()
p.join()
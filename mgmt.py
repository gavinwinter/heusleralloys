# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 17:02:07 2020

@author: Gavin
"""

#-----------------------------------------
# Import modules
import numpy as np
import os
import shutil
import ast
import subprocess
import time
from multiprocessing import Lock



# Deals with all things involving names of VASP runs and folders
class Name:
    def __init__(self,alloy,tag=None,job=None):
        if isinstance(alloy,list):
            # returns alloy name as list
            self.alloyaslist = alloy
            # returns alloy name as str
            self.alloyasstr = "-".join(ele for ele in alloy)
        elif isinstance(alloy,str):
            # returns alloy name as list
            self.alloyaslist = alloy.split("-")
            # returns alloy name as string
            self.alloyasstr = alloy 
        self.tag = tag
        self.alloy_tag = "_".join(filter(None,[self.alloyasstr,tag]))
        self.job = job
        self.alloy_tag_job = "_".join(filter(None,[self.alloyasstr,tag,job]))
    def joiner(self,strings,parseby):
        return parseby.join(filter(None,strings))

# Directs all output to append to its respective output file output_XXXX.out
def write_output(homedir,name,text):
    output = open("{}/output_{}.out".format(homedir,name.alloy_tag),"a")
    output.write(text+'\n')
    output.close()
    return

# Extracts exit codes and name sorted by POTCAR (if resuming from previous run)
def check_exit_code(name):
    exit_code = 0
    enmax_sorted = None
    if (os.path.exists("output_{}.out".format(name.alloy_tag)) and
            os.path.getsize("output_{}.out".format(name.alloy_tag))):
        with open("output_{}.out".format(name.alloy_tag),"r") as f:
            lines=np.array(f.readlines())
        
        for i in np.arange(len(lines)):
            if lines[i].startswith(name.alloy_tag) and "exit_code" in lines[i]:
                exit_code = int(lines[i].split()[-1])
            if lines[i].startswith(name.alloy_tag) and "enmax_sorted" in lines[i]:
                enmax_sorted = \
                    ast.literal_eval(lines[i]
                                     .replace('{} enmax_sorted: '
                                              .format(name.alloy_tag),'')
                                     .replace('\n',''))
    
    return exit_code, enmax_sorted

# Reads output_XXXX.out files to check exit codes in workflow and existing jobs
def check_output(homedir,name,exit_code):
    parsedname=None
    job=None
    status=None
    # Check if job already submitted
    if (os.path.exists("{}/output_{}.out".format(homedir,name.alloy_tag)) and
            os.path.getsize("{}/output_{}.out"
                            .format(homedir,name.alloy_tag))):
        with open("{}/output_{}.out".format(homedir,name.alloy_tag),"r") as f:
            lines=np.array(f.readlines())
        
        start_looking=False
        for i in np.arange(len(lines)):
            if "exit_code: {}".format(exit_code) in lines[i]:
                start_looking=True
            if (start_looking and lines[i].startswith("Job ID ") and
                    name.alloy_tag in lines[i]):
                fullname = lines[i].split()[-1]
                parsedname = fullname.split("_")
                parsedname.remove(name.alloyasstr)
                if name.tag:
                    parsedname.remove(name.tag)
                job = "_".join(parsedname)
                status = "running"
            if job:
                if "Done" in lines[i] and fullname in lines[i]:
                    status = "finished"
                    break
        if ((status=="running" or status=="finished") and
                ((os.path.exists("{}/{}/{}/error.error"
                                .format(homedir,name.alloy_tag,job)) and 
                  os.path.getsize("{}/{}/{}/error.error"
                                  .format(homedir,name.alloy_tag,job))) or 
                 not os.path.exists("{}/{}/{}/error.error"
                                    .format(homedir,name.alloy_tag,job)))):
            shutil.rmtree("{}/{}/{}".format(homedir,name.alloy_tag,job))
            job=None
            status = None
            
    return job, status

# Submit job and wait for job to finish
def fSubmitIn(cmd,homedir,max_wait,name):
    # Sumbit shell file
    subprocess.call(cmd, shell=True)
    os.chdir(homedir)
    jobID = (subprocess.check_output("squeue -n {} -o %i"
                                     .format(name.alloy_tag_job), shell=True)
                                     .decode("utf-8").split('\n'))[1]
    write_output(homedir,name,
                 "Job ID {} corresponds to job name {}"
                 .format(jobID,name.alloy_tag_job))
    # Time running
    start_time = time.time()
    # Wait time (in seconds) before running loop again
    wait_time = 60
    loopcount=0
    # Search for tell that simulation ended
    while time.time()-start_time < max_wait:
        status=(subprocess.check_output("squeue -u winter.ga", shell=True)
                                                        .decode("utf-8"))
        loopcount+=1
        if status.count(jobID) == 0:
            # Stop function
            return
        # Wait time
        time.sleep(wait_time)
        
# Wait for job to finish
def fWait(homedir,max_wait,name):
    os.chdir(homedir)
    jobID = (subprocess.check_output("squeue -n {} -o %i"
                                    .format(name.alloy_tag_job), shell=True)
                                    .decode("utf-8").split('\n'))[1]
    # Time running
    start_time = time.time()
    # Wait time (in seconds) before running loop again
    wait_time = 60
    loopcount=0
    # Search for tell that simulation ended
    while time.time()-start_time < max_wait:
        status=subprocess.check_output("squeue -u winter.ga",
                                       shell=True).decode("utf-8")
        loopcount+=1
        if status.count(jobID) == 0 or jobID == "":
            # Stop function
            return
        # Wait time
        time.sleep(wait_time)
        
# Searches for string in line and extracts everything after that
def searchextract(line,string,r_strip=None,return_string=False):
    inlineindex=line.find(string)+len(string)
    if not return_string:
        if r_strip:
            return float((line[inlineindex:].split()[0]).rstrip(r_strip))
        else:
            return float(line[inlineindex:].split()[0])
    if return_string:
        if r_strip:
            return (line[inlineindex:].split()[0]).rstrip(r_strip)
        else:
            return line[inlineindex:].split()
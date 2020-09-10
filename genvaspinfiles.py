# -*- coding: utf-8 -*-
"""
Created on Thu Aug  1 21:38:59 2019

@author: Gavin

Generating POSCAR file from template.
"""

#-----------------------------------------
# Import modules
import numpy as np
import os
import shutil
import pymatgen
import re
import math
import subprocess
from mgmt import searchextract

eleIVB = {'Ti': ('_sv',None), 'Zr': ('_sv',None), 'Hf': ('_sv',None)}
eleVB = {'V': ('_sv',None), 'Nb': ('_sv',None), 'Ta': ('_pv',None)}
eleVIB = {'Cr': ('',None), 'Mo': None, 'W': None}
eleIIIA = {'Al': ('',None), 'Ga': None, 'In': None}



# Correlates alloy names and metadata
def genalloymetadata(name):
    alloy=name.alloyaslist
    pot_tags = []
    radius = []
    periodictable = [eleIVB,eleVB,eleVIB,eleIIIA]
    for idx in range(len(alloy)):
        for group in periodictable:
            ele = alloy[idx]
            if ele in group:
                pot_tags.append(group[ele][0])
                if group[ele][1]:
                    radius.append(group[ele][1])
                else:
                    radius.append(1.05*float(
                        re.sub("[^0-9.\-]","",
                               str(pymatgen.Element(ele).atomic_radius))))
    # Eqn for calculating lattice parameter based on elements on diagonal
    latparam = round(2*sum(radius)/(math.sqrt(3)),10)
    return pot_tags, latparam

def genbatch(homedir,alloydir):
    # Copy batch file
    shutil.copy("{}/batch".format(homedir),"{}/batch".format(alloydir))
    return

def genincar(name,enmax_sorted,homedir,alloydir):
    alloy=name.alloyaslist
    # Read in INCAR template file
    with open("{}/INCAR_template".format(homedir),"r") as f:
        lines=np.array(f.readlines(),dtype='object')
        
    # Determine arrangement type (regardless of which cyclic permutation)
    for n in range(-4,0):
        if (alloy[n] in eleVIB and alloy[n+1] in eleIVB and
                alloy[n+2] in eleVB and alloy[n+3] in eleIIIA):
            arran = "arrand"
        if (alloy[n] in eleVIB and alloy[n+1] in eleVB and
                alloy[n+2] in eleIVB and alloy[n+3] in eleIIIA):
            arran = "arrane"    
        if (alloy[n] in eleVIB and alloy[n+1] in eleVB and
                alloy[n+2] in eleIIIA and alloy[n+3] in eleIVB):
            arran = "arranf"
        else:
            continue
    
    if "magmomcheck1" in name.tag:
        # Determine sorting of magnetic moments based on order from POTCAR
        magmom=[None]*4
        for n in range(len(enmax_sorted)):
            if enmax_sorted[n] in eleIVB:
                magmom[n] = '4*0'
            if enmax_sorted[n] in eleVB:
                magmom[n] = '4*0'
            if enmax_sorted[n] in eleVIB:
                magmom[n] = '4*-4'
            if enmax_sorted[n] in eleIIIA:
                magmom[n] = '4*0'    
    elif "magmomcheck2" in name.tag:
        # Determine sorting of magnetic moments based on order from POTCAR
        magmom=[None]*4
        for n in range(len(enmax_sorted)):
            if enmax_sorted[n] in eleIVB:
                magmom[n] = '4*0'
            if enmax_sorted[n] in eleVB:
                magmom[n] = '4*3'
            if enmax_sorted[n] in eleVIB:
                magmom[n] = '4*-4'
            if enmax_sorted[n] in eleIIIA:
                magmom[n] = '4*0'
    else:
        # Determine sorting of magnetic moments based on order from POTCAR
        magmom=[None]*4
        for n in range(len(enmax_sorted)):
            if enmax_sorted[n] in eleIVB:
                magmom[n] = '4*2'
            if enmax_sorted[n] in eleVB:
                magmom[n] = '4*3'
            if enmax_sorted[n] in eleVIB:
                magmom[n] = '4*-4'
            if enmax_sorted[n] in eleIIIA:
                magmom[n] = '4*1'  
    
    # Insert actual elements and proper initial magnetic moments
    for i in np.arange(len(lines)):
        if "alloy" in lines[i]:
            if not name.tag:
                lines[i]=lines[i].replace("alloy",
                                          "{}{}{}{}".format(alloy[0],
                                                            alloy[1],
                                                            alloy[2],
                                                            alloy[3]),1)
            else:
                lines[i]=lines[i].replace("alloy",
                                          "{}{}{}{}_{}".format(alloy[0],
                                                               alloy[1],
                                                               alloy[2],
                                                               alloy[3],
                                                               name.tag),1)
        if "Element" in lines[i]:
            lines[i]=lines[i].replace("Element1","{}"
                                      .format(enmax_sorted[0]),1)
            lines[i]=lines[i].replace("Element2","{}"
                                      .format(enmax_sorted[1]),1)
            lines[i]=lines[i].replace("Element3","{}"
                                      .format(enmax_sorted[2]),1)
            lines[i]=lines[i].replace("Element4","{}"
                                      .format(enmax_sorted[3]),1)
        if "MAGMOM" in lines[i]:
            lines[i]=lines[i].replace("x",
                                      "{} {} {} {}".format(magmom[0],
                                                           magmom[1],
                                                           magmom[2],
                                                           magmom[3]))
        #_____can add any other special tags in INCAR file here
        # Change functional method for VASP (if necessary)
        if "woSCAN" in name.tag and "METAGGA" in lines[i]:
            lines[i]=lines[i].replace("METAGGA = SCAN","!METAGGA = SCAN",1)
        # Set Pullay stress (if necessary)
        if "pstress" in name.tag and "!PSTRESS" in lines[i]:
                pstress=name.tag.replace("pstress","",1)
                pstress=pstress[:pstress.find("kbar")]
                lines[i]=lines[i].replace("!PSTRESS",
                                          "PSTRESS = {}\n".format(pstress),1)   
                
    # Write to new INCAR file
    with open("{}/INCAR".format(alloydir),"w") as f:
        for i in lines:
            f.write(i)
    return

def genkpts(name,homedir,alloydir):
    alloy=name.alloyaslist
    # Read in KPOINTS template file
    with open("{}/KPOINTS_template".format(homedir),"r") as f:
        lines=np.array(f.readlines(), dtype='object')
        
    # Insert actual system name and tag
    for i in np.arange(len(lines)):
        if "alloy" in lines[i]:
            if not name.tag:
                lines[i]=lines[i].replace("alloy",
                                          "{}{}{}{}".format(alloy[0],
                                                            alloy[1],
                                                            alloy[2],
                                                            alloy[3]),1)
            else:
                lines[i]=lines[i].replace("alloy",
                                          "{}{}{}{}_{}".format(alloy[0],
                                                               alloy[1],
                                                               alloy[2],
                                                               alloy[3],
                                                               name.tag),1)           
                
    # Write to new KPOINTS file
    with open("{}/KPOINTS".format(alloydir),"w") as f:
        for i in lines:
            f.write(i)
    return

def genpotcar(name,pot_tag,alloydir):
    alloy=name.alloyaslist
    os.chdir("/scratch/bansilgroup/pseudopotentials/PBE54")
    
    potcar=[]
    for i in range(len(alloy)):
        potcar.append(alloy[i]+pot_tag[i])
    
    ENMAX=[]
    for i in range(len(alloy)):
        ENMAX.append(searchextract(str(
            subprocess.check_output("grep ENMAX {}/POTCAR"
                                    .format(potcar[i]),shell=True)),
            "   ENMAX  =  ",r_strip=";"))
    
    alloydict = dict(zip(alloy,ENMAX))
    potcardict = dict(zip(potcar,ENMAX))
    
    enmax_sorted = sorted(alloy, key=alloydict.__getitem__, reverse=True)
    potcar_sorted = sorted(potcar, key=potcardict.__getitem__, reverse=True)
    
    #/home/winter.ga/DFT/HeuslerMaterials/POTCAR
    cmd = ("cat {}/POTCAR {}/POTCAR {}/POTCAR {}/POTCAR>{}/POTCAR"
           .format(potcar_sorted[0],
                   potcar_sorted[1],
                   potcar_sorted[2],
                   potcar_sorted[3],
                   alloydir))
    subprocess.call(cmd,shell=True)
    return enmax_sorted

def genposcar(name,enmax_sorted,latparam,homedir,alloydir):
    alloy=name.alloyaslist
    # Read in POSCAR template file
    with open("{}/POSCAR_template".format(homedir),"r") as f:
        lines=np.array(f.readlines(), dtype='object')
    
    pos=[None]*4
    
    # Absolute corner + outside face - 1st along (111) body diagonal
    pos[0] = ["     0.000000000         0.000000000         0.000000000 \n",
              "     0.000000000         0.500000000         0.500000000 \n",
              "     0.500000000         0.000000000         0.500000000 \n",
              "     0.500000000         0.500000000         0.000000000 \n"]
                
    # Inside corner 1 - 2nd along (111) body diagonal
    pos[1] = ["     0.250000000         0.250000000         0.250000000 \n",
              "     0.750000000         0.750000000         0.250000000 \n",
              "     0.750000000         0.250000000         0.750000000 \n",
              "     0.250000000         0.750000000         0.750000000 \n"]
    
    # Middle outside + dead center - 3rd along (111) body diagonal
    pos[2] = ["     0.500000000         0.500000000         0.500000000 \n",
              "     0.500000000         0.000000000         0.000000000 \n",
              "     0.000000000         0.500000000         0.000000000 \n",
              "     0.000000000         0.000000000         0.500000000 \n"]
    
    # Inside corner 2 - 4th along (111) body diagonal
    pos[3] = ["     0.750000000         0.750000000         0.750000000 \n",
              "     0.250000000         0.250000000         0.750000000 \n",
              "     0.250000000         0.750000000         0.250000000 \n",
              "     0.750000000         0.250000000         0.250000000 \n"]
    
     
    # Insert calculated lattice parameter and change arrangement
    for i in np.arange(len(lines)):
        if "latparam" in lines[i]:
            lines[i]=lines[i].replace("latparam",str(latparam),1)
        if "Element" in lines[i]:
            if len(enmax_sorted[0])<2:
                lines[i]=lines[i].replace("Element1"," {}"
                                          .format(enmax_sorted[0]),1)
            else:
                lines[i]=lines[i].replace("Element1",enmax_sorted[0],1)
            if len(enmax_sorted[1])<2:
                lines[i]=lines[i].replace("Element2"," {}"
                                          .format(enmax_sorted[1]),1)
            else:
                lines[i]=lines[i].replace("Element2",enmax_sorted[1],1)
            if len(enmax_sorted[2])<2:
                lines[i]=lines[i].replace("Element3"," {}"
                                          .format(enmax_sorted[2]),1)
            else:
                lines[i]=lines[i].replace("Element3",enmax_sorted[2],1)
            if len(enmax_sorted[3])<2:
                lines[i]=lines[i].replace("Element4"," {}"
                                          .format(enmax_sorted[3]),1)
            else:
                lines[i]=lines[i].replace("Element4",enmax_sorted[3],1)
            
            for m in range(len(enmax_sorted)):
                for n in range(len(alloy)):
                    if enmax_sorted[m]==alloy[n]:
                        lines=np.append(lines,pos[n],axis=0)
    
    # Write to new POSCAR file
    with open("{}/POSCAR".format(alloydir),"w") as f:
        for i in lines:
            f.write(i)
    return


#from mgmt import Name
#home=os.getcwd()
#name = Name("Ti-Cr-V-Al","")
#pot_tags, latparam = genalloymetadata(name)
#genposcar(name,["Ti","V","Al","Cr"],latparam,home,home)
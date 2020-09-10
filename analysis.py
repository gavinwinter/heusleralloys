# -*- coding: utf-8 -*-
"""
Control overall graphing and analysis.
"""

#-----------------------------------------
#clear previous variables
for name in dir():
    if not name.startswith("_"):
        del globals()[name]

#-----------------------------------------
# Import modules
import os
import graphing
from graphing import dos_graph, dos_graph_soc, bs_graph, extract
import pandas as pd



def analyzethat(lock,homedir,name,enmax_sorted):
    alloy=name.alloyaslist
    
    os.chdir(homedir)
    os.chdir(name.alloy_tag)
    alloydir=os.getcwd()
    savedir = "{}/Results".format(alloydir)
    
    # Make directory for Results
    if not os.path.exists(savedir):
        os.mkdir(savedir)
    
    # DOS graph
    rawdatadir = "{}/DOS".format(alloydir)
    graphing.dos_graph(rawdatadir,savedir,total_dos=True,by_element=True)
    
    # BS graph
    rawdatadir = "{}/BS".format(alloydir)
    graphing.bs_graph(rawdatadir,savedir,dos_graph.e_fermi)
    
    # Extract other data (for moments, etc)
    rawdatadir = "{}/DOS".format(alloydir)
    graphing.extract(rawdatadir,alloy,enmax_sorted)
    
    # Creates dataframe for reading/writing to csv
    labels=["Name","Free Energy","Energy without Entropy","Lattice parameter",
            "Fermi Energy from DOS","Band Gap from DOS","Band Gap from BS",
            "Majority vbm","Majority cbm","Minority vbm","Minority cbm",
            "Majority gap","Minority gap","Electronic gap",
            "Total Mag of Unit Cell (by Bravais matrix)",
            "Sum Mag Moms (by Wigner-Seitz Radius)",
            "Mag Moms (by Wigner-Seitz Radius)","Other notes"]
    data = {"Name": extract.name,
            "Free Energy": extract.free_energy,
            "Energy without Entropy": extract.energy_wo_entropy,
            "Lattice parameter": extract.latparam,
            "Fermi Energy from DOS": dos_graph.e_fermi,
            "Band Gap from DOS": dos_graph.band_gap,
            "Band Gap from BS": bs_graph.band_gap,
            "Majority vbm": dos_graph.majority_vbm,
            "Majority cbm": dos_graph.majority_cbm,
            "Minority vbm": dos_graph.minority_vbm,
            "Minority cbm": dos_graph.minority_cbm,
            "Majority gap": dos_graph.majority_gap,
            "Minority gap": dos_graph.minority_gap,
            "Electronic gap": dos_graph.electronic_gap,
            "Total Mag of Unit Cell (by Bravais matrix)": extract.tot_mag,
            "Sum Mag Moms (by Wigner-Seitz Radius)": extract.sum_mag_mom_rwigs,
            "Mag Moms (by Wigner-Seitz Radius)": extract.mag_mom_rwigs_diag,
            "Other notes": name.tag}
    
    # Lock needed for multiple processes reading/writing to csv
    lock.acquire()
    if os.path.exists("{}/summary.csv".format(homedir)):
        existing_df = pd.read_csv("{}/summary.csv".format(homedir),index_col=0)
    else:
        existing_df = pd.DataFrame(columns=labels)
    df = existing_df.append(data,ignore_index=True)
    df.to_csv("{}/summary.csv".format(homedir))
    lock.release()
    
    return

def analyzethat_soc(lock,homedir,name,enmax_sorted):
    alloy=name.alloyaslist
    
    os.chdir(homedir)
    os.chdir(name.alloy_tag)
    alloydir=os.getcwd()
    savedir = "{}/Results_SOC".format(alloydir)
    
    # Make directory for Results
    if not os.path.exists(savedir):
        os.mkdir(savedir)
    
    # DOS graph
    rawdatadir = "{}/DOS_SOC".format(alloydir)
    graphing.dos_graph_soc(rawdatadir,savedir)
    
    # BS graph
    rawdatadir = "{}/BS_SOC".format(alloydir)
    graphing.bs_graph(rawdatadir,savedir,dos_graph_soc.e_fermi,soc=True)
    
    # Extract other data (for moments, etc)
    rawdatadir = "{}/DOS_SOC".format(alloydir)
    graphing.extract(rawdatadir,alloy,enmax_sorted,soc=True)
    
    # Creates dataframe for reading/writing to csv
    labels=["Name","Free Energy","Energy without Entropy","Lattice parameter",
            "Fermi Energy from DOS","Electronic gap",
            "Total Mag_x of Unit Cell (by Bravais matrix)",
            "Total Mag_y of Unit Cell (by Bravais matrix)",
            "Total Mag_z of Unit Cell (by Bravais matrix)",
            "Sum Mag_x Moms (by Wigner-Seitz Radius)",
            "Mag_x Moms (by Wigner-Seitz Radius)",
            "Sum Orb Moms_x","Orb Moms_x",
            "Sum Mag_y Moms (by Wigner-Seitz Radius)",
            "Mag_y Moms (by Wigner-Seitz Radius)",
            "Sum Orb Moms_y","Orb Moms_y",
            "Sum Mag_z Moms (by Wigner-Seitz Radius)",
            "Mag_z Moms (by Wigner-Seitz Radius)",
            "Sum Orb Moms_z","Orb Moms_z","Other notes"]
    data = {"Name": extract.name,
            "Free Energy": extract.free_energy,
            "Energy without Entropy": extract.energy_wo_entropy,
            "Lattice parameter": extract.latparam,
            "Fermi Energy from DOS": dos_graph_soc.e_fermi,
            "Electronic gap": dos_graph_soc.electronic_gap,
            "Total Mag_x of Unit Cell (by Bravais matrix)": extract.tot_mag_x,
            "Total Mag_y of Unit Cell (by Bravais matrix)": extract.tot_mag_y,
            "Total Mag_z of Unit Cell (by Bravais matrix)": extract.tot_mag_z,
            "Sum Mag_x Moms (by Wigner-Seitz Radius)": extract.sum_mag_x_mom_rwigs,
            "Mag_x Moms (by Wigner-Seitz Radius)": extract.mag_x_mom_rwigs_diag,
            "Sum Orb Moms_x": extract.sum_orbmom_x,
            "Orb Moms_x": extract.orbmom_x_diag,
            "Sum Mag_y Moms (by Wigner-Seitz Radius)": extract.sum_mag_y_mom_rwigs,
            "Mag_y Moms (by Wigner-Seitz Radius)": extract.mag_y_mom_rwigs_diag,
            "Sum Orb Moms_y": extract.sum_orbmom_y,
            "Orb Moms_y": extract.orbmom_y_diag,
            "Sum Mag_z Moms (by Wigner-Seitz Radius)": extract.sum_mag_z_mom_rwigs,
            "Mag_z Moms (by Wigner-Seitz Radius)": extract.mag_z_mom_rwigs_diag,
            "Sum Orb Moms_z": extract.sum_orbmom_z,
            "Orb Moms_z": extract.orbmom_z_diag,
            "Other notes": "SOC, {}".format(name.tag)}
    
    # Lock needed for multiple processes reading/writing to csv
    lock.acquire()
    if os.path.exists("{}/summary_SOC.csv".format(homedir)):
        existing_df = pd.read_csv("{}/summary_SOC.csv".format(homedir),index_col=0)
    else:
        existing_df = pd.DataFrame(columns=labels)
    df = existing_df.append(data,ignore_index=True)
    df.to_csv("{}/summary_SOC.csv".format(homedir))
    lock.release()
    
    return
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 19:21:09 2019

@author: Gavin

Graphing density of states from vasprun using pymatgen.
Graphing band structure from vasprun using pymatgen.
Extract additional info.
"""

#-----------------------------------------
#clear previous variables
for name in dir():
    if not name.startswith("_"):
        del globals()[name]

#-----------------------------------------
# Import modules
import numpy as np
import pymatgen
from pymatgen.io.vasp.outputs import BSVasprun, Vasprun, Outcar, Eigenval
from pymatgen.electronic_structure.core import Spin, SpinNonCollinear, Orbital
from pymatgen.electronic_structure.plotter import BSPlotter, DosPlotter
from pymatgen.electronic_structure.dos import DOS, Dos
from pymatgen.electronic_structure.bandstructure import BandStructure
from pymatgen.io.vasp.outputs import Eigenval
from pymatgen.io.vasp import Poscar
from pymatgen.core.lattice import Lattice
from mgmt import searchextract
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

#import os



def dos_graph(rawdatadir,savedir,
              total_dos=True,by_element=False,by_orbital=False):
    dosrun = Vasprun("{}/vasprun.xml".format(rawdatadir), parse_dos=True)
    dos = dosrun.complete_dos
    
    # Get basic plot
    dos_graph.e_fermi=float(dosrun.efermi)
    dos_graph.band_gap=float(dosrun.eigenvalue_band_properties[0])
    dosplot = DosPlotter()
    #dosplot = DosPlotter(sigma=0.1)
    if total_dos==True:
        dosplot.add_dos("Total DOS", dos)
    if by_element==True:
        dosplot.add_dos_dict(dos.get_element_dos())
    if by_orbital==True:
        dosplot.add_dos_dict(dos.get_spd_dos())
    plt = dosplot.get_plot(xlim=[-3,3],ylim=[-15,15], element_colors=True)
    plt.grid()
    plt.savefig("{}/DOSGraph".format(savedir))
    plt.close()
    
    
    # Get plot for comparison with SOC total DOS plot
    dosplot = DosPlotter()    
    dosplot.add_dos("Total DOS without SOC", dos)
    dosplot.add_dos_dict(dos.get_element_dos())
    plt = dosplot.get_plot_total(xlim=[-3,3], element_colors=True)
    plt.grid()
    plt.savefig("{}/DOSGraph_tot_DOS by Element without SOC".format(savedir))
    plt.close()
    
    dosplot = DosPlotter()        
    orbitals = {"s": Orbital.s,
                "p_y": Orbital.py, "p_z": Orbital.pz, "p_x": Orbital.px,
                "d_xy": Orbital.dxy, "d_yz": Orbital.dyz, 
                "d_z2-r2": Orbital.dz2, "d_xz": Orbital.dxz, 
                "d_x2-y2": Orbital.dx2}
    dosplot.add_dos("Total DOS without SOC", dos)
    dosplot.add_dos_dict(dos.get_orbital_dos())
    plt = dosplot.get_plot_total(xlim=[-3,3])
    plt.grid()
    plt.savefig("{}/DOSGraph_tot_DOS by Orbital without SOC".format(savedir))
    plt.close()
   
    """
    # Get quick info about band gap (source: EIGENVAL)
    eigenval = Eigenval("{}/EIGENVAL".format(rawdatadir))
    dos_graph.band_properties = eigenval.eigenvalue_band_properties
    """
    # Get detailed info about band gap and CB/VB in each spin channel
    # (source: vasprun.xml)
    dos_graph.majority_vbm = \
        dosrun.tdos.get_cbm_vbm_alt(xlim=[-3,3],e_fermi=dos_graph.e_fermi,
                                    tol=0.3,abs_tol=True,spin=Spin.up)[1]
    dos_graph.majority_cbm = \
        dosrun.tdos.get_cbm_vbm_alt(xlim=[-3,3],e_fermi=dos_graph.e_fermi,
                                    tol=0.3,abs_tol=True,spin=Spin.up)[0]
    dos_graph.minority_vbm = \
        dosrun.tdos.get_cbm_vbm_alt(xlim=[-3,3],e_fermi=dos_graph.e_fermi,
                                    tol=0.3,abs_tol=True,spin=Spin.down)[1]
    dos_graph.minority_cbm = \
        dosrun.tdos.get_cbm_vbm_alt(xlim=[-3,3],e_fermi=dos_graph.e_fermi,
                                    tol=0.3,abs_tol=True,spin=Spin.down)[0]
    dos_graph.majority_gap = \
        dosrun.tdos.get_gap_alt(xlim=[-3,3],e_fermi=dos_graph.e_fermi,
                                tol=0.3,abs_tol=True,spin=Spin.up)
    dos_graph.minority_gap = \
        dosrun.tdos.get_gap_alt(xlim=[-3,3],e_fermi=dos_graph.e_fermi,
                                tol=0.3,abs_tol=True,spin=Spin.down)
    dos_graph.electronic_gap = \
        dosrun.tdos.get_gap_alt(xlim=[-3,3],e_fermi=dos_graph.e_fermi,
                                tol=0.3,abs_tol=True,spin=None)
    
    return



def dos_graph_soc(rawdatadir,savedir):
    dosrun = Vasprun("{}/vasprun.xml".format(rawdatadir),
                     soc=True, parse_dos=True)
    dos = dosrun.complete_dos
    
    orbitals = {"s": Orbital.s,
                "p_y": Orbital.py, "p_z": Orbital.pz, "p_x": Orbital.px,
                "d_xy": Orbital.dxy, "d_yz": Orbital.dyz,
                "d_z2-r2": Orbital.dz2, "d_xz": Orbital.dxz,
                "d_x2-y2": Orbital.dx2}
    spinor_component = {"mtot": SpinNonCollinear.mtot,
                        "mx": SpinNonCollinear.mx,
                        "my": SpinNonCollinear.my,
                        "mz": SpinNonCollinear.mz}  
    
    for m in spinor_component:
        dosplot = DosPlotter()
        if m == "mtot":
            dosplot.add_dos("Total DOS with SOC", dos.tdos)
        dosplot.add_dos_dict(dos.get_element_dos())
        plt = dosplot.get_plot(xlim=[-3,3], soc=True,
                               spinor_component=spinor_component[m],
                               element_colors=True)
        plt.grid()
        plt.savefig("{}/DOSGraph_{}_{}"
                    .format(savedir,m,"DOS by Element with SOC"))
        plt.close()    
    
    for m in spinor_component:
        dosplot = DosPlotter()
        if m == "mtot":
            dosplot.add_dos("Total DOS with SOC", dos.tdos)
        dosplot.add_dos_dict(dos.get_orbital_dos())
        plt = dosplot.get_plot(xlim=[-3,3], soc=True,
                               spinor_component=spinor_component[m])
        plt.grid()
        plt.savefig("{}/DOSGraph_{}_{}"
                    .format(savedir,m,"DOS by Orbital with SOC"))
        plt.close() 
    
    # Get detailed info about band gap (source: vasprun.xml)
    dos_graph_soc.e_fermi=float(dosrun.efermi)
    dos_graph_soc.electronic_gap = \
        dosrun.tdos.get_gap_alt(xlim=[-3,3],e_fermi=dos_graph_soc.e_fermi,
                                tol=0.001,abs_tol=False,
                                spin=SpinNonCollinear.mtot) 
        
    return



def bs_graph(rawdatadir,savedir,e_fermi,soc=False):
    run = BSVasprun("{}/vasprun.xml".format(rawdatadir),
                    parse_projected_eigen=True)
    bs = run.get_band_structure(efermi=e_fermi,line_mode=True,
                                force_hybrid_mode=True)  
    bsplot = BSPlotter(bs)
    
    # Get the plot
    bsplot.get_plot(vbm_cbm_marker=True, ylim=(-1.5, 1.5), zero_to_efermi=True)
    bs_graph.e_fermi=float(bs.efermi)
    bs_graph.band_gap=float(bs.get_band_gap()["energy"])
    ax = plt.gca()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ax.hlines(0, xlim[0], xlim[1], linestyle="--", color="black")
    ax.tick_params(labelsize=20)
    if not soc:
        ax.plot((), (), "r-", label="spin up")
        ax.plot((), (), "b-", label="spin down")
        ax.legend(fontsize=16, loc="upper left")
    plt.savefig("{}/BSGraph".format(savedir))
    plt.close()
    
    if not soc:
        # Print quick info about band gap (source: vasprun.xml)
        #print(bs_graph.e_fermi)
        #print(bs_graph.band_gap)
        
        # Get quick info about band gap (source: EIGENVAL)
        eigenval = Eigenval("{}/EIGENVAL".format(rawdatadir))
        bs_graph.band_properties = eigenval.eigenvalue_band_properties
        
        # Get detailed info about band gap and CB/VB in each spin channel 
        # (source: EIGENVAL)
        bs_graph.eigenvalues = eigenval.eigenvalues
        bs_graph.kpoints = eigenval.kpoints
        poscar = Poscar.from_file("{}/POSCAR".format(rawdatadir))
        bs_graph.lattice = poscar.structure.lattice.reciprocal_lattice
        
        bs_graph.eigenvalues[Spin.up] = bs_graph.eigenvalues[Spin.up][:,:,:-1]
        bs_graph.eigenvalues[Spin.down] = bs_graph.eigenvalues[Spin.down][:,:,:-1]
        bs_graph.eigenvalues[Spin.up] = bs_graph.eigenvalues[Spin.up][:,:,0]
        bs_graph.eigenvalues[Spin.down] = bs_graph.eigenvalues[Spin.down][:,:,0]
        
        bs_graph.eigenvalues[Spin.up] = \
            np.transpose(bs_graph.eigenvalues[Spin.up])
        bs_graph.eigenvalues[Spin.down] = \
            np.transpose(bs_graph.eigenvalues[Spin.down])
        
        bs = BandStructure(bs_graph.kpoints,bs_graph.eigenvalues,
                           bs_graph.lattice,bs_graph.e_fermi)
        bs_graph.vbm = bs.get_vbm()["energy"]
        bs_graph.cbm = bs.get_cbm()["energy"]
        bs_graph.electronic_gap = bs.get_band_gap()["energy"]
        bs_graph.direct = bs.get_band_gap()["direct"]
        if bs_graph.vbm and bs_graph.cbm and bs_graph.electronic_gap:
            bs_graph.gap_by_spin = bs.get_direct_band_gap_dict()
    return



def extract(rawdatadir,alloy,enmax_sorted,soc=False):
    # Extract alloy name and ordering
    elements=[ele for ele in enmax_sorted for i in range(4)]
    extract.name=alloy[0]+alloy[1]+alloy[2]+alloy[3]
    
    # Extract magnetic moments of individual species from OUTCAR
    outcar = Outcar("{}/OUTCAR".format(rawdatadir))
    
    if not soc:
        extract.mag_mom_rwigs={}
                
        extract.sum_mag_mom_rwigs=0
        for i in range(len(outcar.magnetization)):
            extract.mag_mom_rwigs[i+1]=(elements[i],
                                        outcar.magnetization[i]['tot'])
            extract.sum_mag_mom_rwigs+=float(outcar.magnetization[i]['tot']) 
        
        extract.mag_mom_rwigs_diag={}
        for i in range(len(alloy)):
            if alloy[i] == extract.mag_mom_rwigs[1][0]:
                extract.mag_mom_rwigs_diag[i] = extract.mag_mom_rwigs[1]
            if alloy[i] == extract.mag_mom_rwigs[5][0]:
                extract.mag_mom_rwigs_diag[i] = extract.mag_mom_rwigs[5]
            if alloy[i] == extract.mag_mom_rwigs[9][0]:
                extract.mag_mom_rwigs_diag[i] = extract.mag_mom_rwigs[9]
            if alloy[i] == extract.mag_mom_rwigs[13][0]:
                extract.mag_mom_rwigs_diag[i] = extract.mag_mom_rwigs[13]
                
        # Extract total magnetic moment from OSZICAR
        with open("{}/OSZICAR".format(rawdatadir),"r") as f:
            lines=np.array(f.readlines())
        for i in np.arange(len(lines)):
            if lines[i].startswith("   1 F= "):
                extract.tot_mag=searchextract(lines[i],"mag=")
    
    elif soc:
        # mag_x
        extract.mag_x_mom_rwigs={}
                
        extract.sum_mag_x_mom_rwigs=0
        for i in range(len(outcar.magnetization)):
            extract.mag_x_mom_rwigs[i+1]=(elements[i],
                                          outcar.magnetization[i]['tot']
                                          .get_moment(saxis=(0, 0, 1))[0])
            extract.sum_mag_x_mom_rwigs+=float(outcar.magnetization[i]['tot']
                                               .get_moment(saxis=(0, 0, 1))[0])
            
        extract.mag_x_mom_rwigs_diag={}
        for i in range(len(alloy)):
            if alloy[i] == extract.mag_x_mom_rwigs[1][0]:
                extract.mag_x_mom_rwigs_diag[i] = extract.mag_x_mom_rwigs[1]
            if alloy[i] == extract.mag_x_mom_rwigs[5][0]:
                extract.mag_x_mom_rwigs_diag[i] = extract.mag_x_mom_rwigs[5]
            if alloy[i] == extract.mag_x_mom_rwigs[9][0]:
                extract.mag_x_mom_rwigs_diag[i] = extract.mag_x_mom_rwigs[9]
            if alloy[i] == extract.mag_x_mom_rwigs[13][0]:
                extract.mag_x_mom_rwigs_diag[i] = extract.mag_x_mom_rwigs[13]
                
        # mag_y
        extract.mag_y_mom_rwigs={}
                
        extract.sum_mag_y_mom_rwigs=0
        for i in range(len(outcar.magnetization)):
            extract.mag_y_mom_rwigs[i+1]=(elements[i],
                                          outcar.magnetization[i]['tot']
                                          .get_moment(saxis=(0, 0, 1))[1])
            extract.sum_mag_y_mom_rwigs+=float(outcar.magnetization[i]['tot']
                                               .get_moment(saxis=(0, 0, 1))[1])
            
        extract.mag_y_mom_rwigs_diag={}
        for i in range(len(alloy)):
            if alloy[i] == extract.mag_y_mom_rwigs[1][0]:
                extract.mag_y_mom_rwigs_diag[i] = extract.mag_y_mom_rwigs[1]
            if alloy[i] == extract.mag_y_mom_rwigs[5][0]:
                extract.mag_y_mom_rwigs_diag[i] = extract.mag_y_mom_rwigs[5]
            if alloy[i] == extract.mag_y_mom_rwigs[9][0]:
                extract.mag_y_mom_rwigs_diag[i] = extract.mag_y_mom_rwigs[9]
            if alloy[i] == extract.mag_y_mom_rwigs[13][0]:
                extract.mag_y_mom_rwigs_diag[i] = extract.mag_y_mom_rwigs[13]
        
        # mag_z
        extract.mag_z_mom_rwigs={}
                
        extract.sum_mag_z_mom_rwigs=0
        for i in range(len(outcar.magnetization)):
            extract.mag_z_mom_rwigs[i+1]=(elements[i],
                                          outcar.magnetization[i]['tot']
                                          .get_moment(saxis=(0, 0, 1))[2])
            extract.sum_mag_z_mom_rwigs+=float(outcar.magnetization[i]['tot']
                                               .get_moment(saxis=(0, 0, 1))[2])
            
        extract.mag_z_mom_rwigs_diag={}
        for i in range(len(alloy)):
            if alloy[i] == extract.mag_z_mom_rwigs[1][0]:
                extract.mag_z_mom_rwigs_diag[i] = extract.mag_z_mom_rwigs[1]
            if alloy[i] == extract.mag_z_mom_rwigs[5][0]:
                extract.mag_z_mom_rwigs_diag[i] = extract.mag_z_mom_rwigs[5]
            if alloy[i] == extract.mag_z_mom_rwigs[9][0]:
                extract.mag_z_mom_rwigs_diag[i] = extract.mag_z_mom_rwigs[9]
            if alloy[i] == extract.mag_z_mom_rwigs[13][0]:
                extract.mag_z_mom_rwigs_diag[i] = extract.mag_z_mom_rwigs[13]
                
        # orbmom_x
        extract.orbmom_x={}
                
        extract.sum_orbmom_x=0
        for i in range(len(outcar.orbital_moment)):
            extract.orbmom_x[i+1]=(elements[i],
                                   outcar.orbital_moment[i]['tot'][0])
            extract.sum_orbmom_x+=float(outcar.orbital_moment[i]['tot'][0])
            
        extract.orbmom_x_diag={}
        for i in range(len(alloy)):
            if alloy[i] == extract.orbmom_x[1][0]:
                extract.orbmom_x_diag[i] = extract.orbmom_x[1]
            if alloy[i] == extract.orbmom_x[5][0]:
                extract.orbmom_x_diag[i] = extract.orbmom_x[5]
            if alloy[i] == extract.orbmom_x[9][0]:
                extract.orbmom_x_diag[i] = extract.orbmom_x[9]
            if alloy[i] == extract.orbmom_x[13][0]:
                extract.orbmom_x_diag[i] = extract.orbmom_x[13]
                
        # orbmom_y
        extract.orbmom_y={}
                
        extract.sum_orbmom_y=0
        for i in range(len(outcar.orbital_moment)):
            extract.orbmom_y[i+1]=(elements[i],
                                   outcar.orbital_moment[i]['tot'][1])
            extract.sum_orbmom_y+=float(outcar.orbital_moment[i]['tot'][1])
            
        extract.orbmom_y_diag={}
        for i in range(len(alloy)):
            if alloy[i] == extract.orbmom_y[1][0]:
                extract.orbmom_y_diag[i] = extract.orbmom_y[1]
            if alloy[i] == extract.orbmom_y[5][0]:
                extract.orbmom_y_diag[i] = extract.orbmom_y[5]
            if alloy[i] == extract.orbmom_y[9][0]:
                extract.orbmom_y_diag[i] = extract.orbmom_y[9]
            if alloy[i] == extract.orbmom_y[13][0]:
                extract.orbmom_y_diag[i] = extract.orbmom_y[13]
                
        # orbmom_z
        extract.orbmom_z={}
                
        extract.sum_orbmom_z=0
        for i in range(len(outcar.orbital_moment)):
            extract.orbmom_z[i+1]=(elements[i],
                                   outcar.orbital_moment[i]['tot'][2])
            extract.sum_orbmom_z+=float(outcar.orbital_moment[i]['tot'][2])
            
        extract.orbmom_z_diag={}
        for i in range(len(alloy)):
            if alloy[i] == extract.orbmom_z[1][0]:
                extract.orbmom_z_diag[i] = extract.orbmom_z[1]
            if alloy[i] == extract.orbmom_z[5][0]:
                extract.orbmom_z_diag[i] = extract.orbmom_z[5]
            if alloy[i] == extract.orbmom_z[9][0]:
                extract.orbmom_z_diag[i] = extract.orbmom_z[9]
            if alloy[i] == extract.orbmom_z[13][0]:
                extract.orbmom_z_diag[i] = extract.orbmom_z[13]
        
        # Extract total magnetic moments from OSZICAR
        with open("{}/OSZICAR".format(rawdatadir),"r") as f:
            lines=np.array(f.readlines())
        for i in np.arange(len(lines)):
            if lines[i].startswith("   1 F= "):
                extract.tot_mag_x= \
                    float(searchextract(lines[i],"mag=",return_string=True)[0])
                extract.tot_mag_y= \
                    float(searchextract(lines[i],"mag=",return_string=True)[1])
                extract.tot_mag_z= \
                    float(searchextract(lines[i],"mag=",return_string=True)[2])

    # Extract other data about overall system from OUTCAR
    with open("{}/OUTCAR".format(rawdatadir),"r") as f:
        lines=np.array(f.readlines())
    for i in np.arange(len(lines)):
        # Extract additional energy data
        if lines[i].startswith("  free  energy   TOTEN  ="):
            extract.free_energy=searchextract(lines[i],
                                              "  free  energy   TOTEN  =")
        if lines[i].startswith("  energy  without entropy=     "):
            extract.energy_wo_entropy=searchextract(lines[i],
                                                    "  energy  without entropy=")
            extract.energy_sigma0=searchextract(lines[i],
                                                "  energy(sigma->0) =")
        # Extract unit cell volume
        if lines[i].startswith("  volume of cell :"):
            extract.cell_volume=searchextract(lines[i],"  volume of cell :")
            
        # Extract lattice parameter
        if lines[i].startswith(" ALAT       ="):
            extract.latparam=searchextract(lines[i]," ALAT       =")
            
    return


#home = os.getcwd()
#os.chdir("DOS")
#homedir=os.getcwd()
#subdir=os.getcwd()
#dos_graph(homedir,subdir,total_dos=True,by_element=True)

#os.chdir(home)
#os.chdir("DOS_SOC")
#homedir=os.getcwd()
#subdir=os.getcwd()
#dos_graph_soc(homedir,subdir)

#print(dos_graph_soc.e_fermi)

#os.chdir(home)
#os.chdir("BS_SOC")
#homedir=os.getcwd()
#subdir=os.getcwd()
#bs_graph(homedir,subdir,7.95042847,soc=True)
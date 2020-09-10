# -*- coding: utf-8 -*-
"""
Create k-walk based on specified high-symmetry points.
"""

#-----------------------------------------
# Import modules
import numpy as np

def kpath(output_filname):
    # Designate high-symmetry points    
    gamma = [[0,0,0], "\Gamma"]
    x = [[0.5,0,0.5], "X"]
    w = [[0.5,0.25,0.75], "W"]
    k = [[0.375,0.375,0.75], "K"]
    l = [[0.5,0.5,0.5], "L"]
    u = [[0.625,0.25,0.625], "U"]

    weight = 0
    
    # Designate path between high-symmetry points
    # Path for space group F-43m (number 216)
    # From International Tables for Crystallography Volume A
    kpath_seg1 = [gamma, x, w, k, gamma, l, u, w, l, k]
    kpath_seg2 = [u, x]
    
    # Specify k-grid spacing
    gridspac = 50
    xcoord = []
    ycoord = []
    zcoord = []
    new_path = []

    
    lines = []
    for i in range(1,len(kpath_seg1)):
        xcoord.append(np.linspace(start= kpath_seg1[i-1][0][0],
                                  stop= kpath_seg1[i][0][0],num= gridspac+1))
        ycoord.append(np.linspace(start= kpath_seg1[i-1][0][1],
                                  stop= kpath_seg1[i][0][1],num= gridspac+1))
        zcoord.append(np.linspace(start= kpath_seg1[i-1][0][2],
                                  stop= kpath_seg1[i][0][2],num= gridspac+1))
        for n in range(len(xcoord[i-1])):
            if n == 0:
                lines = [xcoord[i-1][n],ycoord[i-1][n],zcoord[i-1][n],
                         weight,kpath_seg1[i-1][1]]
            elif n == (len(xcoord[i-1])-1):
                lines = [xcoord[i-1][n],ycoord[i-1][n],zcoord[i-1][n],
                         weight,kpath_seg1[i][1]]
            else:
                lines = [xcoord[i-1][n],ycoord[i-1][n],zcoord[i-1][n],
                         weight,'']
            new_path.append(lines)       

    xcoord = []
    ycoord = []
    zcoord = []       
    lines = []
    for i in range(1,len(kpath_seg2)):
        xcoord.append(np.linspace(start= kpath_seg2[i-1][0][0],
                                  stop= kpath_seg2[i][0][0],num= gridspac+1))
        ycoord.append(np.linspace(start= kpath_seg2[i-1][0][1],
                                  stop= kpath_seg2[i][0][1],num= gridspac+1))
        zcoord.append(np.linspace(start= kpath_seg2[i-1][0][2],
                                  stop= kpath_seg2[i][0][2],num= gridspac+1))
        for n in range(len(xcoord[i-1])):
            if n == 0:
                lines = [xcoord[i-1][n],ycoord[i-1][n],zcoord[i-1][n],
                         weight,kpath_seg2[i-1][1]]
            elif n == (len(xcoord[i-1])-1):
                lines = [xcoord[i-1][n],ycoord[i-1][n],zcoord[i-1][n],
                         weight,kpath_seg1[i][1]]
            else:
                lines = [xcoord[i-1][n],ycoord[i-1][n],zcoord[i-1][n],
                         weight,'']
            new_path.append(lines)      

    dt = np.dtype("float, float, float, float, U32")      
    kgrid=np.array([], dtype=dt)
    for i in range(0,len(new_path)):
        new_row = np.array([(new_path[i][0],new_path[i][1],new_path[i][2],
                             new_path[i][3],new_path[i][4])], dtype=dt)
        kgrid = np.concatenate((kgrid,new_row), axis=0)      
    
    np.savetxt(output_filname, kgrid,
               fmt=["%.7e", "%.7e", "%.7e", "%.7e", "%s"], delimiter="\t")
    
    return
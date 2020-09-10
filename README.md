# heuslers
Integrated workflow for assessing material properties of quaternary XX'YZ Heusler compounds using VASP

*Part of an undergraduate research project*

### Using the Workflow
`main.py` has primary control for submission of VASP jobs on SLURM and requires the other scripts as dependencies. This `main.py` script has a low memory requirement and can be run on the head node or on its own node. However, due to time limits on our cluster, `main.py` could not run for more than 24 hours, so checkpointing was implemented to allow for easy "resuming." The list `alloy` in `main.py` contains strings that specify the ordering of elements along the (111) body diagonal, and `tag` indicates any special modifications to be made to the conventional workflow (see next paragraph for examples). (Note that this ordering convention is not the typical XX'YZ convention for naming of quaternary Heuslers.) The status of the workflow (checkpointing) for a particular Heusler compound with ordering X-Y-X'-Z along the body diagonal is updated using the `exit_code` in the respective output file, named `output_X-Y-X'-Z` or `output_X-Y-X'-Z_tag.out`, if there is a `tag` associated with it. See `mgmt.py` for how checkpointing, errors, and job submission are handled.

As `main.py` initiates an embarrassingly parallel process, the conventional workflow for each Heusler compound runs the following steps sequentially and independently: (1) from cell using initial lattice parameter estimate (based on  atomic radii with additional 5% tolerance), relaxation is performed with ionic and electronic degrees of freedom (while also allowing changes to cell shape and volume), (2) the CONTCAR of the relaxed cell is then used in a self-consistent VASP calculation of density of states and a WAVECAR is generated, (3) charge density is then calculated from the wavefunctions contained in the WAVECAR for band structure calculations, and (4) finally requisite analysis is executed. The `stop_code` set in `main.py` determines what `exit_code` the independent parallel process reaches in the `main.py` script before terminating. While the conventional workflow does not include relativistic effects (`stop_code=5`), calculation and analysis with the effects of spin-orbit coupling can be performed by setting the `stop_code=8` for a given workflow.

`genvaspinfiles` handles generation of all VASP input files, including: modification of the POSCAR with the ordering along the diagonal and the KPOINTS file, concatenation of pseudopotentials into a POTCAR, and modification of the INCAR and batch job files as necessary. Modifications to the INCAR file using `genvaspinfiles` can be implemented using `tag` strings in `main.py`: to change the functional method for VASP (ex: `"woSCAN"`, SCAN meta-GGA is used otherwise), to change the initial magnetic moments (ex: `"magmomcheck1"`), and to indicate a workflow with incremental stress (ex: `"pstress0to100kbar"`). The workflow with incremental stress is the same as the conventional workflow outlined in the previous paragraph, except that Pulay stress is used to simulate hydrostatic stress on the lattice with relaxation performed at each subsqeuent step. Checkpointing still works in the same manner. Other custom run types could be implemented.

`analysis.py` graphs the density of states (decomposd by orbital, element, or site) and band structure, while also compiling a summary of data into a dataframe that is then exported to a .csv (continually updated with each Heusler compound). Data include free energy, lattice parameter, Fermi energy, valence band maximum, conduction band minimum, band gaps in respective spin channels, and magnetic moments by site defined by Wigner-Seitz radius or on the total cell. If the run included the effects of spin-orbit coupling, then the magnetic and orbital moments by site are also provided (decomposed by their spinor components).

Additional dependencies:
```
numpy
pandas
pymatgen
```

Note that all scripts requiring pymatgen as a dependency run on a forked version of `pymatgen` (not all changes are of interest to the broader community and thus were not merged with the current `pymatgen` version).

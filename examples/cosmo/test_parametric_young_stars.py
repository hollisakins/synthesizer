"""
Test the effect on the intrinsic emission of assuming a
parametric SFH for young star particles.

This is now implemented within call to `generate_lnu` 
on a parametric stars object.
"""

import numpy as np
from unyt import Myr
import matplotlib.pyplot as plt

from synthesizer.load_data.load_camels import load_CAMELS_IllustrisTNG
from synthesizer.grid import Grid
from synthesizer.parametric import SFH, ZDist, Stars
from synthesizer.parametric.galaxy import Galaxy


grid_dir = "../../tests/test_grid"
grid_name = "test_grid"
grid = Grid(grid_name, grid_dir=grid_dir)

gals = load_CAMELS_IllustrisTNG(
    "../../tests/data/",
    snap_name="camels_snap.hdf5",
    fof_name="camels_subhalo.hdf5",
    fof_dir="../../tests/data/",
)

# Select a single galaxy
gal = gals[1]

# Age limit at which we replace star particles
age_lim = 500 * Myr

"""
We first demonstrate the process *manually*.
This also allows us to obtain the SFH of each parametric
model for plotting purposes.
"""
# First, filter for star particles
pmask = gal.stars.ages < age_lim

stars = []
# Loop through each young star particle
for _pmask in np.where(pmask)[0]:
    # Parametric SFH parameters
    sfh_p = {"duration": age_lim}
    Z_p = {"metallicity": gal.stars.metallicities[_pmask]}
    stellar_mass = gal.stars.initial_masses[_pmask]

    # Initialise SFH and ZH objects
    sfh = SFH.Constant(**sfh_p)
    metal_dist = ZDist.DeltaConstant(**Z_p)  # constant metallicity

    # Create a parametric stars object
    stars.append(
        Stars(
            grid.log10age,
            grid.metallicity,
            sf_hist=sfh,
            metal_dist=metal_dist,
            initial_mass=stellar_mass,
        )
    )

# Sum each individual Stars object
stars = sum(stars[1:], stars[0])

# Create a parametric galaxy
para_gal = Galaxy(stars)

para_spec = para_gal.stars.get_spectra_incident(grid)
part_spec_old = gal.stars.get_spectra_incident(grid=grid, old=age_lim)
part_spec = gal.stars.get_spectra_incident(grid=grid)

"""
We can also do this directly from call to `generate_lnu`,
as well as any downstream `get_spectra_*` methods.
This shows an example on `get_spectra_incident`, supplying
the optional `parametric_young_stars` keyword argument.
"""

combined_spec = gal.stars.get_spectra_incident(
    grid=grid, parametric_young_stars=age_lim
)

assert (combined_spec.lnu == (part_spec_old.lnu + para_spec.lnu)).all()

"""
Plot intrinsic emission from pure particle, parametric
and parametric + particle models
"""
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

ax1.loglog(para_spec.lam, para_spec.lnu, label="Parametric young", color="C0")
ax1.loglog(
    part_spec_old.lam, part_spec_old.lnu, label="Particle old", color="C3"
)
ax1.loglog(
    part_spec.lam,
    part_spec.lnu,
    label="Particle all",
    color="C1",
    linestyle="dashed",
)
ax1.loglog(
    part_spec.lam,
    part_spec_old.lnu + para_spec.lnu,
    label="Para + Part",
    color="C2",
)
ax1.set_ylim(1e20, 1e30)
ax1.set_xlim(1e2, 2e4)
ax1.legend()
ax1.set_xlabel("$\lambda \,/\, \AA$")
ax1.set_ylabel("$L_{\lambda} / \mathrm{erg / Hz / s}$")

"""
Plot SFH from particles and parametric
"""
binLimits = np.linspace(5, 10, 30)

ax2.hist(
    np.log10(np.hstack([gal.stars.ages[~pmask].value, stars.ages.value])),
    histtype="step",
    weights=np.hstack([gal.stars.initial_masses[~pmask].value, stars.sf_hist]),
    bins=binLimits,
    log=True,
    label="Particle + Parametric",
    color="C2",
    linewidth=3,
)
ax2.hist(
    np.log10(gal.stars.ages),
    histtype="step",
    weights=gal.stars.initial_masses.value,
    bins=binLimits,
    log=True,
    label="All Particles",
    color="C1",
    linestyle="dashed",
    linewidth=3,
)
ax2.hist(
    np.log10(stars.ages.value),
    histtype="step",
    weights=stars.sf_hist,
    bins=binLimits,
    log=True,
    label="Young Parametric",
    color="C0",
    linewidth=3,
    linestyle="dashed",
)
ax2.legend()
# plt.show()
ax2.set_xlabel("$\mathrm{\log_{10} Age \,/\, yr}$")
ax2.set_ylabel("$\mathrm{log_{10} (Mass \,/\, M_{\odot})}$")

plt.show()
# plt.savefig("young_star_parametric.png", dpi=200, bbox_inches="tight")

""" A module for creating and manipulating parametric stellar populations.


"""
import h5py
import numpy as np
from scipy import integrate
from unyt import yr


import matplotlib.pyplot as plt
import cmasher as cmr

from synthesizer import exceptions
from synthesizer.components import StarsComponent
from synthesizer.stats import weighted_median, weighted_mean
from synthesizer.plt import single_histxy, mlabel


class Stars(StarsComponent):
    """
    The parametric stellar population object.

    This class holds a binned star formation and metal enrichment history
    describing the age and metallicity of the stellar population, an
    optional morphology model describing the distribution of those stars,
    and various other important attributes for defining a parametric
    stellar population.

    Attributes:
        log10ages (array-like, float)
        ages (Quantity, array-like, float)
        log10ages_lims (array_like_float)
        metallicities (array-like, float)
        metallicities_lims (array-like, float)
        log10metallicities (array-like, float)
        log10metallicities_lims (array-like, float)
        sfzh (array-like, float)
        sf_hist (array-like, float)
        metal_hist (array-like, float)
        sf_hist_func (function)
        metal_hist_func (function)
    """

    def __init__(
            self,
            log10ages,
            metallicities,
            sfzh,
            morphology=None,
            sf_hist_func=None,
            metal_hist_func=None,
    ):
        """
        Initialise the parametric stellar population.

        Args:
            log10ages
        """
        self.log10ages = log10ages
        self.ages = 10**log10ages
        self.log10ages_lims = [self.log10ages[0], self.log10ages[-1]]
        self.metallicities = metallicities
        self.metallicities_lims = [self.metallicities[0], self.metallicities[-1]]
        self.log10metallicities = np.log10(metallicities)
        self.log10metallicities_lims = [
            self.log10metallicities[0],
            self.log10metallicities[-1],
        ]
        self.sfzh = sfzh  # 2D star formation and metal enrichment history
        self.sf_hist = np.sum(self.sfzh, axis=1)  # 1D star formation history
        self.metal_hist = np.sum(self.sfzh, axis=0)  # metallicity distribution
        self.sf_hist_func = (
            sf_hist_func  # function used to generate the star formation history if given
        )
        self.metal_hist_func = metal_hist_func  # function used to generate the metallicity history/distribution if given

        # --- check if metallicities on regular grid in log10metallicity or metallicity or not at all (e.g. BPASS
        if len(set(self.metallicities[:-1] - self.metallicities[1:])) == 1:
            self.metallicity_grid = "Z"
        elif len(set(self.log10metallicities[:-1] - self.log10metallicities[1:])) == 1:
            self.metallicity_grid = "log10Z"
        else:
            self.metallicity_grid = None

    def calculate_median_age(self):
        """calculate the median age"""

        return weighted_median(self.ages, self.sf_hist) * yr

    def calculate_mean_age(self):
        """calculate the mean age"""

        return weighted_mean(self.ages, self.sf_hist) * yr

    def calculate_mean_metallicity(self):
        """calculate the mean metallicity"""

        return weighted_mean(self.metallicities, self.metal_hist)

    def __str__(self):
        """print basic summary of the binned star formation and metal enrichment history"""

        pstr = ""
        pstr += "-" * 10 + "\n"
        pstr += "SUMMARY OF BINNED SFZH" + "\n"
        pstr += f'median age: {self.calculate_median_age().to("Myr"):.2f}' + "\n"
        pstr += f'mean age: {self.calculate_mean_age().to("Myr"):.2f}' + "\n"
        pstr += f"mean metallicity: {self.calculate_mean_metallicity():.4f}" + "\n"
        pstr += "-" * 10 + "\n"
        return pstr

    def __add__(self, second_sfzh):
        """Add two SFZH histories together"""

        if second_sfzh.sfzh.shape == self.sfzh.shape:
            new_sfzh = self.sfzh + second_sfzh.sfzh

            return Stars(self.log10ages, self.metallicities, new_sfzh)

        else:
            raise exceptions.InconsistentAddition("SFZH must be the same shape")

    def plot(self, show=True):
        """Make a nice plots of the binned SZFH"""

        fig, ax, haxx, haxy = single_histxy()

        # this is technically incorrect because metallicity is not on a an actual grid.
        ax.pcolormesh(
            self.log10ages, self.log10metallicities, self.sfzh.T, cmap=cmr.sunburst
        )

        # --- add binned Z to right of the plot
        haxy.fill_betweenx(
            self.log10metallicities,
            self.metal_hist / np.max(self.metal_hist),
            step="mid",
            color="k",
            alpha=0.3,
        )

        # --- add binned SF_HIST to top of the plot
        haxx.fill_between(
            self.log10ages,
            self.sf_hist / np.max(self.sf_hist),
            step="mid",
            color="k",
            alpha=0.3,
        )

        # --- add SFR to top of the plot
        if self.sf_hist_func:
            x = np.linspace(*self.log10ages_lims, 1000)
            y = self.sf_hist_func.sfr(10**x)
            haxx.plot(x, y / np.max(y))

        haxy.set_xlim([0.0, 1.2])
        haxy.set_ylim(*self.log10metallicities_lims)
        haxx.set_ylim([0.0, 1.2])
        haxx.set_xlim(self.log10ages_lims)

        ax.set_xlabel(mlabel("log_{10}(age/yr)"))
        ax.set_ylabel(mlabel("log_{10}Z"))

        # Set the limits so all axes line up
        ax.set_ylim(*self.log10metallicities_lims)
        ax.set_xlim(*self.log10ages_lims)

        if show:
            plt.show()

        return fig, ax


def generate_sf_hist(ages, sf_hist_, log10=False):
    if log10:
        ages = 10**ages

    SF_HIST = np.zeros(len(ages))

    min_age = 0
    for ia, age in enumerate(ages[:-1]):
        max_age = int(np.mean([ages[ia + 1], ages[ia]]))  #  years
        sf = integrate.quad(sf_hist_.sfr, min_age, max_age)[0]
        SF_HIST[ia] = sf
        min_age = max_age

    # --- normalise
    SF_HIST /= np.sum(SF_HIST)

    return SF_HIST


def generate_instant_sfzh(
    log10ages, metallicities, log10age, metallicity, stellar_mass=1
):
    """simply returns the SFZH where only bin is populated corresponding to the age and metallicity"""

    sfzh = np.zeros((len(log10ages), len(metallicities)))
    ia = (np.abs(log10ages - log10age)).argmin()
    iZ = (np.abs(metallicities - metallicity)).argmin()
    sfzh[ia, iZ] = stellar_mass

    return Stars(log10ages, metallicities, sfzh)


def generate_sfzh(log10ages, metallicities, sf_hist, metal_hist, stellar_mass=1.0):
    """return an instance of the Stars class"""

    ages = 10**log10ages

    sfzh = np.zeros((len(log10ages), len(metallicities)))

    if metal_hist.dist == "delta":
        min_age = 0
        for ia, age in enumerate(ages[:-1]):
            max_age = int(np.mean([ages[ia + 1], ages[ia]]))  #  years
            sf = integrate.quad(sf_hist.sfr, min_age, max_age)[0]
            iZ = (np.abs(metallicities - metal_hist.Z(age))).argmin()
            sfzh[ia, iZ] = sf
            min_age = max_age

    if metal_hist.dist == "dist":
        print("WARNING: NOT YET IMPLEMENTED")

    # --- normalise
    sfzh /= np.sum(sfzh)
    sfzh *= stellar_mass

    return Stars(log10ages, metallicities, sfzh, sf_hist_func=sf_hist, metal_hist_func=metal_hist)


def generate_sfzh_from_array(log10ages, metallicities, sf_hist, metal_hist, stellar_mass=1.0):
    """
    Generated a Stars from an array instead of function
    """

    if not isinstance(metal_hist, np.ndarray):
        iZ = np.abs(metallicities - metal_hist).argmin()
        metal_hist = np.zeros(len(metallicities))
        metal_hist[iZ] = 1.0

    sfzh = sf_hist[:, np.newaxis] * metal_hist

    # --- normalise
    sfzh /= np.sum(sfzh)
    sfzh *= stellar_mass

    return Stars(log10ages, metallicities, sfzh)

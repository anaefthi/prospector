# A place to store handy parameter transormations

import numpy as np
from ..sources.constants import cosmo

__all__ = ["stellar_logzsol", "delogify_mass",
           "tburst_from_fage", "tage_from_tuniv", "zred_to_agebins",
           "dustratio_to_dust1",
           "zfrac_to_masses", "zfrac_to_sfrac", "zfrac_to_sfr", "masses_to_zfrac",
           "sfratio_to_sfr", "sfratio_to_mass"]


# --------------------------------------
# --- Basic Convenience Transforms ---
# --------------------------------------

def stellar_logzsol(logzsol=0.0, **extras):
    """Simple function that takes an argument list and returns the value of the
    `logzsol` argument (i.e. the stellar metallicity)
    """
    return logzsol


def delogify_mass(logmass=0.0, **extras):
    """Simple function that takes an argument list uncluding a `logmass`
    parameter and returns the corresponding linear mass.
    """
    return 10**logmass


# --------------------------------------
# Fancier transforms
# --------------------------------------

def tburst_from_fage(tage=0.0, fage_burst=0.0, **extras):
    """This function transfroms from a fractional age of a burst to an absolute
    age.  With this transformation one can sample in ``fage_burst`` without
    worry about the case tburst > tage.

    :param tage:
        The age of the host galaxy (Gyr)

    :param fage_burst:
        The fraction of the host age at which the burst occurred

    :returns tburst:
        The age of the host when the burst occurred (i.e. the tburst FSPS
        parameter)
    """
    return tage * fage_burst


def tage_from_tuniv(zred=0.0, tage_tuniv=1.0, **extras):
    """This function calculates a galaxy age from the age of the univers at
    `zred` and the age given as a fraction of the age of the universe.  This
    allows for both zred and tage parameters without tage exceeding the age of
    the universe.

    :param zred:
        Cosmological redshift

    :param tage_tuniv:
        The ratio of tage to the age of the universe at `zred`:

    :returns tage:
        The stellar population age, in Gyr
    """
    tuniv = cosmo.age(zred).value
    tage = tage_tuniv * tuniv
    return tage


def zred_to_agebins(zred=0.0, agebins=[], **extras):
    """Set the nonparameteric SFH age bins depending on the age of the universe
    at `zred`
    """
    tuniv = cosmo.age(zred).value * 1e9
    tbinmax = tuniv * 0.85
    ncomp = len(agebins)
    agelims = list(agebins[0]) + np.linspace(agebins[1][1], np.log10(tbinmax), ncomp-2).tolist() + [np.log10(tuniv)]
    return np.array([agelims[:-1], agelims[1:]]).T


def dustratio_to_dust1(dust2=0.0, dust_ratio=0.0, **extras):
    """Set the value of dust1 from the value of dust2 and dust_ratio
    """
    return dust2 * dust_ratio


# --------------------------------------
# --- Transforms for Prospector-alpha non-parametric SFH (Leja et al. 2017) ---
# --------------------------------------

def zfrac_to_sfrac(z_fraction=None, **extras):
    """This transforms from independent dimensionless `z` variables to sfr
    fractions. The transformation is such that sfr fractions are drawn from a
    Dirichlet prior.  See Betancourt et al. 2010 and Leja et al. 2017

    :returns sfrac:
        The star formation fractions (See Leja et al. 2017 for definition).
    """
    sfr_fraction = np.zeros(len(z_fraction) + 1)
    sfr_fraction[0] = 1.0 - z_fraction[0]
    for i in range(1, len(z_fraction)):
        sfr_fraction[i] = np.prod(z_fraction[:i]) * (1.0 - z_fraction[i])
    sfr_fraction[-1] = 1 - np.sum(sfr_fraction[:-1])

    return sfr_fraction


def zfrac_to_masses(total_mass=None, z_fraction=None, agebins=None, **extras):
    """This transforms from independent dimensionless `z` variables to sfr
    fractions and then to bin mass fractions. The transformation is such that
    sfr fractions are drawn from a Dirichlet prior.  See Betancourt et al. 2010
    and Leja et al. 2017

    :returns masses:
        The stellar mass formed in each age bin.
    """
    # sfr fractions
    sfr_fraction = np.zeros(len(z_fraction) + 1)
    sfr_fraction[0] = 1.0 - z_fraction[0]
    for i in range(1, len(z_fraction)):
        sfr_fraction[i] = np.prod(z_fraction[:i]) * (1.0 - z_fraction[i])
    sfr_fraction[-1] = 1 - np.sum(sfr_fraction[:-1])

    # convert to mass fractions
    time_per_bin = np.diff(10**agebins, axis=-1)[:, 0]
    mass_fraction = sfr_fraction * np.array(time_per_bin)
    mass_fraction /= mass_fraction.sum()

    masses = total_mass * mass_fraction
    return masses


def zfrac_to_sfr(total_mass=None, z_fraction=None, agebins=None, **extras):
    """This transforms from independent dimensionless `z` variables to SFRs.

    :returns sfrs:
        The SFR in each age bin (msun/yr).
    """
    # sfr fractions
    sfr_fraction = np.zeros(len(z_fraction) + 1)
    sfr_fraction[0] = 1.0 - z_fraction[0]
    for i in range(1, len(z_fraction)):
        sfr_fraction[i] = np.prod(z_fraction[:i]) * (1.0 - z_fraction[i])
    sfr_fraction[-1] = 1 - np.sum(sfr_fraction[:-1])

    # convert to mass fractions
    time_per_bin = np.diff(10**agebins, axis=-1)[:, 0]
    mass_fraction = sfr_fraction * np.array(time_per_bin)
    mass_fraction /= mass_fraction.sum()

    masses = total_mass * mass_fraction
    return masses / time_per_bin


def masses_to_zfrac(mass=None, agebins=None, **extras):
    """The inverse of zfrac_to_masses, for setting mock parameters based on
    real bin masses.

    :returns zfrac:
        The dimensionless `z` variables used for sfr fraction parameterization.
    """
    total_mass = mass.sum()
    time_per_bin = np.diff(10**agebins, axis=-1)[:, 0]
    sfr_fraction = mass / time_per_bin
    sfr_fraction /= sfr_fraction.sum()

    z_fraction = np.zeros(len(sfr_fraction) - 1)
    z_fraction[0] = 1 - sfr_fraction[0]
    for i in range(1, len(z_fraction)):
        z_fraction[i] = 1.0 - sfr_fraction[i] / np.prod(z_fraction[:i])

    return total_mass, z_fraction


# --------------------------------------
# --- Transforms for SFR ratio based nonparameteric SFH ---
# --------------------------------------

def sfratio_to_sfr(sfr_ratio=None, sfr0=None, **extras):
    sfr = np.cumprod(sfr_ratio)
    all_sfr = np.insert(sfr*sfr0, sfr0, 0)
    return all_sfr


def sfratio_to_mass(sfr_ratio=None, sfr0=None, agebins=None, **extras):
    sfr = sfratio_to_sfr(sfr_ratio=sfr_ratio, sfr0=sfr0)
    time_per_bin = np.diff(10**agebins, axis=-1)[:, 0]
    mass = sfr * time_per_bin
    return mass

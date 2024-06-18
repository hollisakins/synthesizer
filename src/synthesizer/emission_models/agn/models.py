"""A submodule containing the definitions of common agn emission models.

This module contains the definitions of simple emission models that can be
used "out of the box" to generate spectra from components or as a foundation
to work from when creating more complex models.

Example usage:
    # Create a simple emission model
    model = TotalEmission(
        grid=grid,
        dust_curve=dust_curve,
        tau_v=tau_v,
        dust_emission_model=dust_emission_model,
        fesc=0.0,
    )

    # Generate the spectra
    spectra = stars.get_spectra(model)

"""

from unyt import Hz, unyt_array

from synthesizer import exceptions
from synthesizer.emission_models.base_model import EmissionModel
from synthesizer.sed import Sed


class Template(EmissionModel):
    """
    Use a template for the emission model.

    The model is different to all other emission models in that it scales a
    template by bolometric luminosity.

    Attributes:
        sed (Sed)
            The template spectra for the AGN.
        normalisation (unyt_quantity)
            The normalisation for the spectra. In reality this is the
            bolometric luminosity.
    """

    def __init__(
        self,
        label="template",
        filename=None,
        lam=None,
        lnu=None,
        fesc=0.0,
        **kwargs,
    ):
        """
        Initialise the Template.

        Args:
            label (str)
                The label for the model.
            filename (str)
                The filename (including full path) to a file containing the
                template. The file should contain two columns with wavelength
                and luminosity (lnu).
            lam (array)
                Wavelength array.
            lnu (array)
                Luminosity array.
            fesc (float)
                The escape fraction of the AGN.
            **kwargs

        """
        EmissionModel.__init__(
            self,
            grid=None,
            label=label,
            fesc=fesc,
            **kwargs,
        )

        # Ensure we have been given units
        if lam is not None and not isinstance(lam, unyt_array):
            raise exceptions.MissingUnits("lam must be provided with units")
        if lnu is not None and not isinstance(lnu, unyt_array):
            raise exceptions.MissingUnits("lam must be provided with units")

        if filename:
            raise exceptions.UnimplementedFunctionality(
                "Not yet implemented! Feel free to implement and raise a "
                "pull request. Guidance for contributing can be found at "
                "https://github.com/flaresimulations/synthesizer/blob/main/"
                "docs/CONTRIBUTING.md"
            )

        if lam is not None and lnu is not None:
            # initialise a synthesizer Sed object
            self.sed = Sed(lam=lam, lnu=lnu)

            # normalise
            # TODO: add a method to Sed that does this.
            self.normalisation = self.sed.measure_bolometric_luminosity()
            self.sed.lnu /= self.normalisation.value

        else:
            raise exceptions.MissingArgument(
                "Either a filename or both lam and lnu must be provided!"
            )

        # Flag that this is a template
        self._is_template = True

    def _scale_template(self, bolometric_luminosity):
        """
        Calculate the blackhole spectra by scaling the template.

        Args:
            bolometric_luminosity (float)
                The bolometric luminosity of the blackhole(s) for scaling.

        """
        # Ensure we have units for safety
        if bolometric_luminosity is not None and not isinstance(
            bolometric_luminosity, unyt_array
        ):
            raise exceptions.MissingUnits(
                "bolometric luminosity must be provided with units"
            )

        return (
            bolometric_luminosity.to(self.sed.lnu.units * Hz).value
            * self.sed
            * (1 - self.fesc)
        )


class NLRIncidentEmission(EmissionModel):
    """
    An emission model that extracts the NLR incident emission.

    This defines the extraction of key "incident" from a NLR grid.

    This is a child of the EmisisonModel class, for a full description of the
    parameters see the EmissionModel class.
    """

    def __init__(self, grid, label="nlr_incident", **kwargs):
        """
        Initialise the NLRIncidentEmission model.

        Args:
            grid (Grid)
                The grid object containing the NLR incident emission.
            label (str)
                The label for the model.
            **kwargs

        """
        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            extract="incident",
            line_region="nlr",
            **kwargs,
        )


class BLRIncidentEmission(EmissionModel):
    """
    An emission model that extracts the BLR incident emission.

    This defines the extraction of key "incident" from a BLR grid.

    This is a child of the EmisisonModel class, for a full
    description of the parameters see the EmissionModel class.
    """

    def __init__(self, grid, label="blr_incident", **kwargs):
        """
        Initialise the BLRIncidentEmission model.

        Args:
            grid (Grid)
                The grid object containing the BLR incident emission.
            label (str)
                The label for the model.
            **kwargs

        """
        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            extract="incident",
            line_region="blr",
            **kwargs,
        )


class NLRTransmittedEmission(EmissionModel):
    """
    An emission model that extracts the NLR transmitted emission.

    This defines the extraction of key "transmitted" from a NLR grid.

    This is a child of the EmisisonModel class, for a full
    description of the parameters see the EmissionModel class.
    """

    def __init__(
        self,
        grid,
        label="nlr_transmitted",
        covering_fraction=0.1,
        **kwargs,
    ):
        """
        Initialise the NLRTransmittedEmission model.

        Args:
            grid (Grid)
                The grid object containing the NLR transmitted emission.
            label (str)
                The label for the model.
            covering_fraction (float)
                The covering fraction of the NLR (Effectively the escape
                fraction of the NLR). Default is 0.1.
            **kwargs

        """
        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            fesc=covering_fraction,
            extract="transmitted",
            line_region="nlr",
            **kwargs,
        )


class BLRTransmittedEmission(EmissionModel):
    """
    An emission model that extracts the BLR transmitted emission.

    This defines the extraction of key "transmitted" from a BLR grid.

    This is a child of the EmisisonModel class, for a full
    description of the parameters see the EmissionModel class.
    """

    def __init__(
        self,
        grid,
        label="blr_transmitted",
        covering_fraction=0.1,
        **kwargs,
    ):
        """
        Initialise the BLRTransmittedEmission model.

        Args:
            grid (Grid)
                The grid object containing the BLR transmitted emission.
            label (str)
                The label for the model.
            covering_fraction (float)
                The covering fraction of the BLR (Effectively the escape
                fraction of the BLR). Default is 0.1.
            **kwargs

        """
        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            fesc=covering_fraction,
            extract="transmitted",
            line_region="blr",
            **kwargs,
        )


class DiscIncidentEmission(EmissionModel):
    """
    An emission model that extracts the incident disc emission.

    By definition this is just an alias to the incident NLR emission, i.e.
    the emission directly from the NLR with no reprocessing.

    This is a child of the EmisisonModel class, for a full
    description of the parameters see the EmissionModel class.
    """

    def __init__(self, grid, label="disc_incident", **kwargs):
        """
        Initialise the DiscIncidentEmission model.

        Args:
            grid (Grid)
                The grid object containing the incident disc emission.
            label (str)
                The label for the model.
            **kwargs

        """
        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            extract="incident",
            line_region="nlr",
            **kwargs,
        )


class DiscTranmittedEmission(EmissionModel):
    """
    An emission model that combines the transmitted disc emission.

    This will combine the transmitted NLR and BLR emission to give the
    transmitted disc emission.

    This is a child of the EmisisonModel class, for a full
    description of the parameters see the EmissionModel class.
    """

    def __init__(
        self,
        grid,
        label="disc_transmitted",
        covering_fraction_blr=0.1,
        covering_fraction_nlr=0.1,
        **kwargs,
    ):
        """
        Initialise the DiscTransmittedEmission model.

        Args:
            grid (Grid)
                The grid object containing the transmitted disc emission.
            label (str)
                The label for the model.
            **kwargs

        """
        # Create the child models
        nlr = NLRTransmittedEmission(
            grid=grid,
            label="nlr_transmitted",
            covering_fraction=covering_fraction_nlr,
            **kwargs,
        )
        blr = BLRTransmittedEmission(
            grid=grid,
            label="blr_transmitted",
            covering_fraction=covering_fraction_blr,
            **kwargs,
        )

        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            combine=(nlr, blr),
            **kwargs,
        )


class DiscEscapedEmission(EmissionModel):
    """
    An emission model that computes the escaped disc emission.

    This will extract the incident disc emission but apply
    fesc=1 - covering_fraction, since the escaped is the mirror of the
    transmitted emission.

    This is a child of the EmisisonModel class, for a full description of the
    parameters see the EmissionModel class.
    """

    def __init__(
        self,
        grid,
        label="disc_escaped",
        covering_fraction_nlr=0.1,
        covering_fraction_blr=0.1,
        **kwargs,
    ):
        """
        Initialise the DiscEscapedEmission model.

        Args:
            grid (Grid)
                The NLR grid object.
            label (str)
                The label for the model.
            covering_fraction_nlr (float)
                The covering fraction of the NLR (Effectively the escape
                fraction of the NLR). Default is 0.1.
            covering_fraction_blr (float)
                The covering fraction of the BLR (Effectively the escape
                fraction of the BLR). Default is 0.1.
            **kwargs
        """
        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            extract="incident",
            fesc=1 - covering_fraction_nlr - covering_fraction_blr,
            **kwargs,
        )


class DiscEmission(EmissionModel):
    """
    An emission model that computes the total disc emission.

    This will combine the tranmitted and escaped disc emission.

    This is a child of the EmisisonModel class, for a full
    description of the parameters see the EmissionModel class.
    """

    def __init__(self, grid, label="disc", **kwargs):
        """
        Initialise the DiscEmission model.

        Args:
            grid (Grid)
                The grid object containing the disc emission.
            label (str)
                The label for the model.
            **kwargs

        """
        # Create the child models
        transmitted = DiscTranmittedEmission(
            grid=grid,
            label="disc_transmitted",
            **kwargs,
        )
        escaped = DiscEscapedEmission(
            grid=grid,
            label="disc_escaped",
            **kwargs,
        )

        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            combine=(transmitted, escaped),
            **kwargs,
        )


class TorusEmission(EmissionModel):
    """
    An emission model that computes the torus emission.

    This will generate the torus emission from the model.

    This is a child of the EmisisonModel class, for a full
    description of the parameters see the EmissionModel class.
    """

    def __init__(
        self, torus_emission_model, scale_by, label="torus", **kwargs
    ):
        """
        Initialise the TorusEmission model.

        Args:
            torus_emission_model (dust.emission)
                The dust emission model to use for the torus.
            scale_by (float)
                The emission model to use for scaling of the torus emission.
            label (str)
                The label for the model.
            **kwargs

        """
        EmissionModel.__init__(
            self,
            label=label,
            dust_emission_model=torus_emission_model,
            dust_lum_intrinsic=scale_by,
            **kwargs,
        )


class AGNIntrinsicEmission(EmissionModel):
    """
    An emission model that computes the intrinsic AGN emission.

    This will generate the intrinsic AGN emission from the model by combining
    all child models.

    This is a child of the EmisisonModel class, for a full
    description of the parameters see the EmissionModel class.
    """

    def __init__(
        self,
        grid,
        label="intrinsic",
        covering_fraction_nlr=0.1,
        covering_fraction_blr=0.1,
        **kwargs,
    ):
        """
        Initialise the AGNIntrinsicEmission model.

        Args:
            grid (Grid)
                The grid object containing the AGN intrinsic emission.
            label (str)
                The label for the model.
            covering_fraction_nlr (float)
                The covering fraction of the NLR (Effectively the escape
                fraction of the NLR). Default is 0.1.
            covering_fraction_blr (float)
                The covering fraction of the BLR (Effectively the escape
                fraction of the BLR). Default is 0.1.
            **kwargs

        """
        # Create the child models
        incident = DiscIncidentEmission(
            grid=grid,
            label="disc_incident",
            **kwargs,
        )
        disc = DiscEmission(
            grid=grid,
            label="disc",
            covering_fraction_nlr=covering_fraction_nlr,
            covering_fraction_blr=covering_fraction_blr,
            **kwargs,
        )
        torus = TorusEmission(
            torus_emission_model=grid.dust_emission_model,
            scale_by=incident,
            label="torus",
            **kwargs,
        )

        EmissionModel.__init__(
            self,
            grid=grid,
            label=label,
            combine=(
                disc,
                torus,
            ),
            **kwargs,
        )

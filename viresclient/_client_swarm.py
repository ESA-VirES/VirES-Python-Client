import datetime
import json
from collections import OrderedDict
import os
import sys

from ._wps.environment import JINJA2_ENVIRONMENT
from ._wps.time_util import parse_datetime
from ._client import WPSInputs, ClientRequest, TEMPLATE_FILES
from ._data_handling import ReturnedDataFile


TEMPLATE_FILES = {
    **TEMPLATE_FILES,
    'sync': "vires_fetch_filtered_data.xml",
    'async': "vires_fetch_filtered_data_async.xml",
    'model_info': "vires_get_model_info.xml",
    'times_from_orbits': "vires_times_from_orbits.xml"
}

REFERENCES = {
    'General Swarm': (" Swarm Data Handbook, https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook ",
                      " The Swarm Satellite Constellation Application and Research Facility (SCARF) and Swarm data products, https://doi.org/10.5047/eps.2013.07.001 ",
                      " Swarm Science Data Processing and Products (2013), https://link.springer.com/journal/40623/65/11/page/1 ",
                      " Special issue “Swarm science results after 2 years in space (2016), https://www.springeropen.com/collections/swsr ",
                      " Earth's Magnetic Field: Understanding Geomagnetic Sources from the Earth's Interior and its Environment (2017), https://link.springer.com/journal/11214/206/1/page/1 ")
    }

MODEL_REFERENCES = {
    'IGRF':
        (" International Geomagnetic Reference Field: the 13th generation, (waiting for publication) ",
         " https://www.ngdc.noaa.gov/IAGA/vmod/igrf.html "),
    'IGRF12':
        (" International Geomagnetic Reference Field: the 12th generation, https://doi.org/10.1186/s40623-015-0228-9 ",
         " https://www.ngdc.noaa.gov/IAGA/vmod/igrf.html "
         " deprecated model identifier, use IGRF instead"),
    'CHAOS-Core':
        ("CHAOS-7 Core field (SH degrees 1-20)",
         " http://www.spacecenter.dk/files/magnetic-models/CHAOS-7/ "),
    'CHAOS-Static':
        ("CHAOS-7 crust field (SH degrees 21-185)",
         " http://www.spacecenter.dk/files/magnetic-models/CHAOS-7/ "),
    'CHAOS-MMA-Primary':
        ("CHAOS-7 Primary (external) magnetospheric field",
         " hhttp://www.spacecenter.dk/files/magnetic-models/CHAOS-7/ "),
    'CHAOS-MMA-Secondary':
        ("CHAOS-7 Secondary (internal) magnetospheric field",
         " http://www.spacecenter.dk/files/magnetic-models/CHAOS-7/ "),
    'CHAOS-6-Core':
        ("CHAOS Core field",
         " deprecated model identifier, use CHAOS-Core instead"),
    'CHAOS-6-Static':
        ("CHAOS crust field",
         " deprecated model identifier, use CHAOS-Static instead"),
    'CHAOS-6-MMA-Primary':
        ("CHAOS Primary (external) magnetospheric field",
         " deprecated model identifier, use CHAOS-MMA-Primary instead"),
    'CHAOS-6-MMA-Secondary':
        ("CHAOS-Secondary (internal) magnetospheric field",
         " deprecated model identifier, use CHAOS-MMA-Secondary instead"),
    'MF7':
        ("MF7 crustal field model, derived from CHAMP satellite observations",
         " http://geomag.org/models/MF7.html"),
    'LCS-1':
        ("The LCS-1 high-resolution lithospheric field model, derived from CHAMP and Swarm satellite observations",
         " http://www.spacecenter.dk/files/magnetic-models/LCS-1/"),
    'MCO_SHA_2C':
        ("[Comprehensive Inversion]: Core field of CIY4",
         " A comprehensive model of Earth’s magnetic field determined from 4 years of Swarm satellite observations, https://doi.org/10.1186/s40623-018-0896-3 ",
         "Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MCO/SW_OPER_MCO_VAL_2C_20131201T000000_20180101T000000_0401.ZIP "),
    'MCO_SHA_2D':
        ("[Dedicated Chain]: Core field",
         "An algorithm for deriving core magnetic field models from the Swarm data set, https://doi.org/10.5047/eps.2013.07.005 ",
         "Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MCO/SW_OPER_MCO_VAL_2D_20131126T000000_20180101T000000_0401.ZIP "),
    'MLI_SHA_2C':
        ("[Comprehensive Inversion]: Lithospheric field of CIY4",
         "Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MLI/SW_OPER_MLI_VAL_2C_00000000T000000_99999999T999999_0401.ZIP"),
    'MLI_SHA_2D':
        ("[Dedicated Chain]: Lithospheric field",
         " Swarm SCARF Dedicated Lithospheric Field Inversion chain, https://doi.org/10.5047/eps.2013.07.008 ",
         " Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MLI/SW_OPER_MLI_VAL_2D_00000000T000000_99999999T999999_0401.ZIP "),
    'MMA_SHA_2C-Primary':
        ("[Comprehensive Inversion]: Primary (external) magnetospheric field of CIY4",
         "Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MMA/SW_OPER_MMA_VAL_2C_20131201T000000_20180101T000000_0401.ZIP"),
    'MMA_SHA_2C-Secondary':
        ("[Comprehensive Inversion]: Secondary (internal/induced) magnetospheric field of CIY4",),
    'MMA_SHA_2F-Primary':
        ("[Fast-Track Product]: Primary (external) magnetospheric field",
         " Rapid modelling of the large-scale magnetospheric field from Swarm satellite data, https://doi.org/10.5047/eps.2013.09.003 "),
    'MMA_SHA_2F-Secondary':
        ("[Fast-Track Product]: Secondary (internal/induced) magnetospheric field",),
    'MIO_SHA_2C-Primary':
        ("[Comprehensive Inversion]: Primary (external) ionospheric field of CIY4",
         "Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MIO/SW_OPER_MIO_VAL_2C_00000000T000000_99999999T999999_0401.ZIP "),
    'MIO_SHA_2C-Secondary':
        ("[Comprehensive Inversion]: Secondary (external/induced) ionospheric field of CIY4",),
    'MIO_SHA_2D-Primary':
        ("[Dedicated Chain]: Primary (external) ionospheric field, DIFI",
         " Swarm SCARF dedicated ionospheric field inversion chain, https://doi.org/10.5047/eps.2013.08.006 ",
         " First results from the Swarm Dedicated Ionospheric Field Inversion chain, https://doi.org/10.1186/s40623-016-0481-6 ",
         " http://geomag.colorado.edu/difi-3 ",
         "Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MIO/SW_OPER_MIO_VAL_2D_20131201T000000_20171231T235959_0402.ZIP "),
    'MIO_SHA_2D-Secondary':
        ("[Dedicated Chain]: Secondary (external/induced) ionospheric field, DIFI",),
    'AMPS':
        ("AMPS - associated magnetic field, https://github.com/klaundal/pyAMPS",),
    'MCO_SHA_2X':
        ("Alias for 'CHAOS-Core'",),
    'CHAOS':
        ("Alias for 'CHAOS-Core' + 'CHAOS-Static' + 'CHAOS-MMA-Primary' + 'CHAOS-MMA-Secondary'",),
    'CHAOS-MMA':
        ("Alias for 'CHAOS-MMA-Primary' + 'CHAOS-MMA-Secondary'",),
    'MMA_SHA_2C':
        ("Alias for 'MMA_SHA_2C-Primary' + 'MMA_SHA_2C-Secondary'",),
    'MMA_SHA_2F':
        ("Alias for 'MMA_SHA_2F-Primary' + 'MMA_SHA_2F-Secondary'",),
    'MIO_SHA_2C':
        ("Alias for 'MIO_SHA_2C-Primary' + 'MIO_SHA_2C-Secondary'",),
    'MIO_SHA_2D':
        ("Alias for 'MIO_SHA_2D-Primary' + 'MIO_SHA_2D-Secondary'",),
    'SwarmCI':
        ("Alias for 'MCO_SHA_2C' + 'MLI_SHA_2C' + 'MIO_SHA_2C-Primary' + 'MIO_SHA_2C-Secondary' + 'MMA_SHA_2C-Primary' + 'MMA_SHA_2C-Secondary'",),
}

DEPRECATED_MODELS = {
    'IGRF12': "Use IGRF instead.",
    'CHAOS-6-Core': "Use CHAOS-Core instead.",
    'CHAOS-6-Static': "Use CHAOS-Static instead.",
    'CHAOS-6-MMA-Primary': "Use CHAOS-MMA-Primary instead.",
    'CHAOS-6-MMA-Secondary': "Use CHAOS-MMA-Secondary instead.",
}

COLLECTION_REFERENCES = {
    "MAG": (" https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-1b-product-definitions#MAGX_LR_1B_Product ",
            ),
    "MAG_HR": ("https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-1b-product-definitions#MAGX_HR_1B_Product ",
            ),
    "EFI": (" https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-1b-product-definitions#EFIX_LP_1B_Product ",
            ),
    "IBI": (" https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-2-product-definitions#IBIxTMS_2F ",
            " https://earth.esa.int/documents/10174/1514862/Swarm_L2_IBI_product_description "),
    "TEC": (" https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-2-product-definitions#TECxTMS_2F ",
            " https://earth.esa.int/documents/10174/1514862/Swarm_Level-2_TEC_Product_Description "),
    "FAC": (" https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-2-product-definitions#FAC_TMS_2F ",
            " https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-2-product-definitions#FACxTMS_2F ",
            " https://earth.esa.int/documents/10174/1514862/Swarm_L2_FAC_single_product_description ",
            " https://earth.esa.int/documents/10174/1514862/Swarm-L2-FAC-Dual-Product-Description "),
    "EEF": (" https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-2-product-definitions#EEFxTMS_2F ",
            " https://earth.esa.int/documents/10174/1514862/Swarm-Level-2-EEF-Product-Description "),
    "IPD": (" https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-2-product-definitions#IPDxIPR_2F ",
            )
}


class SwarmWPSInputs(WPSInputs):
    """Holds the set of inputs to be passed to the request template for Swarm
    """

    NAMES = [
        'collection_ids',
        'model_expression',
        'begin_time',
        'end_time',
        'variables',
        'filters',
        'sampling_step',
        'response_type',
        'custom_shc',
        ]

    def __init__(self,
                 collection_ids=None,
                 model_expression=None,
                 begin_time=None,
                 end_time=None,
                 variables=None,
                 filters=None,
                 sampling_step=None,
                 response_type=None,
                 custom_shc=None):
        # Set up default values
        # Obligatory - these must be replaced before the request is made
        self.collection_ids = None if collection_ids is None else collection_ids
        self.begin_time = None if begin_time is None else begin_time
        self.end_time = None if end_time is None else end_time
        self.response_type = None if response_type is None else response_type
        # Optional - these defaults will be used if not replaced before the
        #            request is made
        self.model_expression = str() if model_expression is None else model_expression
        self.variables = [] if variables is None else variables
        self.filters = None if filters is None else filters
        self.sampling_step = None if sampling_step is None else sampling_step
        self.custom_shc = None if custom_shc is None else custom_shc

    @property
    def collection_ids(self):
        return self._collection_ids

    @collection_ids.setter
    def collection_ids(self, collection_ids):
        if isinstance(collection_ids, dict) or collection_ids is None:
            self._collection_ids = collection_ids
        else:
            raise TypeError("collection_ids must be a dict")

    @staticmethod
    def _spacecraft_from_collection(collection):
        """Identify spacecraft from collection name."""
        # 12th character in name, e.g. SW_OPER_MAGx_LR_1B
        sc = collection[11]
        sc_to_name = {"A": "Alpha", "B": "Bravo", "C": "Charlie", "_": "NSC"}
        return sc_to_name[sc]

    def set_collections(self, collections):
        """Restructure given list of collections as dict required by VirES."""
        # Build the output dictionary in the form:
        #  {"Alpha": ["SW..A..", "SW..A.."], "Bravo": ["SW..B.."], "NSC": [..]}
        if isinstance(collections, list):
            collection_dict = {}
            for collection in collections:
                tag = self._spacecraft_from_collection(collection)
                if tag in collection_dict.keys():
                    collection_dict[tag].append(collection)
                else:
                    collection_dict[tag] = [collection]
            self.collection_ids = collection_dict
        else:
            raise TypeError("collections must be a list")

    @property
    def model_expression(self):
        return self._model_expression

    @model_expression.setter
    def model_expression(self, model_expression):
        if isinstance(model_expression, str):
            self._model_expression = model_expression
        else:
            raise TypeError("model_expression must be a string")

    @property
    def begin_time(self):
        return self._begin_time

    @begin_time.setter
    def begin_time(self, begin_time):
        if isinstance(begin_time, datetime.datetime) or begin_time is None:
            self._begin_time = begin_time
        else:
            raise TypeError

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, end_time):
        if isinstance(end_time, datetime.datetime) or end_time is None:
            self._end_time = end_time
        else:
            raise TypeError

    @property
    def variables(self):
        return self._variables

    @variables.setter
    def variables(self, variables):
        if isinstance(variables, list):
            self._variables = variables
        else:
            raise TypeError

    @property
    def filters(self):
        return self._filters

    @filters.setter
    def filters(self, filters):
        if isinstance(filters, str) or filters is None:
            self._filters = filters
        else:
            raise TypeError

    @property
    def sampling_step(self):
        return self._sampling_step

    @sampling_step.setter
    def sampling_step(self, sampling_step):
        if isinstance(sampling_step, str) or sampling_step is None:
            self._sampling_step = sampling_step
        else:
            raise TypeError

    @property
    def response_type(self):
        return self._response_type

    @response_type.setter
    def response_type(self, response_type):
        if isinstance(response_type, str) or response_type is None:
            self._response_type = response_type
        else:
            raise TypeError

    @property
    def custom_shc(self):
        return self._custom_shc

    @custom_shc.setter
    def custom_shc(self, custom_shc):
        if isinstance(custom_shc, str) or custom_shc is None:
            self._custom_shc = custom_shc
        else:
            raise TypeError


class SwarmRequest(ClientRequest):
    """Handles the requests to and downloads from the server.

    Example usage::

        from viresclient import SwarmRequest
        # Set up connection with server
        request = SwarmRequest()
        # Set collection to use
        request.set_collection("SW_OPER_MAGA_LR_1B")
        # Set mix of products to fetch:
        #  measurements (variables from the given collection)
        #  models (magnetic model predictions at spacecraft sampling points)
        #  auxiliaries (variables available with any collection)
        request.set_products(
            measurements=["F", "B_NEC"],
            models=["CHAOS-Core"],
            auxiliaries=["QDLat", "QDLon"],
            sampling_step="PT10S"
        )
        # Fetch data from a given time interval
        data = request.get_between(
            start_time="2014-01-01T00:00",
            end_time="2014-01-01T01:00"
        )
        # Load the data as an xarray.Dataset
        ds = data.as_xarray()

    Check what data are available with::

        request.available_collections(details=False)
        request.available_measurements("MAG")
        request.available_auxiliaries()
        request.available_models(details=False)

    Args:
        url (str):
        username (str):
        password (str):
        token (str):
        config (str or ClientConfig):
        logging_level (str):

    """
    COLLECTIONS = {
        "MAG": ["SW_OPER_MAG{}_LR_1B".format(x) for x in "ABC"],
        "MAG_HR": ["SW_OPER_MAG{}_HR_1B".format(x) for x in "ABC"],
        "EFI": ["SW_OPER_EFI{}_LP_1B".format(x) for x in "ABC"],
        "IBI": ["SW_OPER_IBI{}TMS_2F".format(x) for x in "ABC"],
        "TEC": ["SW_OPER_TEC{}TMS_2F".format(x) for x in "ABC"],
        "FAC": ["SW_OPER_FAC{}TMS_2F".format(x) for x in "ABC_"],
        "EEF": ["SW_OPER_EEF{}TMS_2F".format(x) for x in "ABC"],
        "IPD": ["SW_OPER_IPD{}IRR_2F".format(x) for x in "ABC"],
        }

    # These are not necessarily real sampling steps, but are good enough to use
    # for splitting long requests into chunks
    COLLECTION_SAMPLING_STEPS = {
        "MAG": "PT1S",
        "MAG_HR": "PT0.019S",  # approx 50Hz (the sampling is not exactly 50Hz)
        "EFI": "PT0.5S",
        "IBI": "PT1S",
        "TEC": "PT1S",      # Actually more complicated
        "FAC": "PT1S",
        "EEF": "PT90M",
        "IPD": "PT1S",
    }

    PRODUCT_VARIABLES = {
        "MAG": [
            "F", "dF_AOCS", "dF_other", "F_error", "B_VFM", "B_NEC", "dB_Sun",
            "dB_AOCS", "dB_other", "B_error", "q_NEC_CRF", "Att_error",
            "Flags_F", "Flags_B", "Flags_q", "Flags_Platform", "ASM_Freq_Dev",
            ],
        "MAG_HR": [ #NOTE: F is calculated on the fly from B_NEC (F = |B_NEC|)
            "F", "B_VFM", "B_NEC", "dB_Sun", "dB_AOCS", "dB_other", "B_error",
            "q_NEC_CRF", "Att_error", "Flags_B", "Flags_q", "Flags_Platform",
            ],
        "EFI": [
            "U_orbit", "Ne", "Ne_error", "Te", "Te_error", "Vs", "Vs_error",
            "Flags_LP", "Flags_Ne", "Flags_Te", "Flags_Vs",
            ],
        "IBI": [
            "Bubble_Index", "Bubble_Probability", "Flags_Bubble", "Flags_F",
            "Flags_B", "Flags_q",
            ],
        "TEC": [
            "GPS_Position", "LEO_Position", "PRN", "L1", "L2", "P1", "P2", "S1",
            "S2", "Elevation_Angle", "Absolute_VTEC", "Absolute_STEC",
            "Relative_STEC", "Relative_STEC_RMS", "DCB", "DCB_Error",
            ],
        "FAC": [
            "IRC", "IRC_Error", "FAC", "FAC_Error", "Flags", "Flags_F",
            "Flags_B", "Flags_q"],
        "EEF": ["EEF", "EEJ", "RelErr", "Flags"],
        "IPD": [
            "Ne", "Te", "Background_Ne", "Foreground_Ne", "PCP_flag",
            "Grad_Ne_at_100km", "Grad_Ne_at_50km", "Grad_Ne_at_20km",
            "Grad_Ne_at_PCP_edge", "ROD", "RODI10s", "RODI20s",
            "delta_Ne10s", "delta_Ne20s", "delta_Ne40s",
            "Num_GPS_satellites", "mVTEC", "mROT", "mROTI10s", "mROTI20s",
            "IBI_flag", "Ionosphere_region_flag", "IPIR_index",
            "Ne_quality_flag", "TEC_STD"
            ],
        }

    AUXILIARY_VARIABLES = [
        "Timestamp", "Latitude", "Longitude", "Radius", "Spacecraft",
        "OrbitDirection", "QDOrbitDirection", "SyncStatus", "Kp10", "Kp", "Dst",
        "F107", "IMF_BY_GSM", "IMF_BZ_GSM", "IMF_V", "F10_INDEX", "OrbitSource",
        "OrbitNumber", "AscendingNodeTime", "AscendingNodeLongitude", "QDLat",
        "QDLon", "QDBasis", "MLT", "SunDeclination", "SunHourAngle",
        "SunRightAscension", "SunAzimuthAngle", "SunZenithAngle",
        "SunLongitude", "SunVector", "DipoleAxisVector", "NGPLatitude",
        "NGPLongitude", "DipoleTiltAngle",
        ]

    MAGNETIC_MODEL_VARIABLES = ["F", "B_NEC"]

    MAGNETIC_MODELS = [
        "IGRF", "IGRF12", "LCS-1", "MF7",
        "CHAOS-Core", "CHAOS-Static", "CHAOS-MMA-Primary", "CHAOS-MMA-Secondary",
        "CHAOS-6-Core", "CHAOS-6-Static", "CHAOS-6-MMA-Primary", "CHAOS-6-MMA-Secondary",
        "MCO_SHA_2C", "MCO_SHA_2D", "MLI_SHA_2C", "MLI_SHA_2D",
        "MMA_SHA_2C-Primary", "MMA_SHA_2C-Secondary",
        "MMA_SHA_2F-Primary", "MMA_SHA_2F-Secondary",
        "MIO_SHA_2C-Primary", "MIO_SHA_2C-Secondary",
        "MIO_SHA_2D-Primary", "MIO_SHA_2D-Secondary",
        "AMPS",
        "MCO_SHA_2X", "CHAOS", "CHAOS-MMA", "MMA_SHA_2C", "MMA_SHA_2F", "MIO_SHA_2C", "MIO_SHA_2D", "SwarmCI",
        ]

    def __init__(self, url=None, username=None, password=None, token=None,
                 config=None, logging_level="NO_LOGGING"):
        super().__init__(
            url, username, password, token, config, logging_level,
            server_type="Swarm"
            )

        self._available = self._get_available_data()
        self._request_inputs = SwarmWPSInputs()
        self._templatefiles = TEMPLATE_FILES
        self._filterlist = []
        self._supported_filetypes = ("csv", "cdf")
        self._collection_list = None

    @classmethod
    def _get_available_data(cls):
        # Build the reverse mapping: "SW_OPER_MAGA_LR_1B": "MAG" etc
        collections_to_keys = {}
        for key, collections in cls.COLLECTIONS.items():
            collections_to_keys.update({
                collection: key for collection in collections
            })

        return {
            "collections": cls.COLLECTIONS,
            "collections_to_keys": collections_to_keys,
            "collection_sampling_steps": cls.COLLECTION_SAMPLING_STEPS,
            "measurements": cls.PRODUCT_VARIABLES,
            "models": cls.MAGNETIC_MODELS,
            "model_variables": cls.MAGNETIC_MODEL_VARIABLES,
            "auxiliaries": cls.AUXILIARY_VARIABLES,
            }

    @staticmethod
    def _parse_models_input(models=None):
        """Verify and parse models input.

        Args:
            models (list/dict): User-provided values

        Returns:
            list: model_ids, list of model_id strings
            str: model_expression_string to be passed to the server
        """
        models = [] if models is None else models
        # Convert input to OrderedDict
        #  e.g. {"model_name": "model_expression", ..}
        # Check if models input is basic list of strings,
        #  If not, then handle inputs given as dicts or list of tuples
        if (isinstance(models, list) and
                all(isinstance(item, str) for item in models)):
            # Convert the models list to an OrderedDict
            model_expressions = OrderedDict()
            for model in models:
                model_id, _, model_expression = [
                    s.strip() for s in model.partition("=")
                ]
                model_expressions[model_id] = model_expression
        else:
            try:
                model_expressions = OrderedDict(models)
                # Check that everything is a string
                if not all(isinstance(item, str)for item in
                           [*model_expressions.values()] +
                           [*model_expressions.keys()]):
                    raise ValueError
            except ValueError:
                raise ValueError("Invalid models input!")
        # TODO: Verify input model names
        #  (use self._available["models"])
        # Create the combined model expression string passed to the request
        model_expression_string = ""
        for model_id, model_expression in model_expressions.items():
            if model_expression == "":
                s = model_id
            else:
                s = "=".join([model_id, model_expression])
            model_expression_string = ",".join([model_expression_string, s])
        model_ids = list(s.strip("\'\"") for s in model_expressions.keys())
        return model_ids, model_expression_string[1:]

    def available_collections(self, groupname=None, details=True):
        """Show details of available collections.

        Args:
            groupname (str): one of: ("MAG", "EFI", etc.)
            details (bool): If True then print a nice output.
                If False then return a dict of available collections.

        """
        def _filter_collections(groupname):
            groups = list(self._available["collections"].keys())
            if groupname in groups:
                return {groupname:
                        self._available["collections"][groupname]}
            else:
                raise ValueError("Invalid collection group name")
        if groupname:
            collections_filtered = _filter_collections(groupname)
        else:
            collections_filtered = self._available["collections"]
        if details:
            print("General References:")
            for i in REFERENCES["General Swarm"]:
                print(i)
            print()
            for key, val in collections_filtered.items():
                print(key)
                for i in val:
                    print('  ', i)
                refs = COLLECTION_REFERENCES.get(key, ('No reference...',))
                for ref in refs:
                    print(ref)
                print()
        else:
            return collections_filtered

    def available_measurements(self, collection=None):
        """Returns a list of the available measurements for the chosen collection.

        Args:
            collection (str): one of: ("MAG", "EFI", "IBI", "TEC", "FAC", "EEF")

        """
        keys = list(self._available["measurements"].keys())
        if collection in keys:
            collection_key = collection
            return self._available["measurements"][collection_key]
        elif collection in self._available["collections_to_keys"]:
            collection_key = self._available["collections_to_keys"][collection]
            return self._available["measurements"][collection_key]
        elif collection is None:
            return self._available["measurements"]
        else:
            raise Exception(
                "collection must be one of {}\nor\n{}".format(
                    ", ".join(keys),
                    "\n".join(self._available["collections_to_keys"])
                    )
                )

    def available_models(self, param=None, details=True, nice_output=True):
        """Show details of avalable models.

        If details is True, return a dictionary of model names and details.
        If nice_output is True, the dictionary is printed nicely.
        If details is False, return a list of model names.
        If param is set, filter to only return entries including this

        Note:
            |  F = Fast-Track Products
            |  C = Comprehensive Inversion
            |  D = Dedicated Chain
            |  MCO = Core / main
            |  MLI = Lithosphere
            |  MMA = Magnetosphere
            |  MIO = Ionosphere

        Args:
            param (str): one of "F C D MCO MLI MMA MIO"
            details (bool): True for a dict of details, False for a brief list
            nice_output (bool): If True, just print the dict nicely

        """

        def filter_by_param(d, param):
            if param in ("F", "C", "D"):
                param = '2' + param
            return [i for i in d if param in i]

        # get all models provided by the server
        models_info = self.get_model_info()

        # keep only models really provided by the server
        d = [
            model_name for model_name in self._available["models"]
            if model_name in models_info
        ]

        # Filter the dict/list to only include those that contain param
        if param is not None:
            d = filter_by_param(d, param)

        if details:
            d = {
                model_name: {
                    "description": MODEL_REFERENCES[model_name],
                    "details": models_info[model_name]
                }
                for model_name in d
            }

        if nice_output and details:
            d = OrderedDict(sorted(d.items()))
            for model_name, desc_details in d.items():
                print(model_name, "=", desc_details["details"]["expression"])
                print("  START:", desc_details["details"]["validity"]["start"])
                print("  END:  ", desc_details["details"]["validity"]["end"])
                print("DESCRIPTION:")
                for line in desc_details["description"]:
                    print(line)
                print("SOURCES:")
                for line in desc_details["details"]["sources"]:
                    print(" ", line)
                print()
        else:
            return d

    def available_auxiliaries(self):
        """Returns a list of the available auxiliary parameters.
        """
        return self._available["auxiliaries"]

    def set_collection(self, *args):
        """Set the collection(s) to use.

        Args:
            (str): one or several from .available_collections()

        """
        collections = [*args]
        for collection in collections:
            if not isinstance(collection, str):
                raise TypeError(
                    "{} invalid. Must be string."
                    .format(collection)
                    )
        for collection in collections:
            if collection not in self._available["collections_to_keys"]:
                raise ValueError(
                    "Invalid collection: {}. "
                    "Check available with SwarmRequest().available_collections()"
                    .format(collection)
                    )
        self._collection_list = collections
        self._request_inputs.set_collections(collections)
        return self

    def set_products(self, measurements=None, models=None, custom_model=None,
                     auxiliaries=None, residuals=False, sampling_step=None
                     ):
        """Set the combination of products to retrieve.

        If residuals=True then just get the measurement-model residuals,
        otherwise get both measurement and model values.

        Args:
            measurements (list(str)): from .available_measurements(collection_key)
            models (list(str)/dict): from .available_models() or defineable with custom expressions
            custom_model (str): path to a custom model in .shc format
            auxiliaries (list(str)): from .available_auxiliaries()
            residuals (bool): True if only returning measurement-model residual
            sampling_step (str): ISO_8601 duration, e.g. 10 seconds: PT10S, 1 minute: PT1M

        """
        if self._collection_list is None:
            raise Exception("Must run .set_collection() first.")
        measurements = [] if measurements is None else measurements
        models = [] if models is None else models
        model_variables = set(self._available["model_variables"])
        auxiliaries = [] if auxiliaries is None else auxiliaries
        # If inputs are strings (when providing only one parameter)
        #  put them in lists
        if isinstance(measurements, str):
            measurements = [measurements]
        if isinstance(models, str):
            models = [models]
        if isinstance(auxiliaries, str):
            auxiliaries = [auxiliaries]
        # print warning for deprecated models
        self._check_deprecated_models(models)
        # Check the chosen measurements are available for the set collections
        available_measurements = []
        for collection in self._collection_list:
            collection_key = self._available["collections_to_keys"][collection]
            available_measurements.extend(
                self._available["measurements"][collection_key]
            )
        for variable in measurements:
            if variable not in available_measurements:
                raise Exception(
                    "Measurement '{}' not available for collection '{}'. "
                    "Check available with "
                    "SwarmRequest.available_measurements({})".format(
                        variable, collection_key, collection_key
                    ))
        # Check if at least one model defined when requesting residuals
        if residuals and not models:
            raise Exception("Residuals requested but no model defined!")
        # Check models format, extract model_ids and string to pass to server
        model_ids, model_expression_string = self._parse_models_input(models)
        # Check chosen aux is available
        for variable in auxiliaries:
            if variable not in self._available["auxiliaries"]:
                raise Exception(
                    "'{}' not available. Check available with "
                    "SwarmRequest.available_auxiliaries()".format(variable)
                    )
        # Load the custom .shc file
        if custom_model:
            if os.path.exists(custom_model):
                with open(custom_model) as custom_shc_file:
                    custom_shc = custom_shc_file.read()
                model_ids.append("Custom_Model")
            else:
                raise OSError("Custom model .shc file not found")
        else:
            custom_shc = None
        # Set up the variables that actually get passed to the WPS request
        variables = []
        for variable in measurements:
            if variable in model_variables:
                if residuals:
                    variables.extend(
                        "%s_res_%s" % (variable, model_name)
                        for model_name in model_ids
                    )
                else:
                    variables.append(variable)
                    variables.extend(
                        "%s_%s" % (variable, model_name)
                        for model_name in model_ids
                    )
            else:  # not a model variable
                variables.append(variable)
        variables.extend(auxiliaries)
        # Set these in the SwarmWPSInputs object
        self._request_inputs.model_expression = model_expression_string
        self._request_inputs.variables = variables
        self._request_inputs.sampling_step = sampling_step
        self._request_inputs.custom_shc = custom_shc
        return self

    def set_range_filter(self, parameter=None, minimum=None, maximum=None):
        """Set a filter to apply.

        Filters data for minimum ≤ parameter ≤ maximum

        Note:
            Apply multiple filters with successive calls to set_range_filter()

        Args:
            parameter (str)
            minimum (float)
            maximum (float)

        """
        if not isinstance(parameter, str):
            raise TypeError("parameter must be a str")
        # Update the list that contains the separate filters
        self._filterlist += [parameter+":"+str(minimum)+","+str(maximum)]
        # Convert the list into the string that gets passed to the xml template
        if len(self._filterlist) == 1:
            filters = self._filterlist[0]
        else:
            filters = ';'.join(self._filterlist)
        # Update the SwarmWPSInputs object
        self._request_inputs.filters = filters
        return self

    def clear_range_filter(self):
        """Remove all applied filters."""
        self._filterlist = []
        self._request_inputs.filters = None
        return self

    def get_times_for_orbits(self, spacecraft, start_orbit, end_orbit):
        """Translate a pair of orbit numbers to a time interval.

        Args:
            spacecraft (str): one of ('A','B','C') or
                                ("Alpha", "Bravo", "Charlie")
            start_orbit (int): a starting orbit number
            end_orbit (int): a later orbit number

        Returns:
            tuple (datetime): (start_time, end_time) The start time of the
            start_orbit and the ending time of the end_orbit.
            (Based on ascending nodes of the orbits)

        """
        # Change to spacecraft = "A" etc. for this request
        if spacecraft in ("Alpha", "Bravo", "Charlie"):
            spacecraft = spacecraft[0]
        templatefile = TEMPLATE_FILES["times_from_orbits"]
        template = JINJA2_ENVIRONMENT.get_template(templatefile)
        request = template.render(
            spacecraft=spacecraft,
            start_orbit=start_orbit,
            end_orbit=end_orbit
        ).encode('UTF-8')
        response = self._get(
            request, asynchronous=False, show_progress=False)
        responsedict = json.loads(response.decode('UTF-8'))
        start_time = parse_datetime(responsedict['start_time'])
        end_time = parse_datetime(responsedict['end_time'])
        return start_time, end_time

    def get_orbit_number(self, spacecraft, input_time):
        """Translate a time to an orbit number.

        Args:
            spacecraft (str): one of ('A','B','C') or
                                ("Alpha", "Bravo", "Charlie")
            input_time (datetime): a point in time

        Returns:
            int: The current orbit number at the input_time

        """
        try:
            input_time = parse_datetime(input_time)
        except TypeError:
            raise TypeError(
                "input_time must be datetime object or ISO-8601 "
                "date/time string"
            )
        # Change to spacecraft = "A" etc. for this request
        if spacecraft in ("Alpha", "Bravo", "Charlie"):
            spacecraft = spacecraft[0]
        collections = ["SW_OPER_MAG{}_LR_1B".format(spacecraft[0])]
        request_inputs = SwarmWPSInputs(
            collection_ids={spacecraft: collections},
            begin_time=input_time,
            end_time=input_time+datetime.timedelta(seconds=1),
            variables=["OrbitNumber"],
            response_type="text/csv"
        )
        request = request_inputs.as_xml(self._templatefiles['sync'])
        retdata = ReturnedDataFile(filetype="csv")
        response_handler = self._response_handler(
            retdata, show_progress=False
        )
        self._get(
            request, asynchronous=False, response_handler=response_handler,
            show_progress=False)
        # self._wps_service.retrieve(request, handler=response_handler)
        return retdata.as_dataframe()["OrbitNumber"][0]

    def get_model_info(self, models=None, custom_model=None,
                       original_response=False):
        """Get model info from server.

        Handles the same models input as .set_products(), and returns a dict
        like:

        {'IGRF12': {
        'expression': 'IGRF12(max_degree=13,min_degree=0)',
        'validity': {'start': '1900-01-01T00:00:00Z', 'end': '2020-01-01T00:00:00Z'
        }, ...}

        If original_response=True, return the list of dicts like:

        {'expression': 'MCO_SHA_2C(max_degree=16,min_degree=0)',
        'name': 'MCO_SHA_2C',
        'validity': {'start': '2013-11-30T14:38:24Z',
        'end': '2018-01-01T00:00:00Z'}}, ...

        Args:
            models (list/dict): as with set_products
            custom_model (str): as with set_products
            original_response (bool)

        Returns:
            dict or list

        """

        def _request_get_model_info(model_expression=None, custom_shc=None):
            """ Make the get_model_info request. """
            templatefile = TEMPLATE_FILES["model_info"]
            template = JINJA2_ENVIRONMENT.get_template(templatefile)
            request = template.render(
                model_expression=model_expression,
                custom_shc=custom_shc,
                response_type="application/json"
            ).encode('UTF-8')
            response = self._get(
                request, asynchronous=False, show_progress=False)
            response_list = json.loads(response.decode('UTF-8'))
            return response_list

        def _build_dict(response_list):
            """ Build dictionary output organised by model name. """
            return {
                model_dict.pop("name"): model_dict
                for model_dict in response_list
            }

        if custom_model:
            with open(custom_model) as custom_shc_file:
                custom_shc = custom_shc_file.read()
            if not models:
                models = ["Custom_Model"]
        else:
            custom_shc = None

        if models is not None:
            _, model_expression = self._parse_models_input(models)
        else:
            model_expression = None

        response = _request_get_model_info(model_expression, custom_shc)

        if not original_response:
            response = _build_dict(response)

        return response

    @staticmethod
    def _check_deprecated_models(models):
        """ Print deprecation warning for deprecated models. """
        deprecated_models = []
        for deprecated_model in DEPRECATED_MODELS:
            for model in models:
                if deprecated_model in model:
                    deprecated_models.append(deprecated_model)
                    break
        for deprecated_model in deprecated_models:
            print("WARNING: Model {} is deprecated. {}".format(
                deprecated_model, DEPRECATED_MODELS[deprecated_model]
            ), file=sys.stdout)

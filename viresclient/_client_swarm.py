import datetime
import json
from collections import OrderedDict

from ._wps.environment import JINJA2_ENVIRONMENT
from ._wps import time_util
from ._client import WPSInputs, ClientRequest
from ._data_handling import ReturnedDataFile

TEMPLATE_FILES = {
    'sync': "vires_fetch_filtered_data.xml",
    'async': "vires_fetch_filtered_data_async.xml"
}

REFERENCES = {
    'General Swarm': (" Swarm Data Handbook, https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook ",
                      " The Swarm Satellite Constellation Application and Research Facility (SCARF) and Swarm data products, https://doi.org/10.5047/eps.2013.07.001 ",
                      " Swarm Science Data Processing and Products (2013), https://link.springer.com/journal/40623/65/11/page/1 ",
                      " Special issue “Swarm science results after 2 years in space (2016), https://www.springeropen.com/collections/swsr ",
                      " Earth's Magnetic Field: Understanding Geomagnetic Sources from the Earth's Interior and its Environment (2017), https://link.springer.com/journal/11214/206/1/page/1 ")
    }

MODEL_REFERENCES = {
    'IGRF12':
        (" International Geomagnetic Reference Field: the 12th generation, https://doi.org/10.1186/s40623-015-0228-9 ",
         " https://www.ngdc.noaa.gov/IAGA/vmod/igrf.html "),
    'SIFM':
        ("Swarm Initial Field Model",
         " The Swarm Initial Field Model for the 2014 geomagnetic field, https://doi.org/10.1002/2014GL062659 "),
    'CHAOS-6-Combined':
        ("CHAOS-6 Core + Static, NB: no magnetospheric part",
         " Recent geomagnetic secular variation from Swarm and ground observatories as estimated in the CHAOS-6 geomagnetic field model, http://doi.org/10.1186/s40623-016-0486-1 ",
         " http://www.space.dtu.dk/english/Research/Scientific_data_and_models/Magnetic_Field_Models "),
    'CHAOS-6-Core': "",
    'CHAOS-6-Static': "",
    'MCO_SHA_2C':
        ("[Comprehensive Inversion]: Core field of CIY4",
         " A comprehensive model of Earth’s magnetic field determined from 4 years of Swarm satellite observations, https://doi.org/10.1186/s40623-018-0896-3 ",
         "Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MCO/SW_OPER_MCO_VAL_2C_20131201T000000_20180101T000000_0401.ZIP "),
    'MCO_SHA_2D':
        ("[Dedicated Chain]: Core field",
         "An algorithm for deriving core magnetic field models from the Swarm data set, https://doi.org/10.5047/eps.2013.07.005 ",
         "Validation: ftp://swarm-diss.eo.esa.int/Level2longterm/MCO/SW_OPER_MCO_VAL_2D_20131126T000000_20180101T000000_0401.ZIP "),
    'MCO_SHA_2F':
        ("[Fast-Track Product]: Core field",),
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
        ("[Dedicated Chain]: Secondary (external/induced) ionospheric field, DIFI",)
}

COLLECTION_REFERENCES = {
    "MAG": (" https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/level-1b-product-definitions#MAGX_LR_1B_Product ",
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
            " https://earth.esa.int/documents/10174/1514862/Swarm-Level-2-EEF-Product-Description ")
}


class SwarmWPSInputs(WPSInputs):
    """Holds the set of inputs to be passed to the request template for Swarm
    """

    def __init__(self,
                 collection_ids=None,
                 model_ids=None,
                 begin_time=None,
                 end_time=None,
                 variables=None,
                 filters=None,
                 sampling_step=None,
                 response_type=None):
        # Set up default values
        # Obligatory - these must be replaced before the request is made
        self.collection_ids = None if collection_ids is None else collection_ids
        self.begin_time = None if begin_time is None else begin_time
        self.end_time = None if end_time is None else end_time
        self.response_type = None if response_type is None else response_type
        # Optional - these defaults will be used if not replaced before the
        #            request is made
        self.model_ids = [] if model_ids is None else model_ids
        self.variables = [] if variables is None else variables
        self.filters = None if filters is None else filters
        self.sampling_step = None if sampling_step is None else sampling_step

        self.names = ('collection_ids',
                      'model_ids',
                      'begin_time',
                      'end_time',
                      'variables',
                      'filters',
                      'sampling_step',
                      'response_type'
                      )

    @property
    def collection_ids(self):
        return self._collection_ids

    @collection_ids.setter
    def collection_ids(self, collection_ids):
        if isinstance(collection_ids, dict) or collection_ids is None:
            self._collection_ids = collection_ids
        else:
            raise TypeError("collection_ids must be a dict")

    def set_collection(self, collection):
        if isinstance(collection, str):
            tag = 'X'
            collections = [collection]
            self.collection_ids = {tag: collections}
        else:
            raise TypeError("collection must be a string")

    @property
    def model_ids(self):
        return self._model_ids

    @model_ids.setter
    def model_ids(self, model_ids):
        if isinstance(model_ids, list):
            self._model_ids = model_ids
        else:
            raise TypeError("tag must be a string and collections a list")

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


class SwarmRequest(ClientRequest):
    """Handles the requests to and downloads from the server.

    Steps to download data:

    1. Set up a connection to the server with: request = SwarmRequest()

    2. Set collections to use with: request.set_collections()

    3. Set parameters to get with: request.set_products()

    4. Set filters to apply with: request.set_range_filter()

    5. Get the data in a chosen time window: request.get_between()

    Args:
        url (str):
        username (str):
        password (str):
        logging_level (str):

    """

    def __init__(self, url=None, username=None, password=None,
                 logging_level="NO_LOGGING"):
        super().__init__(url, username, password, logging_level,
                         server_type="Swarm"
                         )
        self._available = self._set_available_data()
        self._request_inputs = SwarmWPSInputs()
        self._templatefiles = TEMPLATE_FILES
        self._filterlist = []
        self._supported_filetypes = ("csv", "cdf")

    @staticmethod
    def _set_available_data():
        collections_grouped = {
            "MAG": ["SW_OPER_MAG{}_LR_1B".format(x) for x in ("ABC")],
            "EFI": ["SW_OPER_EFI{}_PL_1B".format(x) for x in ("ABC")],
            "IBI": ["SW_OPER_IBI{}TMS_2F".format(x) for x in ("ABC")],
            "TEC": ["SW_OPER_TEC{}TMS_2F".format(x) for x in ("ABC")],
            "FAC": ["SW_OPER_FAC{}TMS_2F".format(x) for x in ("ABC")] +
                   ["SW_OPER_FAC_TMS_2F"],
            "EEF": ["SW_OPER_EEF{}TMS_2F".format(x) for x in ("ABC")]
            }
        collections_flat = [
            item for sublist in list(collections_grouped.values())
            for item in sublist
            ]
        # Build the reverse mapping: "SW_OPER_MAGA_LR_1B": "MAG" etc
        collections_to_keys = dict.fromkeys(collections_flat)
        for coll in collections_to_keys:
            for key in list(collections_grouped.keys()):
                if key in coll:
                    collections_to_keys[coll] = key

        measurements = {
            "MAG": "F,dF_AOCS,dF_other,F_error,B_VFM,B_NEC,dB_Sun,dB_AOCS,dB_other,B_error,q_NEC_CRF,Att_error,Flags_F,Flags_B,Flags_q,Flags_Platform,ASM_Freq_Dev".split(","),
            "EFI": "v_SC,v_ion,v_ion_error,E,E_error,dt_LP,n,n_error,T_ion,T_ion_error,T_elec,T_elec_error,U_SC,U_SC_error,v_ion_H,v_ion_H_error,v_ion_V,v_ion_V_error,rms_fit_H,rms_fit_V,var_x_H,var_y_H,var_x_V,var_y_V,dv_mtq_H,dv_mtq_V,SAA,Flags_LP,Flags_LP_n,Flags_LP_T_elec,Flags_LP_U_SC,Flags_TII,Flags_Platform,Maneuver_Id".split(","),
            "IBI": "Bubble_Index,Bubble_Probability,Flags_Bubble,Flags_F,Flags_B,Flags_q".split(","),
            "TEC": "GPS_Position,LEO_Position,PRN,L1,L2,P1,P2,S1,S2,Absolute_STEC,Relative_STEC,Relative_STEC_RMS,DCB,DCB_Error".split(","),
            "FAC": "IRC,IRC_Error,FAC,FAC_Error,Flags,Flags_F,Flags_B,Flags_q".split(","),
            "EEF": "EEF,RelErr,flags".split(",")
            }

        models = """
            IGRF12, SIFM, CHAOS-6-Combined, CHAOS-6-Core, CHAOS-6-Static,
            MCO_SHA_2C, MCO_SHA_2D, MCO_SHA_2F, MLI_SHA_2C, MLI_SHA_2D,
            MMA_SHA_2C-Primary, MMA_SHA_2C-Secondary,
            MMA_SHA_2F-Primary, MMA_SHA_2F-Secondary,
            MIO_SHA_2C-Primary, MIO_SHA_2C-Secondary,
            MIO_SHA_2D-Primary, MIO_SHA_2D-Secondary
            """.replace("\n", "").replace(" ", "").split(",")

        auxiliaries = """
            Timestamp, Latitude, Longitude, Radius, Spacecraft,
            SyncStatus, Kp, Dst, IMF_BY_GSM, IMF_BZ_GSM, IMF_V, F10_INDEX,
            OrbitSource, OrbitNumber, AscendingNodeTime,
            AscendingNodeLongitude, QDLat, QDLon, QDBasis, MLT, SunDeclination,
            SunHourAngle, SunRightAscension, SunAzimuthAngle, SunZenithAngle,
            SunLongitude, SunVector, DipoleAxisVector, NGPLatitude, NGPLongitude,
            DipoleTiltAngle, UpwardCurrent, TotalCurrent,
            DivergenceFreeCurrentFunction, F_AMPS, B_NEC_AMPS
            """.replace("\n", "").replace(" ", "").split(",")

        return {
            "collections_grouped": collections_grouped,
            "collections": collections_flat,
            "collections_to_keys": collections_to_keys,
            "measurements": measurements,
            "models": models,
            "auxiliaries": auxiliaries
            }

    def available_collections(self, details=True):
        """Show details of available collections.

        Args:
            details (bool): If True then print a nice output.
                If False then return a list of available collections.

        """
        if details:
            print("General References:")
            for i in REFERENCES["General Swarm"]:
                print(i)
            print()
            for key, val in self._available["collections_grouped"].items():
                print(key)
                for i in val:
                    print('  ', i)
                for ref in COLLECTION_REFERENCES[key]:
                    print(ref)
                print()
        else:
            return self._available["collections"]

    def available_measurements(self, collection=None):
        """Returns a list of the available measurements for the chosen collection.

        Args:
            collection (str): one of: ("MAG", "EFI", "IBI", "TEC", "FAC", "EEF")

        """
        keys = list(self._available["measurements"].keys())
        if collection in keys:
            collection_key = collection
            return self._available["measurements"][collection_key]
        elif collection in self._available["collections"]:
            collection_key = self._available["collections_to_keys"][collection]
            return self._available["measurements"][collection_key]
        elif collection is None:
            return self._available["measurements"]
        else:
            raise Exception(
                "collection must be one of {}\nor\n{}".format(
                    ", ".join(keys),
                    "\n".join(self._available["collections"])
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
        param_choices = "F C D MCO MLI MMA MIO".split(' ')

        def filter_by_param(d, param):
            if param not in param_choices:
                raise Exception("param must be one of {}".format(param_choices))
            if param in "F C D".split(' '):
                param = '2' + param
            if isinstance(d, list):
                d = [i for i in d if param in i]
            elif isinstance(d, dict):
                d = {k: d[k] for k in d.keys() if param in k}
            else:
                raise TypeError("d should be a dict or a list")
            return d

        if details:
            d = MODEL_REFERENCES
        else:
            d = self._available["models"]
        # Filter the dict/list to only include those that contain param
        if param is not None:
            d = filter_by_param(d, param)

        if nice_output and details:
            d = OrderedDict(sorted(d.items()))
            for key, val in d.items():
                print(key)
                for i in val:
                    print(i)
                print()
        else:
            return d

    def available_auxiliaries(self):
        """Returns a list of the available auxiliary parameters.
        """
        return self._available["auxiliaries"]

    def set_collection(self, collection):
        """Set the collection to use (sets satellite implicitly).

        Note:
            Currently limited to one collection, one satellite.

        Args:
            collection (str): one of .available_collections()

        """
        if collection not in self._available["collections"]:
            raise Exception(
                "Invalid collection. "
                "Check available with SwarmRequest.available_collections()")
        else:
            self._collection = collection
            self._request_inputs.set_collection(collection)

    def set_products(self, measurements=None, models=None, auxiliaries=None,
                     residuals=False, sampling_step=None
                     ):
        """Set the combination of products to retrieve.

        If residuals=True then just get the measurement-model residuals,
        otherwise get both measurement and model values.

        Args:
            measurements (list(str)): from .available_measurements(collection_key)
            models (list(str)): from .available_models()
            auxiliaries (list(str)): from .available_auxiliaries()
            residuals (bool): True if only returning measurement-model residual
            sampling_step (str): ISO_8601 duration, e.g. 10 seconds: PT10S, 1 minute: PT1M

        """
        measurements = [] if measurements is None else measurements
        models = [] if models is None else models
        auxiliaries = [] if auxiliaries is None else auxiliaries
        # Check the chosen measurements are available for the set collection
        collection_key = self._available["collections_to_keys"][self._collection]
        for x in measurements:
            if x not in self._available["measurements"][collection_key]:
                raise Exception(
                    "Measurement '{}' not available for collection '{}'. "
                    "Check available with "
                    "SwarmRequest.available_measurements({})".format(
                        x, collection_key, collection_key
                    ))
        # Check chosen model is available
        for x in models:
            if x not in self._available["models"]:
                raise Exception(
                    "Model '{}' not available. Check available with "
                    "SwarmRequest.available_models()".format(x)
                    )
        # Check chosen aux is available
        for x in auxiliaries:
            if x not in self._available["auxiliaries"]:
                raise Exception(
                    "'{}' not available. Check available with "
                    "SwarmRequest.available_auxiliaries()".format(x)
                    )
        # Set up the variables that actually get passed to the WPS request
        variables = []
        if not residuals:
            variables += measurements
            # Model values
            for model_name in models:
                for measurement in measurements:
                    variables += ["%s_%s" % (measurement, model_name)]
        elif residuals:
            # Model residuals
            for model_name in models:
                for measurement in measurements:
                    variables += ["%s_res_%s" % (measurement, model_name)]
        variables += auxiliaries

        # Set these in the SwarmWPSInputs object
        self._request_inputs.model_ids = models
        self._request_inputs.variables = variables
        self._request_inputs.sampling_step = sampling_step

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

    def clear_range_filter(self):
        """Remove all applied filters."""
        self._filterlist = []
        self._request_inputs.filters = None

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
        templatefile = "vires_times_from_orbits.xml"
        template = JINJA2_ENVIRONMENT.get_template(templatefile)
        request = template.render(
            spacecraft=spacecraft,
            start_orbit=start_orbit,
            end_orbit=end_orbit
        ).encode('UTF-8')
        response = self._wps_service.retrieve(request)
        responsedict = json.loads(response.decode('UTF-8'))
        start_time = time_util.parse_datetime(responsedict['start_time'])
        end_time = time_util.parse_datetime(responsedict['end_time'])
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
            retdata.file, show_progress=False
        )
        self._wps_service.retrieve(request, handler=response_handler)
        return retdata.as_dataframe()["OrbitNumber"][0]

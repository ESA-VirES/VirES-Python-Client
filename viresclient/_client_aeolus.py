import datetime, json

from ._client import WPSInputs, ClientRequest
from ._data import CONFIG_AEOLUS
import pandas as pd
# from pandas import DataFrame, json_normalize

TEMPLATE_FILES = {
    'sync': "vires_aeolus_fetch_filtered_data.xml",
    'async': "vires_aeolus_fetch_filtered_data_async.xml"
}


class AeolusWPSInputs(WPSInputs):

    NAMES = [
        'processId',
        'collection_ids',
        'begin_time',
        'end_time',
        'response_type',
        'fields',
        'filters',
        'aux_type',
        'observation_fields',
        'measurement_fields',
        'mie_profile_fields',
        'rayleigh_profile_fields',
        'mie_wind_fields',
        'rayleigh_wind_fields',
        'ica_fields',
        'sca_fields',
        'mca_fields',
        'bbox',
    ]

    def __init__(self,
                 processId=None,
                 collection_ids=None,
                 begin_time=None,
                 end_time=None,
                 response_type=None,
                 fields=None,
                 filters=None,
                 aux_type=None,
                 observation_fields=None,
                 measurement_fields=None,
                 sca_fields=None,
                 ica_fields=None,
                 mca_fields=None,
                 mie_profile_fields=None,
                 rayleigh_profile_fields=None,
                 mie_wind_fields=None,
                 rayleigh_wind_fields=None,
                 bbox=None,
                 ):
        # Obligatory
        self.processId = None if processId is None else processId
        self.collection_ids = None if collection_ids is None else collection_ids
        self.begin_time = None if begin_time is None else begin_time
        self.end_time = None if end_time is None else end_time
        self.response_type = None if response_type is None else response_type
        # Optional
        self.fields = fields
        self.filters = filters
        self.aux_type = aux_type
        self.observation_fields = observation_fields
        self.measurement_fields = measurement_fields
        self.ica_fields = ica_fields
        self.mca_fields = mca_fields
        self.sca_fields = sca_fields
        self.mie_profile_fields = mie_profile_fields
        self.rayleigh_profile_fields = rayleigh_profile_fields
        self.mie_wind_fields = mie_wind_fields
        self.rayleigh_wind_fields = rayleigh_wind_fields
        self.bbox = bbox

    @property
    def as_dict(self):
        # Add these as properties later:
        self._filters = self.filters
        self._fields = self.fields
        self._observation_fields = self.observation_fields
        self._measurement_fields = self.measurement_fields
        self._mie_profile_fields = self.mie_profile_fields
        self._rayleigh_profile_fields = self.rayleigh_profile_fields
        self._mie_wind_fields = self.mie_wind_fields
        self._rayleigh_wind_fields = self.rayleigh_wind_fields
        self._ica_fields = self.ica_fields
        self._mca_fields = self.mca_fields
        self._sca_fields = self.sca_fields
        self._bbox = self.bbox
        return {key: self.__dict__['_{}'.format(key)] for key in self.NAMES}

    @property
    def processId(self):
        return self.processId

    @processId.setter
    def processId(self, processId):
        if isinstance(processId, str) or processId is None:
            self._processId = processId
        else:
            raise TypeError

    @property
    def collection_ids(self):
        return self._collection_ids

    @collection_ids.setter
    def collection_ids(self, collection):
        if isinstance(collection, str) or collection is None:
            # tag = 'X'
            # collections = [collection]
            # self._collection_ids = {tag: collections}
            self._collection_ids = [collection]
        else:
            raise TypeError("collection_ids must be a string")

    # @collection_ids.setter
    # def collection_ids(self, collection_ids):
    #     if isinstance(collection_ids, dict) or collection_ids is None:
    #         self._collection_ids = collection_ids
    #     else:
    #         raise TypeError("collection_ids must be a dict")
    #
    # def set_collection(self, collection):
    #     if isinstance(collection, str):
    #         tag = 'X'
    #         collections = [collection]
    #         self.collection_ids = {tag: collections}
    #     else:
    #         raise TypeError("collection must be a string")

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
    def filters(self):
        return self._filters

    @filters.setter
    def filters(self, filters):
        if isinstance(filters, str) or filters is None:
            self._filters = filters
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
    def aux_type(self):
        return self._aux_type

    @aux_type.setter
    def aux_type(self, aux_type):
        if isinstance(aux_type, str) or aux_type is None:
            self._aux_type = aux_type
        else:
            raise TypeError


class AeolusRequest(ClientRequest):
    """Handles the requests to and downloads from the server.

    Args:
        url (str):
        username (str):
        password (str):
        token (str):
        config (str or ClientConfig):
        logging_level (str):

    """
    def __init__(self, url=None, token=None,
                 config=None, logging_level="NO_LOGGING"):
        super().__init__(
            url, token, config, logging_level,
            server_type="Aeolus"
            )
        # self._available = self._set_available_data()
        self._request_inputs = AeolusWPSInputs()
        self._request_inputs.processId = 'aeolus:level1B'
        self._templatefiles = TEMPLATE_FILES
        self._filterlist = {}
        self._supported_filetypes = ("nc",)

    def set_collection(self, collection):
        # self._request_inputs.set_collection = collection
        # We set the process id corresponding to the selected collection
        collection_mapping = {
            "ALD_U_N_1B": "aeolus:level1B",
            "ALD_U_N_2A": "aeolus:level2A",
            "ALD_U_N_2B": "aeolus:level2B",
            "ALD_U_N_2C": "aeolus:level2C",
            "AUX_MRC_1B": "aeolus:level1B:AUX:MRC",
            "AUX_RRC_1B": "aeolus:level1B:AUX:RRC",
            "AUX_ISR_1B": "aeolus:level1B:AUX:ISR",
            "AUX_ZWC_1B": "aeolus:level1B:AUX:ZWC",
            "AUX_MET_12": "aeolus:AUX:MET",
        }
        if collection in collection_mapping:
            self._request_inputs.processId = collection_mapping[collection]
            self._request_inputs.collection_ids = collection
        else:
            raise ValueError("Product not found")

    def available_collections(
        self, collection=None, field_type=None, like=None, details=True):
        return CONFIG_AEOLUS
    
    def print_available_collections(
        self, collection=None, field_type=None, regex=None, details=True):
        pd.set_option("max_rows", None)
        pd.set_option('display.max_colwidth', None)
        collection_dfs = []
        collection_names = []
        for c_name, collection_obj in CONFIG_AEOLUS["collections"].items():
            field_dfs = []
            for _, ft in collection_obj.items():
                fdf = pd.DataFrame(ft).transpose()
                if regex != None:
                    fdf = fdf[fdf.index.str.contains(regex, regex=True)]
                field_dfs.append(fdf)
            ft_df = pd.concat(
                field_dfs, names=["field type"], keys=collection_obj.keys()
            )
            if field_type != None:
                try: 
                    ft_df = ft_df.loc[field_type]
                    collection_dfs.append(ft_df)
                    collection_names.append(c_name)
                except KeyError: 
                    pass
            else:
                collection_dfs.append(ft_df)
                collection_names.append(c_name)
        if len(collection_dfs) == 0:
            print("Passed field_type not found")
            return
        df = pd.concat(collection_dfs, names=["collection"], keys=collection_names)
        df.fillna("-",inplace=True)
        if collection != None:
            try: 
                df = df.loc[collection]
            except KeyError: 
                print("Passed collection not found")
                return
        if not details:
            df = df.filter('')
        return df

    def set_fields(self,
                   observation_fields=None, measurement_fields=None,
                   ica_fields=None, sca_fields=None, mca_fields=None,
                   mie_profile_fields=None, rayleigh_profile_fields=None,
                   rayleigh_wind_fields=None, mie_wind_fields=None,
                   fields=None):
        if observation_fields:
            self._request_inputs.observation_fields = ",".join(observation_fields)
        if measurement_fields:
            self._request_inputs.measurement_fields = ",".join(measurement_fields)
        if ica_fields:
            self._request_inputs.ica_fields = ",".join(ica_fields)
        if mca_fields:
            self._request_inputs.mca_fields = ",".join(mca_fields)
        if sca_fields:
            self._request_inputs.sca_fields = ",".join(sca_fields)
        if mie_profile_fields:
            self._request_inputs.mie_profile_fields = ",".join(mie_profile_fields)
        if rayleigh_profile_fields:
            self._request_inputs.rayleigh_profile_fields = ",".join(rayleigh_profile_fields)
        if rayleigh_wind_fields:
            self._request_inputs.rayleigh_wind_fields = ",".join(rayleigh_wind_fields)
        if mie_wind_fields:
            self._request_inputs.mie_wind_fields = ",".join(mie_wind_fields)
        if fields:
            self._request_inputs.fields = ",".join(fields)

    def set_variables(self, aux_type=None, fields=None):
        self._request_inputs.aux_type = aux_type
        self._request_inputs.fields = fields

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
        # Update filter dictionary
        self._filterlist[parameter] = {
            "min": minimum,
            "max": maximum
        }
        # Update the inputs object with dictionary converted
        # to JSON used by XML template
        self._request_inputs.filters = json.dumps(self._filterlist)
        return self

    def clear_range_filter(self):
        """Remove all applied filters."""
        self._filterlist = []
        self._request_inputs.filters = None
        return self


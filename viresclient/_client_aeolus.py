import datetime

from ._client import WPSInputs, ClientRequest

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
        'mie_profile_fields',
        'rayleigh_profile_fields',
        'mie_wind_fields',
        'rayleigh_wind_fields',
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
        self._mie_profile_fields = self.mie_profile_fields
        self._rayleigh_profile_fields = self.rayleigh_profile_fields
        self._mie_wind_fields = self.mie_wind_fields
        self._rayleigh_wind_fields = self.rayleigh_wind_fields
        self._bbox = self.bbox
        return {key: self.__dict__['_{}'.format(key)] for key in self.names}

    @property
    def processId(self):
        return self._processID

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

    def __init__(self, url=None, username=None, password=None, token=None,
                 config=None, logging_level="NO_LOGGING"):
        super().__init__(
            url, username, password, token, config, logging_level,
            server_type="Aeolus"
            )
        # self._available = self._set_available_data()
        self._request_inputs = AeolusWPSInputs()
        self._request_inputs.processId = 'aeolus:level1B:AUX'
        self._templatefiles = TEMPLATE_FILES
        self._filterlist = []
        self._supported_filetypes = ("nc",)

    def set_collection(self, collection):
        # self._request_inputs.set_collection = collection
        self._request_inputs.collection_ids = collection

    def set_variables(self, aux_type=None, fields=None):
        self._request_inputs.aux_type = aux_type
        self._request_inputs.fields = fields

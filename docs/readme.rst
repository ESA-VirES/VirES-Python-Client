Introduction
------------

This is the documentation for the ``viresclient`` Python package. This is a tool which connects to a VirES server through the `WPS <http://www.opengeospatial.org/standards/wps>`_ interface and handles product requests and downloads.

Installation
------------

It can currently be installed with::

  pip install viresclient

Dependencies::

  Jinja2
  pandas
  cdflib
  tables
  tqdm

Example usage
-------------
Import the package and set up the connection to the server:

.. code-block:: python

  from viresclient import ClientRequest
  import datetime as dt

  url = "https://staging.viresdisc.vires.services/openows"
  username = ""
  password = ""

  request = ClientRequest(url, username, password)

Choose which collection to access:

.. code-block:: python

  collection = "SW_OPER_MAGA_LR_1B"

  request.set_collection(collection)

Choose measurements and models to evaluate:

.. code-block:: python

  measurements = ["F","B_NEC"]
  models = ["MCO_SHA_2C","MMA_SHA_2C-Primary"]
  auxiliaries = ["OrbitNumber","SunZenithAngle","QDLat","QDLon","MLT"]

  request.set_products(measurements, models, auxiliaries, residuals=False, subsample="PT10S")

Set a parameter range filter to apply. You can add multiple filters in sequence

.. code-block:: python

  parameter = "Latitude"
  minimum = 0
  maximum = 90

  request.set_range_filter(parameter, minimum, maximum)

  request.set_range_filter("Longitude", 0, 90)

Specify the time range from which to retrieve data, make the request to the server (specifying the output file format, currently either csv or cdf):

.. code-block:: python

  start_time = dt.datetime(2016,1,1)
  end_time = dt.datetime(2016,1,2)

  data = request.get_between(start_time, end_time, filetype="cdf", asynchronous=True)

Transfer your data to a (``pandas``) dataframe or save it:

.. code-block:: python

  df = data.as_dataframe()
  data.to_file('outfile.cdf', overwrite=False)

Convert to an HDF5 file:

.. code-block:: python

  data.to_file('outfile.h5', hdf=True, overwrite=False)

  import pandas as pd
  df = pd.read_hdf('outfile.h5')

The returned data has columns for:
 - ``Spacecraft, Timestamp, Latitude, Longitude, Radius``
 - those specified in ``measurements`` and ``auxiliaries`` above
... and model values and residuals, named as:
   - ``F_<model_id>``           -- scalar field
   - ``B_NEC_<model_id>``       -- vector field
   - ``F_res_<model_id>``       -- scalar field residual (``F - F_<model_id>``)
   - ``B_NEC_res_<model_id>``   -- vector field residual (``B_NEC - B_NEC_<model_id>``)

Available parameters for Swarm data
-----------------------------------

``collections`` (replace x with A, B, or C for Alpha, Bravo, or Charlie)::

  SW_OPER_MAGx_LR_1B
  SW_OPER_EFIx_PL_1B
  SW_OPER_IBIxTMS_2F
  SW_OPER_TECxTMS_2F
  SW_OPER_FACxTMS_2F
  SW_OPER_EEFxTMS_2F

For Alpha-Charlie FAC: ``collection="SW_OPER_FAC_TMS_2F"``.

The ``measurements``, ``models``, and ``auxiliaries`` chosen will match the cadence of the ``collection`` chosen.

``measurements``:

Choose from one of the following sets, corresponding to the collection chosen above.

For MAG::

  F,dF_AOCS,dF_other,F_error,B_VFM,B_NEC,dB_Sun,dB_AOCS,dB_other,B_error,q_NEC_CRF,Att_error,Flags_F,Flags_B,Flags_q,Flags_Platform,ASM_Freq_Dev

For EFI::

  v_SC,v_ion,v_ion_error,E,E_error,dt_LP,n,n_error,T_ion,T_ion_error,T_elec,T_elec_error,U_SC,U_SC_error,v_ion_H,v_ion_H_error,v_ion_V,v_ion_V_error,rms_fit_H,rms_fit_V,var_x_H,var_y_H,var_x_V,var_y_V,dv_mtq_H,dv_mtq_V,SAA,Flags_LP,Flags_LP_n,Flags_LP_T_elec,Flags_LP_U_SC,Flags_TII,Flags_Platform,Maneuver_Id

For IBI::

  Bubble_Index,Bubble_Probability,Flags_Bubble,Flags_F,Flags_B,Flags_q

For TEC::

  GPS_Position,LEO_Position,PRN,L1,L2,P1,P2,S1,S2,Absolute_STEC,Relative_STEC,Relative_STEC_RMS,DCB,DCB_Error

For FAC::

  IRC,IRC_Error,FAC,FAC_Error,Flags,Flags_F,Flags_B,Flags_q

For EEF::

  EEF,RelErr,flags

``models`` (``residuals`` available when combined with MAG ``measurements``)::

  IGRF12, SIFM, CHAOS-6-Combined, CHAOS-6-Core, CHAOS-6-Static,
  MCO_SHA_2C, MCO_SHA_2D, MCO_SHA_2F, MLI_SHA_2C, MLI_SHA_2D,
  MMA_SHA_2C-Primary, MMA_SHA_2C-Secondary,
  MMA_SHA_2F-Primary, MMA_SHA_2F-Secondary,
  MIO_SHA_2C-Primary, MIO_SHA_2C-Secondary,
  MIO_SHA_2D-Primary, MIO_SHA_2D-Secondary

``auxiliaries``::

  SyncStatus, Kp, Dst, IMF_BY_GSM, IMF_BZ_GSM, IMF_V, F10_INDEX,
  OrbitSource, OrbitNumber, AscendingNodeTime,
  AscendingNodeLongitude, QDLat, QDLon, QDBasis, MLT, SunDeclination,
  SunHourAngle, SunRightAscension, SunAzimuthAngle, SunZenithAngle,
  SunLongitude, SunVector, DipoleAxisVector, NGPLatitude, NGPLongitude,
  DipoleTiltAngle,

  UpwardCurrent, TotalCurrent,
  DivergenceFreeCurrentFunction, F_AMPS, B_NEC_AMPS

Standard positional variables always returned::

  Timestamp,Latitude,Longitude,Radius,Spacecraft

NB: the AMPS model is currently accessible as "auxiliaries" instead of a "model".

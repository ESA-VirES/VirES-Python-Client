Available parameters for Swarm data
===================================

.. note::

  | `See also: Jupyter notebook about data and model availability <https://swarm-vre.readthedocs.io/en/latest/Swarm_notebooks/02b__viresclient-Available-Data.html>`_ - check out the other demo notebooks there too. If you can't see a suitable recipe to help you get started, do `get in touch <https://swarm-vre.readthedocs.io/en/latest/help.html>`_ (email ashley.smith@ed.ac.uk) and I will help you out.

You can check which parameters are available with:

.. code-block:: python

  from viresclient import SwarmRequest
  request = SwarmRequest()
  request.available_collections()
  request.available_measurements("MAG")
  request.available_measurements("SW_OPER_MAGA_LR_1B")
  request.available_models()
  request.available_auxiliaries()

The available measurements are segregated according to the "collection" (essentially Swarm products): each ``collection`` has a number of ``measurements`` associated with it, and the appropriate collection must be set in order to access the measurements. ``auxiliaries`` are available together with any set ``collection``. ``models`` provide magnetic model evaluation on demand, at the locations of the time series which is being accessed (when accessing magnetic field data such as ``MAG`` or ``MAG_HR``). Standard positional variables always returned, such as Timestamp, Spacecraft, geocentric Latitude, Longitude, Radius.

----

See the `Swarm Data Handbook`_ for details about the products and `Swarm Product Demos`_ (Jupyter notebooks) for basic recipes to get started.

.. _`Swarm Data Handbook`: https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/

.. _`Swarm Product Demos`: https://swarm-vre.readthedocs.io/en/latest/Swarm_notebooks.html#swarm-product-demos

----

``collections``
---------------

Collections are grouped according to a type containing similar measurements (i.e. the same product from different spacecraft). The collection type can be given to :py:meth:`viresclient.SwarmRequest.available_collections` to retrieve the full collection names. These cover the Swarm data products as below (replace x with A, B, or C for Alpha, Bravo, or Charlie):

======================== ================ ==============================================================
Collection full name     Collection type  Description
======================== ================ ==============================================================
SW_OPER_MAGx_LR_1B       MAG              Magnetic field (1Hz) from VFM and ASM
SW_OPER_MAGx_HR_1B       MAG_HR           Magnetic field (50Hz) from VFM
SW_OPER_EFIx_LP_1B       EFI              Electric field instrument (Langmuir probe measurements at 2Hz)
SW_OPER_IPDxIRR_2F       IPD              Ionospheric plasma characteristics (derived quantities at 1Hz)
SW_OPER_TECxTMS_2F       TEC              Total electron content
SW_OPER_FACxTMS_2F       FAC              Field-aligned currents (single satellite)
SW_OPER_FAC_TMS_2F       FAC              Field-aligned currents (dual-satellite A-C)
SW_OPER_EEFxTMS_2F       EEF              Equatorial electric field
SW_OPER_IBIxTMS_2F       IBI              Ionospheric bubble index
======================== ================ ==============================================================

The AEBS (auroral electrojets and boundaries) products are a bit more complicated:

============================================ ================================= ==============================================================
Collection full name                         Collection type                   Description
============================================ ================================= ==============================================================
SW_OPER_AEJxLPL_2F                           AEJ_LPL                           Auroral electrojets line profile - Line current method (LC)
SW_OPER_AEJxLPL_2F:Quality                   AEJ_LPL:Quality                   -> Quality indicators per orbital section from LC
SW_OPER_AEJxPBL_2F                           AEJ_PBL                           -> Peaks and boundaries from LC
SW_OPER_AEJxLPS_2F                           AEJ_LPS                           Auroral electrojets line profile - SECS method
SW_OPER_AEJxLPS_2F:Quality                   AEJ_LPS:Quality                   -> Quality indicators per orbital section from SECS
SW_OPER_AEJxPBS_2F                           AEJ_PBS                           -> Peaks and boundaries from SECS
SW_OPER_AEJxPBS_2F:GroundMagneticDisturbance AEJ_PBS:GroundMagneticDisturbance -> Location and strength of peak ground disturbance per pass
SW_OPER_AOBxFAC_2F                           AOB_FAC                           Auroral oval boundaries derived from FACs
============================================ ================================= ==============================================================

The AUX_OBS collections contain ground magnetic observatory data from `INTERMAGNET <https://intermagnet.github.io/data_conditions.html>`_ and `WDC <http://www.wdc.bgs.ac.uk/>`_. Please note that these data are provided under different usage terms than the ESA data, and must be acknowledged accordingly.

======================== ================ ==============================================================
Collection full name     Collection type  Description
======================== ================ ==============================================================
SW_OPER_AUX_OBSH2\_       AUX_OBSH         Hourly values derived from both WDC and INTERMAGNET data
SW_OPER_AUX_OBSM2\_       AUX_OBSM         Minute values from INTERMAGNET
SW_OPER_AUX_OBSS2\_       AUX_OBSS         Second values from INTERMAGNET
======================== ================ ==============================================================

The AUX_OBS collections contain data from all observatories together (distinguishable by the ``IAGA_code`` variable). Data from a single observatory can be accessed with special collection names like ``SW_OPER_AUX_OBSM2_:ABK`` where ``ABK`` can be replaced with the IAGA code of the observatory. Use :py:meth:`viresclient.SwarmRequest.available_observatories` to find these IAGA codes.

The ``measurements``, ``models``, and ``auxiliaries`` chosen will match the cadence of the ``collection`` chosen.

----

``measurements``
---------------- 

Choose combinations of measurements from one of the following sets, corresponding to the collection chosen above. The collection full name or collection type can be given to :py:meth:`viresclient.SwarmRequest.available_measurements` to retrieve the list of available measurements for a given collection (e.g. ``request.available_measurements("SW_OPER_MAGA_LR_1B")``)

=============== ==============================================================================================================================================================================================================================================================================================
Collection type Available measurement names
=============== ==============================================================================================================================================================================================================================================================================================
MAG             ``F,dF_AOCS,dF_other,F_error,B_VFM,B_NEC,dB_Sun,dB_AOCS,dB_other,B_error,q_NEC_CRF,Att_error,Flags_F,Flags_B,Flags_q,Flags_Platform,ASM_Freq_Dev``
MAG_HR          ``F,B_VFM,B_NEC,dB_Sun,dB_AOCS,dB_other,B_error,q_NEC_CRF,Att_error,Flags_B,Flags_q,Flags_Platform,ASM_Freq_Dev``
EFI             ``U_orbit,Ne,Ne_error,Te,Te_error,Vs,Vs_error,Flags_LP,Flags_Ne,Flags_Te,Flags_Vs``
IPD             ``Ne,Te,Background_Ne,Foreground_Ne,PCP_flag,Grad_Ne_at_100km,Grad_Ne_at_50km,Grad_Ne_at_20km,Grad_Ne_at_PCP_edge,ROD,RODI10s,RODI20s,delta_Ne10s,delta_Ne20s,delta_Ne40s,Num_GPS_satellites,mVTEC,mROT,mROTI10s,mROTI20s,IBI_flag,Ionosphere_region_flag,IPIR_index,Ne_quality_flag,TEC_STD``
TEC             ``GPS_Position,LEO_Position,PRN,L1,L2,P1,P2,S1,S2,Elevation_Angle,Absolute_VTEC,Absolute_STEC,Relative_STEC,Relative_STEC_RMS,DCB,DCB_Error``
FAC             ``IRC,IRC_Error,FAC,FAC_Error,Flags,Flags_F,Flags_B,Flags_q``
EEF             ``EEF,EEJ,RelErr,Flags``
IBI             ``Bubble_Index,Bubble_Probability,Flags_Bubble,Flags_F,Flags_B,Flags_q``
=============== ==============================================================================================================================================================================================================================================================================================

AEBS products:

================================= ================================================================================
Collection type                   Available measurement names
================================= ================================================================================
AEJ_LPL                           ``Latitude_QD,Longitude_QD,MLT_QD,J_NE,J_QD``
AEJ_LPL:Quality                   ``RMS_misfit,Confidence``
AEJ_PBL                           ``Latitude_QD,Longitude_QD,MLT_QD,J_QD,Flags,PointType``
AEJ_LPS                           ``Latitude_QD,Longitude_QD,MLT_QD,J_CF_NE,J_DF_NE,J_CF_SemiQD,J_DF_SemiQD,J_R``
AEJ_LPS:Quality                   ``RMS_misfit,Confidence``
AEJ_PBS                           ``Latitude_QD,Longitude_QD,MLT_QD,J_DF_SemiQD,Flags,PointType``
AEJ_PBS:GroundMagneticDisturbance ``B_NE``
AOB_FAC                           ``Latitude_QD,Longitude_QD,MLT_QD,Boundary_Flag,Quality,Pair_Indicator``
================================= ================================================================================

AUX_OBS products:

=============== =========================================
Collection type Available measurement names
=============== =========================================
AUX_OBSH        ``B_NEC,F,IAGA_code,Quality,SensorIndex``
AUX_OBSM        ``B_NEC,F,IAGA_code,Quality``
AUX_OBSS        ``B_NEC,F,IAGA_code,Quality``
=============== =========================================

----

``models``
----------

Models are evaluated along the satellite track at the positions of the time series that has been requested. These must be used together with one of the MAG collections, and one or both of the "F" and "B_NEC" measurements. This can yield either the model values together with the measurements, or the data-model residuals.

.. note::

  For a good estimate of the ionospheric field measured by a Swarm satellite (with the core, crust and magnetosphere effects removed) use a composed model defined as:
  ``models=["'CHAOS-full' = 'CHAOS-Core' + 'CHAOS-Static' + 'CHAOS-MMA-Primary' + 'CHAOS-MMA-Secondary'"]``
  `(click for more info) <https://github.com/klaundal/notebooks/blob/master/get_external_field.ipynb>`_
  
  This composed model can also be accessed by an alias: ``models=["CHAOS"]`` which represents the full CHAOS model

  See `Magnetic Earth <https://magneticearth.org/pages/models.html>`_ for an introduction to geomagnetic models.

::

  IGRF,

  # Comprehensive inversion (CI) models:
  MCO_SHA_2C,                                # Core
  MLI_SHA_2C,                                # Lithosphere
  MMA_SHA_2C-Primary, MMA_SHA_2C-Secondary,  # Magnetosphere
  MIO_SHA_2C-Primary, MIO_SHA_2C-Secondary,  # Ionosphere

  # Dedicated inversion models:
  MCO_SHA_2D,                                # Core
  MLI_SHA_2D, MLI_SHA_2E                     # Lithosphere
  MIO_SHA_2D-Primary, MIO_SHA_2D-Secondary   # Ionosphere
  AMPS                                       # High-latitude ionosphere

  # Fast-track models:
  MMA_SHA_2F-Primary, MMA_SHA_2F-Secondary,  # Magnetosphere

  # CHAOS models:
  CHAOS-Core,                                # Core
  CHAOS-Static,                              # Lithosphere
  CHAOS-MMA-Primary, CHAOS-MMA-Secondary     # Magnetosphere

  # Other lithospheric models:
  MF7, LCS-1

  # Aliases for compositions of the above models (shortcuts)
  MCO_SHA_2X    # 'CHAOS-Core'
  CHAOS-MMA     # 'CHAOS-MMA-Primary' + 'CHAOS-MMA-Secondary'
  CHAOS         # 'CHAOS-Core' + 'CHAOS-Static' + 'CHAOS-MMA-Primary' + 'CHAOS-MMA-Secondary'
  MMA_SHA_2F    # 'MMA_SHA_2F-Primary' + 'MMA_SHA_2F-Secondary'
  MMA_SHA_2C    # 'MMA_SHA_2C-Primary' + 'MMA_SHA_2C-Secondary'
  MIO_SHA_2C    # 'MIO_SHA_2C-Primary' + 'MIO_SHA_2C-Secondary'
  MIO_SHA_2D    # 'MIO_SHA_2D-Primary' + 'MIO_SHA_2D-Secondary'
  SwarmCI       # 'MCO_SHA_2C' + 'MLI_SHA_2C' + 'MIO_SHA_2C-Primary' + 'MIO_SHA_2C-Secondary' + 'MMA_SHA_2C-Primary' + 'MMA_SHA_2C-Secondary'

Custom (user uploaded) models can be provided as a .shc file and become accessible in the same way as pre-defined models, under the name ``"Custom_Model"``.

Flexible evaluation of models and defining new derived models is possible with the "model expressions" functionality whereby models can be defined like:

.. code-block:: python

  request.set_products(
    ...
    models=["Combined_model = 'MMA_SHA_2F-Primary'(min_degree=1,max_degree=1) + 'MMA_SHA_2F-Secondary'(min_degree=1,max_degree=1)"],
    ...
  )

In this case, model evaluations will then be available in the returned data under the name "Combined_model", but you can name it however you like.

NB: When using model names containing a hyphen (``-``) then extra single (``'``) or double (``"``) quotes must be used around the model name. This is to distinguish from arithmetic minus (``-``).

----

``auxiliaries``
---------------

::

  SyncStatus, Kp10, Kp, Dst, IMF_BY_GSM, IMF_BZ_GSM, IMF_V, F107, F10_INDEX,
  OrbitDirection, QDOrbitDirection,
  OrbitSource, OrbitNumber, AscendingNodeTime,
  AscendingNodeLongitude, QDLat, QDLon, QDBasis, MLT, SunDeclination,
  SunHourAngle, SunRightAscension, SunAzimuthAngle, SunZenithAngle,
  SunLongitude, SunVector, DipoleAxisVector, NGPLatitude, NGPLongitude,
  DipoleTiltAngle


.. note::

  - ``Kp`` provides the Kp values in fractional form (e.g 2.2), and ``Kp10`` is multiplied by 10 (as integers)
  - ``F107`` is the hourly 10.7 cm solar radio flux value, and ``F10_INDEX`` is the daily average
  - ``QDLat`` and ``QDLon`` are quasi-dipole coordinates
  - ``MLT`` is calculated from the QDLon and the subsolar position
  - ``OrbitDirection`` and ``QDOrbitDirection`` flags indicate if the satellite is moving towards or away from each pole, respectively for geographic and quasi-dipole magnetic poles. +1 for ascending, and -1 for descending (in latitude); 0 for no data.

----

.. note::

  Check other packages such `hapiclient`_ and others from `PyHC`_ for data from other sources.
  
.. _`hapiclient`: https://github.com/hapi-server/client-python

.. _`PyHC`: http://heliopython.org/projects/


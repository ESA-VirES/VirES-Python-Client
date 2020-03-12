Available parameters for Swarm data
===================================

| `See also: Jupyter notebook about data and model availability <https://swarm-vre.readthedocs.io/en/latest/Swarm_notebooks/02b__viresclient-Available-Data.html>`_

You can check which parameters are available with:

.. code-block:: python

  from viresclient import SwarmRequest
  req = SwarmRequest()
  req.available_collections()
  req.available_measurements("MAG")
  req.available_models()
  req.available_auxiliaries()

The available measurements are segregated according to the "collection" (essentially Swarm products): each ``collection`` has a number of ``measurements`` associated with it, and the appropriate collection must be set in order to access the measurements. ``auxiliaries`` are available together with any set ``collection``. ``models`` provide magnetic model evaluation on demand, at the locations of the time series which is being accessed.

See the `Swarm Data Handbook`_ for details about the products.

.. _`Swarm Data Handbook`: https://earth.esa.int/web/guest/missions/esa-eo-missions/swarm/data-handbook/

----

``collections``
---------------

(replace x with A, B, or C for Alpha, Bravo, or Charlie)::

  SW_OPER_MAGx_LR_1B
  SW_OPER_MAGx_HR_1B
  SW_OPER_EFIx_LP_1B
  SW_OPER_IBIxTMS_2F
  SW_OPER_TECxTMS_2F
  SW_OPER_FACxTMS_2F
  SW_OPER_EEFxTMS_2F
  SW_OPER_IPDxIRR_2F

For Alpha-Charlie FAC: ``collection="SW_OPER_FAC_TMS_2F"``.

The ``measurements``, ``models``, and ``auxiliaries`` chosen will match the cadence of the ``collection`` chosen.

----

``measurements``
----------------

Choose combinations of measurements from one of the following sets, corresponding to the collection chosen above.

For MAG and ``MAG_HR``::

  F,dF_AOCS,dF_other,F_error,B_VFM,B_NEC,dB_Sun,dB_AOCS,dB_other,B_error,q_NEC_CRF,Att_error,Flags_F,Flags_B,Flags_q,Flags_Platform,ASM_Freq_Dev

For EFI::

  U_orbit,Ne,Ne_error,Te,Te_error,Vs,Vs_error,Flags_LP,Flags_Ne,Flags_Te,Flags_Vs

For IBI::

  Bubble_Index,Bubble_Probability,Flags_Bubble,Flags_F,Flags_B,Flags_q

For TEC::

  GPS_Position,LEO_Position,PRN,L1,L2,P1,P2,S1,S2,Elevation_Angle,Absolute_VTEC,Absolute_STEC,Relative_STEC,Relative_STEC_RMS,DCB,DCB_Error

For FAC::

  IRC,IRC_Error,FAC,FAC_Error,Flags,Flags_F,Flags_B,Flags_q

For EEF::

  EEF,RelErr,flags

For IPD::

  Ne,Te,Background_Ne,Foreground_Ne,PCP_flag,Grad_Ne_at_100km,Grad_Ne_at_50km,Grad_Ne_at_20km,Grad_Ne_at_PCP_edge,ROD,RODI10s,RODI20s,delta_Ne10s,delta_Ne20s,delta_Ne40s,Num_GPS_satellites,mVTEC,mROT,mROTI10s,mROTI20s,IBI_flag,Ionosphere_region_flag,IPIR_index,Ne_quality_flag,TEC_STD

----

``models``
----------

Models are evaluated along the satellite track at the positions of the time series that has been requested. These must be used together with one of the MAG collections, and one or both of the "F" and "B_NEC" measurements. This can yield either the model values together with the measurements, or the data-model residuals. `(More info about models) <https://magneticearth.org/pages/models.html>`_

.. note::

  For a good estimate of the ionospheric field measured by a Swarm satellite (with the core, crust and magnetosphere effects removed) use a composed model defined as:  
  ``models=['CHAOS-full' = 'CHAOS-Core' + 'CHAOS-Static' + 'CHAOS-MMA-Primary' + 'CHAOS-MMA-Secondary'"]``
  `(click for more info) <https://github.com/klaundal/notebooks/blob/master/get_external_field.ipynb>`_

::

  IGRF,

  # Comprehensive inversion (CI) models:
  MCO_SHA_2C,                                # Core
  MLI_SHA_2C,                                # Lithosphere
  MMA_SHA_2C-Primary, MMA_SHA_2C-Secondary,  # Magnetosphere
  MIO_SHA_2C-Primary, MIO_SHA_2C-Secondary,  # Ionosphere

  # Dedicated inversion models:
  MCO_SHA_2D,
  MLI_SHA_2D,
  MIO_SHA_2D-Primary, MIO_SHA_2D-Secondary
  AMPS

  # Fast-track models:
  MMA_SHA_2F-Primary, MMA_SHA_2F-Secondary,

  # CHAOS models:
  CHAOS-Core,
  CHAOS-Static,
  CHAOS-MMA-Primary, CHAOS-MMA-Secondary

  # Other lithospheric models:
  MF7, LCS-1

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

  - The AMPS model is currently accessible as "auxiliaries" instead of a "model" (On the DISC server it is now accessible as a regular model)
  - ``Kp`` provides the Kp values in fractional form (e.g 2.2), and ``Kp10`` is multiplied by 10 (as integers)
  - ``F107`` is the hourly 10.7 cm solar radio flux value, and ``F10_INDEX`` is the daily average
  - ``QDLat`` and ``QDLon`` are quasi-dipole coordinates
  - ``OrbitDirection`` and ``QDOrbitDirection`` flags indicate if the satellite is moving towards or away from each pole, respectively for geographic and quasi-dipole magnetic poles. +1 for ascending, and -1 for descending (in latitude); 0 for no data.

----

Standard positional variables always returned::

  Timestamp,Latitude,Longitude,Radius,Spacecraft

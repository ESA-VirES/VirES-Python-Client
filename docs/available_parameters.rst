.. _Swarm parameters:

Available parameters for Swarm
==============================

.. tip::

  Did you know? The *VirES for Swarm* service provides data not only from Swarm but also INTERMAGNET ground observatories (search below for ``AUX_OBS``), and recalibrated platform magnetometer data from selected LEO missions (search below for ``MAG_``).

.. note::

  | `See also: Jupyter notebook about data and model availability <https://notebooks.vires.services/notebooks/02b__viresclient-available-data>`_ - check out the other demo notebooks there too.

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

.. _`Swarm Data Handbook`: https://earth.esa.int/eogateway/missions/swarm/product-data-handbook

.. _`Swarm Product Demos`: https://notebooks.vires.services/notebooks/03a1_demo-magx_lr_1b

----

``collections``
---------------

.. note::

  ``FAST`` data are available for some products. These are processed and made available faster than the traditional operational (``OPER``) data, mainly for space weather monitoring. The collection names are the same, but with ``OPER`` replaced by ``FAST``:

  - ``SW_FAST_MAGx_LR_1B``
  - ``SW_FAST_MAGx_HR_1B``
  - ``SW_FAST_EFIx_LP_1B``
  - ``SW_FAST_MODx_SC_1B``
  - ``SW_FAST_FACxTMS_2F``
  - ``SW_FAST_TECxTMS_2F``

Collections are grouped according to a type containing similar measurements (i.e. the same product from different spacecraft). The collection type can be given to :py:meth:`viresclient.SwarmRequest.available_collections` to retrieve the full collection names. These cover the Swarm data products as below (replace x with A, B, or C for Alpha, Bravo, or Charlie):

======================== ================ ==============================================================
Collection full name     Collection type  Description
======================== ================ ==============================================================
SW_OPER_MAGx_LR_1B       MAG              Magnetic field (1Hz) from VFM and ASM
SW_OPER_MAGx_HR_1B       MAG_HR           Magnetic field (50Hz) from VFM
SW_OPER_EFIx_LP_1B       EFI              Electric field instrument (Langmuir probe measurements at 2Hz)
SW_OPER_EFIxTIE_2\_       EFI_TIE          Estimates of the ion temperatures
SW_EXPT_EFIx_TCT02       EFI_TCT02        2Hz cross-track ion flows
SW_EXPT_EFIx_TCT16       EFI_TCT16        16Hz cross-track ion flows
SW_PREL_EFIxIDM_2\_      EFI_IDM          2Hz ion drift velocities and effective masses (SLIDEM project)
SW_OPER_IPDxIRR_2F       IPD              Ionospheric plasma characteristics (derived quantities at 1Hz)
SW_OPER_TECxTMS_2F       TEC              Total electron content
SW_OPER_FACxTMS_2F       FAC              Field-aligned currents (single satellite)
SW_OPER_FAC_TMS_2F       FAC              Field-aligned currents (dual-satellite A-C)
SW_OPER_EEFxTMS_2F       EEF              Equatorial electric field
SW_OPER_IBIxTMS_2F       IBI              Ionospheric bubble index
SW_OPER_MODx_SC_1B       MOD_SC           Spacecraft positions at 1Hz
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

The PRISM (Plasmapause Related boundaries in the topside Ionosphere as derived from Swarm Measurements) products are provided as:

====================== ================ ===================================================================================================
Collection full name   Collection type  Description
====================== ================ ===================================================================================================
SW_OPER_MITx_LP_2F     MIT_LP           Minima of the Midlatitude Ionospheric Trough (MIT) - derived from Langmuir Probe (LP) measurements
SW_OPER_MITx_LP_2F:ID  MIT_LP:ID        -> Boundaries of the MIT - derived from the LP
SW_OPER_MITxTEC_2F     MIT_TEC          Minima of the MIT - derived from Total Electron Content (TEC)
SW_OPER_MITxTEC_2F:ID  MIT_TEC:ID       -> Boundaries of the MIT - derived from TEC
SW_OPER_PPIxFAC_2F     PPI_FAC          Midnight Plasmapause Index (PPI)
SW_OPER_PPIxFAC_2F:ID  PPI_FAC:ID       -> Boundaries of the Small-Scale Field Aligned Currents (SSFAC)
====================== ================ ===================================================================================================

`TOLEOS (Thermosphere Observations from Low-Earth Orbiting Satellites) <https://earth.esa.int/eogateway/activities/toleos>`_ products are provided as follows.

============================== ================ ===================================================================================================
Collection full name           Collection type  Description
============================== ================ ===================================================================================================
CH_OPER_DNS_ACC_2\_            DNS_ACC_CHAMP    Thermosphere mass density (CHAMP)
GR_OPER_DNSxACC_2\_            DNS_ACC_GRACE    Thermosphere mass density (GRACE)
GF_OPER_DNSxACC_2\_            DNS_ACC_GFO      Thermosphere mass density (GRACE-FO)
CH_OPER_WND_ACC_2\_            WND_ACC_CHAMP    Thermosphere crosswind (CHAMP)
GR_OPER_WNDxACC_2\_            WND_ACC_GRACE    Thermosphere crosswind (GRACE)
GF_OPER_WNDxACC_2\_            WND_ACC_GFO      Thermosphere crosswind (GRACE-FO)
MM_CON_SPH_2\_:crossover                        Conjunction information (times when ground-tracks intersect)
MM_CON_SPH_2\_:plane_alignment                  Conjunction information (times when orbital planes align)
============================== ================ ===================================================================================================

The AUX_OBS collections contain ground magnetic observatory data from `INTERMAGNET <https://intermagnet.github.io/data_conditions.html>`_ and `WDC <http://www.wdc.bgs.ac.uk/>`_. Please note that these data are provided under different usage terms than the ESA data, and must be acknowledged accordingly.

======================== ================ ==============================================================
Collection full name     Collection type  Description
======================== ================ ==============================================================
SW_OPER_AUX_OBSH2\_       AUX_OBSH         Hourly values derived from both WDC and INTERMAGNET data
SW_OPER_AUX_OBSM2\_       AUX_OBSM         Minute values from INTERMAGNET
SW_OPER_AUX_OBSS2\_       AUX_OBSS         Second values from INTERMAGNET
======================== ================ ==============================================================

The AUX_OBS collections contain data from all observatories together (distinguishable by the ``IAGA_code`` variable). Data from a single observatory can be accessed with special collection names like ``SW_OPER_AUX_OBSM2_:ABK`` where ``ABK`` can be replaced with the IAGA code of the observatory. Use :py:meth:`viresclient.SwarmRequest.available_observatories` to find these IAGA codes.

The VOBS collections contain derived magnetic measurements from `Geomagnetic Virtual Observatories <https://earth.esa.int/eogateway/activities/gvo>`_ and have a similar interface as the AUX_OBS collections. The data are organised across several collections:

==================================== =========================== ==========================================================================
Collection full name                 Collection type             Description
==================================== =========================== ==========================================================================
SW_OPER_VOBS_1M_2\_                  VOBS_SW_1M                  Swarm (1-monthly cadence)
OR_OPER_VOBS_1M_2\_                  VOBS_OR_1M                  Ørsted (1-monthly cadence)
CH_OPER_VOBS_1M_2\_                  VOBS_CH_1M                  CHAMP (1-monthly)
CR_OPER_VOBS_1M_2\_                  VOBS_CR_1M                  Cryosat-2 (1-monthly)
CO_OPER_VOBS_1M_2\_                  VOBS_CO_1M                  Composite time series from Ørsted, CHAMP, Cryosat-2, & Swarm (1-monthly)
SW_OPER_VOBS_4M_2\_                  VOBS_SW_4M                  Swarm (4-monthly)
OR_OPER_VOBS_4M_2\_                  VOBS_OR_4M                  Ørsted (4-monthly)
CH_OPER_VOBS_4M_2\_                  VOBS_CH_4M                  CHAMP (4-monthly)
CR_OPER_VOBS_4M_2\_                  VOBS_CR_4M                  Cryosat-2 (4-monthly)
CO_OPER_VOBS_4M_2\_                  VOBS_CO_4M                  Composite time series from Ørsted, CHAMP, Cryosat-2, & Swarm (4-monthly)
SW_OPER_VOBS_1M_2\_:SecularVariation VOBS_SW_1M:SecularVariation Secular variation (``B_SV``) from Swarm 1-monthly
(ditto for the others)
==================================== =========================== ==========================================================================

Each VOBS product (e.g. Swarm 1-monthly) is split into two collections (e.g. ``SW_OPER_VOBS_1M_2_`` (containing ``B_OB`` & ``B_CF``) and ``SW_OPER_VOBS_1M_2_:SecularVariation`` (containing ``B_SV``)) because of the different temporal sampling points (i.e. differing ``Timestamp``) of these measurements. Data can also be requested for a specific virtual observatory alone (distinguishable by the ``SiteCode`` variable) with special collection names like ``SW_OPER_VOBS_1M_2_:N65W051`` and ``SW_OPER_VOBS_1M_2_:SecularVariation:N65W051``.

`CHAMP magnetic products <https://doi.org/10.5880/GFZ.2.3.2019.004>`_ are available:

=============================== ================ ===================================================================================================================================
Collection full name            Collection type  Available measurement names
=============================== ================ ===================================================================================================================================
CH_ME_MAG_LR_3                  MAG_CHAMP        ``F,B_VFM,B_NEC,Flags_Position,Flags_B,Flags_q,Mode_q,q_ICRF_CRF``
=============================== ================ ===================================================================================================================================

Calibrated magnetic data are also available from external missions: Cryosat-2, GRACE (A+B), GRACE-FO (1+2), GOCE:

=============================== ================ ===================================================================================================================================
Collection full name            Collection type  Available measurement names
=============================== ================ ===================================================================================================================================
CS_OPER_MAG                     MAG_CS           ``F,B_NEC,B_mod_NEC,B_NEC1,B_NEC2,B_NEC3,B_FGM1,B_FGM2,B_FGM3,q_NEC_CRF,q_error``
GRACE_x_MAG (x=A/B)             MAG_GRACE        ``F,B_NEC,B_NEC_raw,B_FGM,B_mod_NEC,q_NEC_CRF,q_error``
GFx_OPER_FGM_ACAL_CORR (x=1/2)  MAG_GFO          ``F,B_NEC,B_FGM,dB_MTQ_FGM,dB_XI_FGM,dB_NY_FGM,dB_BT_FGM,dB_ST_FGM,dB_SA_FGM,dB_BAT_FGM,q_NEC_FGM,B_FLAG``
GFx_MAG_ACAL_CORR_ML (x=1/2)    MAG_GFO_ML       ``F,B_MAG,B_NEC,q_NEC_FGM,B_FLAG,KP_DST_FLAG,Latitude_QD,Longitude_QD``
GO_MAG_ACAL_CORR                MAG_GOCE         ``F,B_MAG,B_NEC,dB_MTQ_SC,dB_XI_SC,dB_NY_SC,dB_BT_SC,dB_ST_SC,dB_SA_SC,dB_BAT_SC,dB_HK_SC,dB_BLOCK_CORR,q_SC_NEC,q_MAG_SC,B_FLAG``
GO_MAG_ACAL_CORR_ML             MAG_GOCE_ML      ``F,B_MAG,B_NEC,q_FGM_NEC,B_FLAG,MAGNETIC_ACTIVITY_FLAG,NaN_FLAG,Latitude_QD,Longitude_QD``
=============================== ================ ===================================================================================================================================

The ``measurements``, ``models``, and ``auxiliaries`` chosen will match the cadence of the ``collection`` chosen.

----

``measurements``
----------------

Choose combinations of measurements from one of the following sets, corresponding to the collection chosen above. The collection full name or collection type can be given to :py:meth:`viresclient.SwarmRequest.available_measurements` to retrieve the list of available measurements for a given collection (e.g. ``request.available_measurements("SW_OPER_MAGA_LR_1B")``)

=============== ==============================================================================================================================================================================================================================================================================================
Collection type Available measurement names
=============== ==============================================================================================================================================================================================================================================================================================
MAG             ``F,dF_Sun,dF_AOCS,dF_other,F_error,B_VFM,B_NEC,dB_Sun,dB_AOCS,dB_other,B_error,q_NEC_CRF,Att_error,Flags_F,Flags_B,Flags_q,Flags_Platform,ASM_Freq_Dev``
MAG_HR          ``F,B_VFM,B_NEC,dB_Sun,dB_AOCS,dB_other,B_error,q_NEC_CRF,Att_error,Flags_B,Flags_q,Flags_Platform,ASM_Freq_Dev``
EFI             ``U_orbit,Ne,Ne_error,Te,Te_error,Vs,Vs_error,Flags_LP,Flags_Ne,Flags_Te,Flags_Vs``
EFI_TIE         ``Latitude_GD,Longitude_GD,Height_GD,Radius_GC,Latitude_QD,MLT_QD,Tn_msis,Te_adj_LP,Ti_meas_drift,Ti_model_drift,Flag_ti_meas,Flag_ti_model``
EFI_TCTyy       ``VsatC,VsatE,VsatN,Bx,By,Bz,Ehx,Ehy,Ehz,Evx,Evy,Evz,Vicrx,Vicry,Vicrz,Vixv,Vixh,Viy,Viz,Vixv_error,Vixh_error,Viy_error,Viz_error,Latitude_QD,MLT_QD,Calibration_flags,Quality_flags``
EFI_IDM         ``Latitude_GD,Longitude_GD,Height_GD,Radius_GC,Latitude_QD,MLT_QD,V_sat_nec,M_i_eff,M_i_eff_err,M_i_eff_Flags,M_i_eff_tbt_model,V_i,V_i_err,V_i_Flags,V_i_raw,N_i,N_i_err,N_i_Flags,A_fp,R_p,T_e,Phi_sc``
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

PRISM products:

================ ================================================================================================================
Collection type  Available measurement names
================ ================================================================================================================
MIT_LP           ``Counter,Latitude_QD,Longitude_QD,MLT_QD,L_value,SZA,Ne,Te,Depth,DR,Width,dL,PW_Gradient,EW_Gradient,Quality``
MIT_LP:ID        ``Counter,Latitude_QD,Longitude_QD,MLT_QD,L_value,SZA,Ne,Te,Position_Quality,PointType``
MIT_TEC          ``Counter,Latitude_QD,Longitude_QD,MLT_QD,L_value,SZA,TEC,Depth,DR,Width,dL,PW_Gradient,EW_Gradient,Quality``
MIT_TEC:ID       ``Counter,Latitude_QD,Longitude_QD,MLT_QD,L_value,SZA,TEC,Position_Quality,PointType``
PPI_FAC          ``Counter,Latitude_QD,Longitude_QD,MLT_QD,L_value,SZA,Sigma,PPI,dL,Quality``
PPI_FAC:ID       ``Counter,Latitude_QD,Longitude_QD,MLT_QD,L_value,SZA,Position_Quality,PointType``
================ ================================================================================================================

AUX_OBS products:

=============== =========================================
Collection type Available measurement names
=============== =========================================
AUX_OBSH        ``B_NEC,F,IAGA_code,Quality,ObsIndex``
AUX_OBSM        ``B_NEC,F,IAGA_code,Quality``
AUX_OBSS        ``B_NEC,F,IAGA_code,Quality``
=============== =========================================

AUX_OBSH contains a special variable, ``ObsIndex``, which is set to 0, 1, 2 ... to indicate changes to the observatory where the IAGA code has remained the same (e.g. small change of location, change of instrument or calibration procedure).

VOBS products:

==================================== ===========================================
Collection full name                 Available measurement names
==================================== ===========================================
SW_OPER_VOBS_1M_2\_                  ``SiteCode,B_CF,B_OB,sigma_CF,sigma_OB``
SW_OPER_VOBS_1M_2\_:SecularVariation ``SiteCode,B_SV,sigma_SV``
(ditto for the others)
==================================== ===========================================


----

.. _Swarm models:

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

  SyncStatus, Kp10, Kp, Dst, dDst, IMF_BY_GSM, IMF_BZ_GSM, IMF_V, F107, F10_INDEX,
  OrbitDirection, QDOrbitDirection,
  OrbitSource, OrbitNumber, AscendingNodeTime,
  AscendingNodeLongitude, QDLat, QDLon, QDBasis, MLT, SunDeclination,
  SunHourAngle, SunRightAscension, SunAzimuthAngle, SunZenithAngle,
  SunLongitude, SunVector, DipoleAxisVector, NGPLatitude, NGPLongitude,
  DipoleTiltAngle, F107_avg81d, F107_avg81d_count


.. note::

  - ``Kp`` provides the Kp values in fractional form (e.g 2.2), and ``Kp10`` is multiplied by 10 (as integers)
  - ``F107`` is the hourly 10.7 cm solar radio flux value, and ``F10_INDEX`` is the daily average
  - ``QDLat`` and ``QDLon`` are quasi-dipole coordinates
  - ``MLT`` is calculated from the QDLon and the subsolar position
  - ``OrbitDirection`` and ``QDOrbitDirection`` flags indicate if the satellite is moving towards or away from each pole, respectively for geographic and quasi-dipole magnetic poles. +1 for ascending, and -1 for descending (in latitude); 0 for no data.

----

.. note::

  Check other packages such as `hapiclient`_ and others from `PyHC`_ for data from other sources.

.. _`hapiclient`: https://github.com/hapi-server/client-python

.. _`PyHC`: http://heliopython.org/projects/

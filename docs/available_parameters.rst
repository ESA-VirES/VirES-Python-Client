Available parameters for Swarm data
===================================

You can check which parameters are available with:

.. code-block:: python

  from viresclient import SwarmRequest
  req = SwarmRequest()
  req.available_collections()
  req.available_measurements("MAG")
  req.available_models()
  req.available_auxiliaries()

----

``collections``
---------------

(replace x with A, B, or C for Alpha, Bravo, or Charlie)::

  SW_OPER_MAGx_LR_1B
  SW_OPER_EFIx_LP_1B
  SW_OPER_IBIxTMS_2F
  SW_OPER_TECxTMS_2F
  SW_OPER_FACxTMS_2F
  SW_OPER_EEFxTMS_2F

For Alpha-Charlie FAC: ``collection="SW_OPER_FAC_TMS_2F"``.

The ``measurements``, ``models``, and ``auxiliaries`` chosen will match the cadence of the ``collection`` chosen.

----

``measurements``
----------------

Choose combinations of measurements from one of the following sets, corresponding to the collection chosen above.

For MAG::

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

----

``models``
----------

Models are evaluated along the satellite track at the positions of the measurements.

::

  IGRF12, SIFM, CHAOS-6-Combined, CHAOS-6-Core, CHAOS-6-Static,
  MCO_SHA_2C, MCO_SHA_2D, MCO_SHA_2F, MLI_SHA_2C, MLI_SHA_2D,
  MMA_SHA_2C-Primary, MMA_SHA_2C-Secondary,
  MMA_SHA_2F-Primary, MMA_SHA_2F-Secondary,
  MIO_SHA_2C-Primary, MIO_SHA_2C-Secondary,
  MIO_SHA_2D-Primary, MIO_SHA_2D-Secondary

(``residuals`` available when combined with MAG ``measurements`` ``F`` and/or ``B_NEC``)

----

``auxiliaries``
---------------

::

  SyncStatus, Kp, Dst, IMF_BY_GSM, IMF_BZ_GSM, IMF_V, F10_INDEX,
  OrbitSource, OrbitNumber, AscendingNodeTime,
  AscendingNodeLongitude, QDLat, QDLon, QDBasis, MLT, SunDeclination,
  SunHourAngle, SunRightAscension, SunAzimuthAngle, SunZenithAngle,
  SunLongitude, SunVector, DipoleAxisVector, NGPLatitude, NGPLongitude,
  DipoleTiltAngle,

  UpwardCurrent, TotalCurrent,
  DivergenceFreeCurrentFunction, F_AMPS, B_NEC_AMPS

NB: the AMPS model is currently accessible as "auxiliaries" instead of a "model".

----

Standard positional variables always returned::

  Timestamp,Latitude,Longitude,Radius,Spacecraft

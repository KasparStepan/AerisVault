$# LS-DYNA Keyword file created by LS-PrePost(R) 2025 R2 (v4.13.2) - 10Jun2025
$# Created on May-20-2026 (14:24:11)
*KEYWORD
*DEFINE_CURVE_TITLE
Velocity
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
       902         0       1.0       1.0       0.0       0.0         0         0
$#                a1                  o1
                 0.0                20.0
    9.9999994421e+27                20.0
*DAMPING_PART_MASS
$#     pid      lcid        sf      flag     struc
         1         0       0.1         0         0
*INCLUDE
00_CFD_mesh_canopy.k
00_CFD_mesh_domain.k
*ICFD_BOUNDARY_FREESLIP
$#     pid
  40000001
*ICFD_BOUNDARY_FSI
$#     pid
  10000001
*ICFD_BOUNDARY_PRESCRIBED_PRE
$#     pid      lcid        sf     death     birth       iso
  30000001       902       1.01.00000E28       0.0         0
*ICFD_BOUNDARY_PRESCRIBED_VEL
$#     pid       dof       vad      lcid        sf       vid     death     birth
  20000001         3         1       902       1.0         01.00000E28       0.0
*ICFD_CONTROL_ADAPT
$#    minh      maxh       err       mth       nit       var         -       kis
       0.0       0.5       2.5         1         0         0                   1
*ICFD_CONTROL_GENERAL
$#   atype     mtype      dvcl     rdvcl     solcl         -       idr
         0         0         0         0         0                   0
*ICFD_CONTROL_MESH
$#    mgsf         -    mstrat   2dstruc     nrmsh
       1.1                   0         0         0
$#    aver      sfbl
        16       1.0
*ICFD_CONTROL_OUTPUT
$#    msgl      outl     dtout   lsppout         -     itout
         4         0     0.003         0                   0
*ICFD_CONTROL_TIME
$#     ttm        dt       cfl    lcidsf     dtmin     dtmax    dtinit    tdeath
       1.07.50000E-4       0.0         01.00000E-91.00000E28       0.01.00000E28
*ICFD_CONTROL_TRANSIENT
$#    tord     fsord
         0         0
*ICFD_CONTROL_TURBULENCE
$#    tmod    submod      wlaw        ks        cs         -     twlaw    typlus
         4         3         1       0.0       0.0                   0       0.0
$#   gamma    beta01   sigmaw1   sigmak1   beta0st      ccut
      1.44     0.072       2.0       2.0      0.09      -1.0
$#      a1    beta02   sigmaw2   sigmak2        cl
      0.31    0.0828       2.0       2.0     0.875
*ICFD_CONTROL_FSI
$#     owc        bt        dt       idc    lcidsf     xproj
         0       0.01.00000E28       1.0         0         0
$#    nsub         -         -    idetec     vforc
         0                             0         0
*ICFD_DATABASE_DRAG
$#     pid      cpid     dtout    perout      divi     elout     ssout
  10000001         0     0.001         0        10         0         0
*ICFD_DATABASE_RESIDUALS
$#    rlvl
         3
*ICFD_MAT_TITLE
ICFD_Air
$#     mid       flg        ro       vis        st  stsflcid        ca
    900001         1     1.2251.80300E-5       0.0         0       0.0
*ICFD_MAT_TITLE
ICFD_Air_Porous
$#     mid       flg        ro       vis        st  stsflcid        ca
    900002         1     1.2251.80300E-5       0.0         0       0.0
$#      hc        tc      beta       prt  hcsflcid  tcsflcid
       0.0       0.0       0.0      0.85         0         0
$#  nnmoid    pmmoid         -    sptrid         -       vid
         0      9001                   0                   0
*ICFD_PART_TITLE
Canopy
$#     pid     secid       mid
  10000001   9000001    900001
*ICFD_PART_TITLE
ICFD_Inlet
$#     pid     secid       mid
  20000001   9000001    900001
*ICFD_PART_TITLE
ICFD_Outlet
$#     pid     secid       mid
  30000001   9000001    900001
*ICFD_PART_TITLE
ICFD_Walls
$#     pid     secid       mid
  40000001   9000001    900001
*ICFD_PART_VOL_TITLE
ICFD_Domain
$#     pid     secid       mid
         1   9000001    900001
$#   spid1     spid2     spid3     spid4     spid5     spid6     spid7     spid8
  20000001  30000001  40000001         0         0         0         0         0
*ICFD_SECTION
$#     sid
   9000001
*ICFD_MODEL_POROUS
$#  pmmoid   pmmtype      form     rhocp     kappa
      9001         2         0       0.0       0.0
$#     por       per        ff         -   psflcid         -         -
     0.0454.2684E-12  1.056553                   0                    
*MESH_BL
$#     pid     nelth      blth      blfe      blst      bldr
  10000001         0       0.0       0.0         0         0
*MESH_EMBEDSHELL
$#   volid
         1
$#    pid1      pid2      pid3      pid4      pid5      pid6      pid7      pid8
  10000001         0         0         0         0         0         0         0
*MESH_VOLUME
$#   volid
         1
$#    pid1      pid2      pid3      pid4      pid5      pid6      pid7      pid8
  20000001  30000001  40000001         0         0         0         0         0
*END

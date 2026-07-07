$# LS-DYNA Keyword file created by LS-PrePost(R) 2025 R2 (v4.13.2) - 10Jun2025
$# Created on May-20-2026 (14:24:11)
*KEYWORD
*CONTROL_IMPLICIT_DYNAMICS
$#   imass     gamma      beta    tdybir    tdydth    tdybur     irate     alpha
         1       0.6      0.36       0.01.00000E281.00000E28         0     -0.05
*CONTROL_IMPLICIT_GENERAL
$#  imflag       dt0    imform      nsbs       igs     cnstn      form    zero_v
         17.50000E-4         2         1         2         0         0         0
*CONTROL_IMPLICIT_SOLUTION
$#  nsolvr    ilimit    maxref     dctol     ectol     rctol     lstol    abstol
        12        11        50      0.02     0.0051.00000E10       0.91.0000E-10
$#   dnorm    diverg     istif   nlprint    nlnorm   d3itctl     cpchk
         1         1         1         0         2         0         0
$#  arcctl    arcdir    arclen    arcmth    arcdmp    arcpsi    arcalf    arctim
         0         0       0.0         1         2       0.0       0.0       0.0
$#   lsmtd     lsdir      irad      srad      awgt      sred    kssize
         4         2       0.0       0.0       0.0       0.0        10
*CONTROL_SHELL
$#  wrpang     esort     irnxx    istupd    theory       bwc     miter      proj
      20.0         0        -1         0         2         2         1         0
*CONTROL_TERMINATION
$#  endtim    endcyc     dtmin    endeng    endmas     nosol
       1.0         0       0.0       0.01.000000E8         0
*DATABASE_NODOUT
$#      dt    binary      lcur     ioopt   option1   option2
5.00000E-4         3         0         3       0.0         0
*DATABASE_HISTORY_NODE_SET
$#     id1       id2       id3       id4       id5       id6       id7       id8
      1001         0         0         0         0         0         0         0
*SET_PART_LIST_TITLE
Suspension_lines
$#     sid       da1       da2       da3       da4    solver
      2002       0.0       0.0       0.0       0.0MECH
$#    pid1      pid2      pid3      pid4      pid5      pid6      pid7      pid8
         4         0         0         0         0         0         0         0
*CONTACT_AUTOMATIC_SINGLE_SURFACE
$#     cid                                                                 title
$#   surfa     surfb  surfatyp  surfbtyp   saboxid   sbboxid      sapr      sbpr
      2001         0         2         0         0         0         0         2
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.0       0.0       0.0       0.0       0.0         0       0.01.00000E20
$#    sfsa      sfsb      sast      sbst     sfsat     sfsbt       fsf       vsf
       1.0       1.0     0.008       0.0       1.0       1.0       1.0       1.0
$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         2       0.1         0     1.025         0         2         0         1
$#  penmax    thkopt    shlthk     snlog      isym     i2d3d    sldthk    sldstf
       0.0         0         0         1         0         0       0.0       0.0
$#    igap    ignore    dprfac    dtstif     edgek         -    flangl   cid_rcf
         2         0       0.0       0.0       0.0                 0.0         0
*HOURGLASS_TITLE
Hourglass
$#    hgid       ihq        qm       ibq        q1        q2    qb/vdc        qw
         1         8       0.1         0       1.5      0.06       0.1       0.1
*MAT_FABRIC_TITLE
Fabric
$#     mid        ro        ea        eb         -      prba      prab         -
     10011     656.76.050000E8       0.0                 0.3       0.0          
$#     gab         -         -       cse        el       prl    lratio      damp
       0.0                           1.0       0.0       0.0       0.0      0.05
$#    aopt    flc/x2    fac/x3       ela      lnrc      form     fvopt    tsrfac
       0.0       0.0       0.0       0.0       0.0        12         0       0.0
$#       -    rgbrth     a0ref        a1        a2        a3        x0        x1
                 0.0         0       0.0       0.0       0.0       0.0       0.0
$#      v1        v2        v3         -         -         -      beta    isrefg
       0.0       0.0       0.0                                     0.0         0
*MAT_CABLE_DISCRETE_BEAM_TITLE
Suspension_Rope
$#     mid        ro         e      lcid        f0    tmaxf0     tramp     iread
     10021     820.62.700000E9         0       0.0       0.0       0.0         0
*DEFINE_CURVE_TITLE
Gravity
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
         1         0       1.0      -1.0       0.0       0.0         0         0
$#                a1                  o1
                 0.0             39.2266
               100.0             39.2266
*SECTION_SHELL_TITLE
Shell_Fabric
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
     20001        16       1.0         4         1         0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
6.00000E-56.00000E-56.00000E-56.00000E-5       0.0       0.0       0.0         0
*SECTION_SHELL_TITLE
Skirt_Reinforcement
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
     20005        16       1.0         4         1         0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
7.00000E-47.00000E-47.00000E-47.00000E-4       0.0       0.0       0.0         0
*SECTION_SHELL_TITLE
Gore_reinforcement
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
     20006        16       1.0         4         1         0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
2.40000E-42.40000E-42.40000E-42.40000E-4       0.0       0.0       0.0         0
*SECTION_BEAM_TITLE
Beam_Suspension_rope_SCRAB
$#   secid    elform      shrf   qr/irid       cst     scoor       nsm     naupd
     20004         6      0.83         2         0       0.0       0.0         0
$#     vol      iner       cid  ca/dofoffset/dofn2rrcon/nullsrcon/nulltrcon/null
       0.0       0.0         07.06500E-6       0.0       0.0       0.0       0.0
*INCLUDE
00_CSD_mesh.k
*SECTION_BEAM_TITLE
Beam_Riser_SCRAB
$#   secid    elform      shrf   qr/irid       cst     scoor       nsm     naupd
     20002         6      0.83         2         0       0.0       0.0         0
$#     vol      iner       cid  ca/dofoffset/dofn2rrcon/nullsrcon/nulltrcon/null
       0.0       0.0         01.00000E-4       0.0       0.0       0.0       0.0
*SECTION_BEAM_TITLE
Beam_Suspension_rope_SCRAB
$#   secid    elform      shrf   qr/irid       cst     scoor       nsm     naupd
     20003         6      0.83         2         0       0.0       0.0         0
$#     vol      iner       cid  ca/dofoffset/dofn2rrcon/nullsrcon/nulltrcon/null
       0.0       0.0         01.40000E-5       0.0       0.0       0.0       0.0
*END

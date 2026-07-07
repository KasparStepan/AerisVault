$# LS-DYNA Keyword file created by LS-PrePost(R) 2025 R2 (v4.13.2) - 10Jun2025
$# Created on May-20-2026 (14:24:11)
*KEYWORD
*TITLE
$#                                                                         title
LS-DYNA keyword deck by LS-PrePost
*DATABASE_BINARY_D3PLOT
$#      dt      lcdt      beam     npltc    psetid
5.00000E-4         0         0         0         0
*BOUNDARY_SPC_SET
$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
      1001         0         1         1         1         0         0         0
*BOUNDARY_SPC_SET_BIRTH_DEATH
$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
      1002         0         1         1         1         0         0         0
$#   birth     death
       0.0       0.1
*CONTACT_AUTOMATIC_GENERAL_ID
$#     cid                                                                 title
         0Canopy2Lines
$#   surfa     surfb  surfatyp  surfbtyp   saboxid   sbboxid      sapr      sbpr
      2002      2001         2         2         0         0         0         0
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.0       0.0       0.0       0.0       0.0         0       0.01.00000E20
$#    sfsa      sfsb      sast      sbst     sfsat     sfsbt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
*INCLUDE
00_CSD_setup.k
00_CFD_setup.k
*END

# COBOL Source Files for CICS Banking Sample Application

This document lists all COBOL source files that need to be compiled to
build the application, based on the JCL files in the buildjcl directory.

## CICS COBOL Programs

1. **ABNDPROC** - CICS COBOL program
2. **BNK1CAC** - CICS COBOL program
3. **BNK1CCA** - CICS COBOL program
4. **BNK1CCS** - CICS COBOL program
5. **BNK1CRA** - CICS COBOL program
6. **BNK1DAC** - CICS COBOL program
7. **BNK1DCS** - CICS COBOL program
8. **BNK1TFN** - CICS COBOL program
9. **BNK1UAC** - CICS COBOL program
10. **BNKMENU** - CICS COBOL program
11. **CRDTAGY1** - CICS COBOL program
12. **CRDTAGY2** - CICS COBOL program
13. **CRDTAGY3** - CICS COBOL program
14. **CRDTAGY4** - CICS COBOL program
15. **CRDTAGY5** - CICS COBOL program
16. **CREACC** - CICS COBOL program
17. **CRECUST** - Batch COBOL program (compiled with CICS proc)
18. **DBCRFUN** - Batch COBOL program (compiled with CICS proc)
19. **DELACC** - CICS COBOL program
20. **DELCUS** - CICS COBOL program
21. **GETCOMPY** - CICS COBOL program
22. **GETSCODE** - CICS COBOL program
23. **INQACC** - CICS COBOL program
24. **INQACCCU** - CICS COBOL program
25. **INQCUST** - Batch COBOL program (compiled with CICS proc)
26. **UPDACC** - CICS COBOL program
27. **UPDCUST** - CICS COBOL program
28. **XFRFUN** - COBOL program

## Batch COBOL Programs

1. **BANKDATA** - Batch COBOL program (compiled with BATCH proc)
2. **EXTDCUST** - Batch COBOL program (compiled with BATCH proc)

## BMS Maps (Not COBOL, but compiled)

The following BMS maps are also compiled as part of the build process:

1. **BNK1ACC** - BMS map
2. **BNK1CAM** - BMS map
3. **BNK1CCM** - BMS map
4. **BNK1CDM** - BMS map
5. **BNK1DAM** - BMS map
6. **BNK1DCM** - BMS map
7. **BNK1MAI** - BMS map
8. **BNK1TFM** - BMS map
9. **BNK1UAM** - BMS map

## Summary

- **Total COBOL Programs**: 30
  - CICS COBOL Programs: 28
  - Batch COBOL Programs: 2
- **Total BMS Maps**: 9

## Notes

- Most programs use the CICS procedure for compilation
- BANKDATA and EXTDCUST use the BATCH procedure
- All programs are compiled and link-edited as part of the build process
- The COMPALL.jcl file provides an en-masse compile job for all programs

"""
Demo Corpus Generator
=====================
Produces a realistic, internally-consistent synthetic document corpus for a
fictional refinery -- Bharat Petrochem Refinery, Jamnagar Complex.

The corpus is deliberately engineered to contain DISCOVERABLE CROSS-DOCUMENT
PATTERNS that no single document reveals:

  * P-101A suffers repeated mechanical seal failures across 3 years, recorded
    in separate work orders, an incident report and an inspection report --
    the recurrence is only visible when the documents are linked.
  * E-204 shows progressive wall thinning across two inspection cycles while a
    separate work order records tube leaks -- a correlated degradation story.
  * H2S exposure appears in an incident, a permit, and an SDS with an
    inconsistent exposure limit -- a genuine compliance gap.
  * V-301 has incident and work-order history but NO procedural document --
    the 'knowledge cliff' gap the platform is designed to surface.

Run:  python build_corpus.py
"""

import os
import textwrap

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_corpus")

DOCS = {}

# ---------------------------------------------------------------------------
# 1. INCIDENT REPORT -- the anchor event
# ---------------------------------------------------------------------------
DOCS["INC-2026-014_Seal_Failure_CDU.txt"] = """
BHARAT PETROCHEM REFINERY - JAMNAGAR COMPLEX
INCIDENT INVESTIGATION REPORT

Report No: INC-2026-014
Date of Incident: 09-Jan-2026
Time: 02:40 hrs
Unit: Crude Distillation Unit
Classification: Process Safety Event - Tier 2 (Loss of Primary Containment)
Reportable under: Factories Act 1948, Section 88A
Prepared by: Er. Anil Deshmukh, Process Engineer
Reviewed by: Mr. Rajesh Kumar, Chief Safety Officer

1. SUMMARY OF EVENT

At approximately 02:40 hrs on 09-Jan-2026, the Panel Operator observed a sudden
drop in discharge pressure on crude charge pump P-101A from 18.5 barg to 11.2 barg
over a period of four minutes. Simultaneously the local hydrocarbon detector AT-1142
in the pump bay registered a rising reading which peaked at 34 % LEL.

The Field Operator dispatched to the location reported visible liquid hydrocarbon
spray from the outboard mechanical seal of P-101A. The Shift Supervisor initiated
the unit emergency shutdown procedure per SOP-CDU-011 and P-101A was isolated.
Standby pump P-101B was started to maintain unit charge. No injury occurred.
Estimated release quantity: 380 litres of crude oil, fully contained within the
paved bund area.

2. IMMEDIATE CAUSE

Catastrophic failure of the outboard mechanical seal on P-101A. Seal faces were
recovered and showed circumferential scoring consistent with dry running.

3. ROOT CAUSE ANALYSIS

The investigation team applied a 5-Why analysis supported by review of historical
maintenance records.

Why 1: Hydrocarbon released. -> Mechanical seal failure on P-101A.
Why 2: Seal failed. -> Seal faces ran dry due to loss of flush flow.
Why 3: Flush flow lost. -> Seal flush line strainer was blocked with coke fines.
Why 4: Strainer blocked. -> Strainer cleaning was not performed at required frequency.
Why 5: Cleaning not performed. -> Seal flush strainer cleaning is not listed as a
       discrete task in the preventive maintenance plan for P-101A. It is referenced
       only in the OEM manual and relies on operator knowledge.

ROOT CAUSE: Procedural gap. The preventive maintenance schedule for P-101A does not
capture seal flush system maintenance as a controlled task. The organisation has
been dependent on undocumented operator knowledge of this requirement.

4. HISTORICAL CONTEXT

The investigation team notes that this is NOT the first mechanical seal failure on
this pump. Reference is made to WO-238811 (Mar-2024) and WO-221094 (Aug-2023), both
of which record seal replacement on P-101A. Neither work order triggered a root
cause investigation as each was closed as routine breakdown maintenance. The
recurrence pattern was not identified at the time.

5. HAZARDOUS SUBSTANCE EXPOSURE

Crude oil at this location contains dissolved hydrogen sulphide. Personal H2S
monitors carried by the responding Field Operator recorded a peak of 8 ppm during
the response, below the alarm threshold of 10 ppm. Reference SDS-CRUDE-01 for
exposure controls. Applicable standard: OISD-STD-105.

6. CORRECTIVE AND PREVENTIVE ACTIONS

CAPA-2026-031 : Add seal flush strainer cleaning to the PM plan for all CDU
                charge pumps at 90-day frequency. Owner: Reliability Engineer.
CAPA-2026-032 : Conduct a bad-actor review of all rotating equipment with more
                than two seal failures in a rolling 36-month window.
                Owner: Maintenance Engineer.
CAPA-2026-033 : Issue SOP covering seal support system maintenance. Currently no
                controlled procedure exists. Owner: Process Engineer.

7. REGULATORY NOTIFICATION

Notified to the Directorate of Industrial Safety and Health as required.
Compliance reference: Factories Act 1948, OISD-STD-105, MSIHC Rules 1989.
"""

# ---------------------------------------------------------------------------
# 2-3. WORK ORDERS -- the prior occurrences
# ---------------------------------------------------------------------------
DOCS["WO-238811_Seal_Replacement_P101A.txt"] = """
BHARAT PETROCHEM REFINERY - MAINTENANCE WORK ORDER
CMMS Export - Module: Corrective Maintenance

Work Order No     : WO-238811
Equipment Tag     : P-101A
Equipment Desc    : Crude Charge Pump A
Location          : Crude Distillation Unit
Maintenance Type  : Breakdown
Priority          : P1 - Urgent
Raised By         : Panel Operator
Raised On         : 18-Mar-2024 06:15 hrs
Completed On      : 19-Mar-2024 21:40 hrs
Total Downtime    : 39.4 hrs
Labour Hours      : 26.0
Executed By       : Mr. Suresh Patil, Maintenance Engineer

JOB DESCRIPTION
Pump P-101A tripped on low discharge pressure. Field inspection found mechanical
seal leak at outboard seal with continuous drip observed. Pump removed from service.

WORK PERFORMED
1. Isolated P-101A per SOP-CDU-011. Permit PTW-4471 issued for cold work.
2. Drained and flushed pump casing with nitrogen purge. N2 purge verified.
3. Removed coupling guard and decoupled from motor MTR-204.
4. Dismantled outboard mechanical seal cartridge.
5. Findings: seal faces scored. Secondary containment showed carbon deposits.
   Seal flush port partially blocked. Bearing housing showed no abnormality.
6. Replaced seal cartridge with OEM spare, part no MS-4412-B.
7. Reassembled, aligned coupling. Final alignment 0.04 mm within tolerance.
8. Vibration check on restart: 3.2 mm/s, acceptable per ISO 10816.

SPARES CONSUMED
MS-4412-B   Mechanical seal cartridge, outboard    Qty 1
GK-0881     Casing gasket set                      Qty 1
LB-2201     Bearing lube oil ISO VG 68             Qty 8 litres

REMARKS
Second seal failure on this pump within 8 months. Previous failure recorded under
WO-221094. Recommend investigation of seal flush system adequacy. Note: this
recommendation was recorded but no follow-up work order was raised.

CLOSURE
Closed as routine breakdown. No RCA initiated.
Reviewed by Reliability Engineer: signature on file.
"""

DOCS["WO-221094_Seal_Replacement_P101A.txt"] = """
BHARAT PETROCHEM REFINERY - MAINTENANCE WORK ORDER
CMMS Export - Module: Corrective Maintenance

Work Order No     : WO-221094
Equipment Tag     : P-101A
Equipment Desc    : Crude Charge Pump A
Location          : Crude Distillation Unit
Maintenance Type  : Breakdown
Priority          : P1 - Urgent
Raised On         : 04-Aug-2023 14:20 hrs
Completed On      : 05-Aug-2023 11:05 hrs
Total Downtime    : 20.8 hrs
Labour Hours      : 14.5
Executed By       : Mr. Suresh Patil, Maintenance Engineer

JOB DESCRIPTION
Reported gland leak from P-101A outboard seal area during routine round. Seal
leak rate increased over a 6 hour period. Decision taken to shut down and replace.

WORK PERFORMED
1. Pump isolated. Permit PTW-3922 issued.
2. Outboard mechanical seal cartridge removed and inspected.
3. Findings: light scoring on rotating face, elastomer hardened.
   Seal flush line found restricted. Strainer not cleaned since installation.
4. Seal cartridge replaced, part no MS-4412-B.
5. Flush line back-flushed manually. Strainer cleaned.
6. Restart vibration 2.9 mm/s. Discharge pressure restored to 18.4 barg.

SPARES CONSUMED
MS-4412-B   Mechanical seal cartridge, outboard    Qty 1
ST-1140     Flush line strainer element            Qty 1

REMARKS
Strainer condition noted as heavily fouled with coke fines. Operator advised to
include in routine checks. No formal PM task exists for this activity.

CLOSURE
Closed as routine breakdown. No RCA initiated.
"""

# ---------------------------------------------------------------------------
# 4. SOP -- the procedure that exists
# ---------------------------------------------------------------------------
DOCS["SOP-CDU-011_Charge_Pump_Isolation.txt"] = """
BHARAT PETROCHEM REFINERY
STANDARD OPERATING PROCEDURE

Document No   : SOP-CDU-011
Title         : Isolation and Handover of Crude Charge Pumps for Maintenance
Revision      : 04
Effective Date: 01-Apr-2025
Unit          : Crude Distillation Unit
Applicable To : P-101A, P-101B, P-102A, P-102B
Approved By   : Mr. Vikram Nair, Unit Head

1. PURPOSE
To define the controlled sequence for isolating crude charge pumps from the process
and handing them over to the maintenance department, ensuring elimination of stored
energy and hydrocarbon inventory prior to any intrusive work.

2. SCOPE
This procedure applies to all crude charge pumps in the Crude Distillation Unit.
It covers isolation only. It does NOT cover seal support system maintenance,
which is outside the scope of this document.

3. RESPONSIBILITY
Shift Supervisor    : Authorises isolation, verifies process conditions.
Panel Operator      : Executes remote isolation, confirms flow diversion.
Field Operator      : Executes physical isolation, applies locks and tags.
Permit Issuer       : Issues Permit to Work after verifying isolation complete.
Maintenance Engineer: Receives equipment, verifies isolation before starting work.

4. PRECAUTIONS
4.1 Crude oil in this service contains dissolved H2S. Personal gas monitors are
    mandatory. Alarm threshold is set at 10 ppm as an 8-hour reference value.
4.2 Pump casing may retain hydrocarbon under pressure after isolation.
4.3 Confined Space entry is NOT permitted under this procedure.
4.4 All electrical isolation shall follow lockout tagout requirements.

5. PROCEDURE

Step 1  Confirm standby pump is available and healthy. Verify P-101B on auto standby.
Step 2  Shift Supervisor authorises changeover. Record in shift log.
Step 3  Panel Operator starts standby pump, confirms discharge pressure stabilises
        at 18.0 barg to 19.0 barg. Confirm flow on FT-1103.
Step 4  Stop duty pump from panel. Confirm zero flow.
Step 5  Field Operator closes suction MOV-1101 and discharge MOV-1102. Confirm
        valve position locally, do not rely on panel indication alone.
Step 6  Electrical isolation of motor MTR-204 at MCC. Apply lock and personal tag.
Step 7  Depressurise casing to closed drain. Confirm zero pressure on PT-1105.
Step 8  Nitrogen purge casing. Purge until hydrocarbon reading below 1 % LEL.
Step 9  Gas test by Competent Person. Record on permit. Oxygen 19.5 % to 23.5 %.
Step 10 Permit Issuer issues PTW. Handover to Maintenance Engineer.

6. RESTORATION
Reverse sequence. Vibration check mandatory on restart. Acceptance limit 4.5 mm/s
per ISO 10816 for this machine class.

7. REFERENCES
OISD-STD-105  Work Permit System
IS 5571       Selection of electrical equipment for hazardous areas
ISO 10816     Mechanical vibration evaluation
Factories Act 1948
"""

# ---------------------------------------------------------------------------
# 5-6. INSPECTION REPORTS -- the exchanger degradation story
# ---------------------------------------------------------------------------
DOCS["INSP-2024-208_Heat_Exchanger_E204.txt"] = """
BHARAT PETROCHEM REFINERY
EQUIPMENT INSPECTION REPORT - THICKNESS SURVEY

Report No        : INSP-2024-208
Equipment Tag    : E-204
Equipment Desc   : Crude Preheat Exchanger, Shell and Tube
Location         : Crude Distillation Unit
Inspection Date  : 12-Sep-2024
Inspection Type  : Ultrasonic Thickness Survey, on-stream
Inspector        : Mr. Deepak Joshi, Inspection Engineer
NDT Technician   : Mr. Imran Shaikh
Procedure Ref    : API 570

1. SCOPE
On-stream ultrasonic thickness measurement at designated Condition Monitoring
Locations on the shell and inlet/outlet nozzles of E-204.

2. DESIGN DATA
Design Pressure  : 21 barg shell side
Design Temperature: 320 degC
Material         : Shell SA-516 Gr 70, Tubes SA-179
Nominal Thickness: 12.7 mm shell
Minimum Required Thickness: 9.5 mm

3. THICKNESS READINGS

CML ID   Location                Previous (mm)  Current (mm)  Loss (mm)
CML-01   Shell inlet quadrant        12.1          11.4          0.7
CML-02   Shell mid-body top          12.3          12.0          0.3
CML-03   Shell mid-body bottom       11.8          10.9          0.9
CML-04   Shell outlet quadrant       12.0          11.5          0.5
CML-05   Inlet nozzle neck           11.6          10.6          1.0
CML-06   Outlet nozzle neck          12.2          11.8          0.4

4. FINDINGS
Measurable wall thinning observed at CML-03, CML-05 and CML-01. The pattern of
metal loss is concentrated at the inlet quadrant and bottom of the shell,
consistent with erosion corrosion driven by entrained solids and turbulent flow
at the inlet. General corrosion is also evident across all CMLs.

Highest corrosion rate: CML-05 at 0.50 mm/year.
Remaining life at CML-05 based on current rate: 2.2 years to minimum thickness.

5. RECOMMENDATIONS
5.1 Reduce inspection interval for E-204 from 36 months to 18 months.
5.2 Install an erosion shield at the inlet nozzle at next available shutdown.
5.3 Monitor CML-03 and CML-05 at every opportunity.
5.4 Review upstream filtration for solids carryover.

6. NEXT INSPECTION DUE
Recommended: March 2026.
Compliance reference: API 570, OISD-STD-130.
"""

DOCS["INSP-2026-042_Heat_Exchanger_E204.txt"] = """
BHARAT PETROCHEM REFINERY
EQUIPMENT INSPECTION REPORT - THICKNESS SURVEY AND INTERNAL EXAMINATION

Report No        : INSP-2026-042
Equipment Tag    : E-204
Equipment Desc   : Crude Preheat Exchanger, Shell and Tube
Location         : Crude Distillation Unit
Inspection Date  : 21-Mar-2026
Inspection Type  : Ultrasonic Thickness Survey plus internal visual examination
Inspector        : Mr. Deepak Joshi, Inspection Engineer
Third Party Inspector: M/s Reliable NDT Services
Procedure Ref    : API 570

1. SCOPE
Follow-up thickness survey per recommendation 5.1 of INSP-2024-208, combined with
internal visual examination during unit shutdown.

2. THICKNESS READINGS

CML ID   Location                Sep-2024 (mm)  Mar-2026 (mm)  Rate (mm/yr)
CML-01   Shell inlet quadrant       11.4           10.6           0.53
CML-02   Shell mid-body top         12.0           11.8           0.13
CML-03   Shell mid-body bottom      10.9            9.8           0.73
CML-04   Shell outlet quadrant      11.5           11.1           0.27
CML-05   Inlet nozzle neck          10.6            9.7           0.60
CML-06   Outlet nozzle neck         11.8           11.5           0.20

3. FINDINGS

3.1 SHELL CONDITION
CML-03 is now at 9.8 mm against a minimum required thickness of 9.5 mm. Remaining
margin is 0.3 mm. At the observed corrosion rate of 0.73 mm/year this location
will reach minimum thickness within approximately 5 months.

CML-05 at 9.7 mm is similarly marginal. The corrosion rate at both locations has
INCREASED relative to the previous survey period, indicating the degradation
mechanism is accelerating rather than stable.

3.2 INTERNAL EXAMINATION
Internal visual examination of the shell side revealed erosion corrosion scars
downstream of the inlet nozzle. The erosion shield recommended in INSP-2024-208
recommendation 5.2 was NOT installed. No management of change record exists for
the deferral of this recommendation.

3.3 TUBE BUNDLE
Eddy current examination of 100 percent of tubes identified 14 tubes with wall
loss exceeding 40 percent. Two tubes showed through-wall indication consistent
with the tube leak reported under WO-244501.

4. IMMEDIATE ACTIONS TAKEN
14 tubes plugged. Fitness for service assessment initiated for CML-03 and CML-05
per API 579 Level 1.

5. RECOMMENDATIONS
5.1 E-204 shall NOT be returned to full design pressure without a fitness for
    service assessment. Interim operating pressure restricted to 17 barg.
5.2 Erosion shield installation is now mandatory, not advisory.
5.3 Shell section replacement to be scoped for next turnaround.
5.4 Raise NCR against the failure to action INSP-2024-208 recommendation 5.2.

6. NON-CONFORMANCE
NCR-2026-018 raised. Previous inspection recommendation was not implemented and
no deviation was formally approved. This represents a breakdown in the inspection
recommendation tracking process.

Compliance reference: API 570, API 579, OISD-STD-130, Factories Act 1948.
"""

DOCS["WO-244501_Tube_Leak_E204.txt"] = """
BHARAT PETROCHEM REFINERY - MAINTENANCE WORK ORDER

Work Order No     : WO-244501
Equipment Tag     : E-204
Equipment Desc    : Crude Preheat Exchanger
Location          : Crude Distillation Unit
Maintenance Type  : Breakdown
Priority          : P1 - Urgent
Raised On         : 08-Feb-2026 09:30 hrs
Completed On      : 11-Feb-2026 18:00 hrs
Total Downtime    : 80.5 hrs
Executed By       : Mr. Suresh Patil, Maintenance Engineer

JOB DESCRIPTION
Suspected tube leak on E-204. Shell side sample showed hydrocarbon contamination
inconsistent with normal operation. Unit rate reduced pending investigation.

WORK PERFORMED
1. E-204 isolated and blinded. Permit PTW-5518 issued for cold work.
2. Shell side drained and steamed out. Gas test clear.
3. Hydrotest of tube bundle at 1.5 times design pressure.
4. Two tubes identified with through-wall leakage. Tubes plugged.
5. Bundle reinstalled. Leak test satisfactory.

FINDINGS
Tube leak confirmed on two tubes in the peripheral row nearest the inlet nozzle.
Visual inspection of accessible shell internals showed erosion damage in the
inlet region. Erosion appears longstanding.

REMARKS
Inspection department advised that thickness survey INSP-2024-208 had previously
flagged accelerated metal loss in this region and recommended an erosion shield
which was not installed. Recommend inspection review before restart.

CLOSURE
Closed. Equipment returned to service at reduced rate pending inspection review.
"""

# ---------------------------------------------------------------------------
# 7. PERMIT TO WORK
# ---------------------------------------------------------------------------
DOCS["PTW-5518_Cold_Work_E204.txt"] = """
BHARAT PETROCHEM REFINERY
PERMIT TO WORK - COLD WORK

Permit No        : PTW-5518
Date of Issue    : 08-Feb-2026
Validity         : 08-Feb-2026 10:00 hrs to 11-Feb-2026 18:00 hrs
Work Location    : Crude Distillation Unit, Exchanger Bay 2
Equipment        : E-204
Issuing Authority: Mr. Vikram Nair, Permit Issuer
Receiving Authority: Mr. Suresh Patil, Permit Receiver
Reference Standard: OISD-STD-105

1. DESCRIPTION OF WORK
Isolation, blinding, bundle withdrawal and tube plugging on crude preheat
exchanger E-204 following suspected tube leak.

2. HAZARD IDENTIFICATION
Residual hydrocarbon inventory in shell and tube side.
Potential H2S evolution from sour crude residues.
Stored pressure and thermal energy.
Overhead lifting operation for bundle withdrawal.
Manual handling.

3. ISOLATION CERTIFICATE
Isolation Cert No: ISO-5518-A
Process isolation : Double block and bleed on inlet and outlet, blinds installed.
Electrical isolation: Not applicable, static equipment.
Drain and vent    : Completed to closed drain system.
Purging           : Steam out followed by air freshening.

4. GAS TEST RECORD

Time      Hydrocarbon (%LEL)   H2S (ppm)   Oxygen (%)   Tested By
09:45     0                    2           20.8         Competent Person
13:00     0                    1           20.9         Competent Person
09:00 D2  0                    0           20.9         Competent Person
09:00 D3  0                    3           20.7         Competent Person

NOTE: H2S reading of 3 ppm recorded on Day 3. Work continued. The permit
condition specifies work may proceed below 5 ppm. This threshold differs from
the 10 ppm alarm setpoint stated in SOP-CDU-011 and from the value in
SDS-CRUDE-01. Discrepancy noted by Safety Officer for review.

5. PERSONAL PROTECTIVE EQUIPMENT REQUIRED
Flame retardant coverall, safety helmet, safety goggles, chemical resistant gloves,
personal H2S monitor, escape set available at work location.

6. PRECAUTIONS
Continuous gas monitoring during bundle withdrawal.
Fire watch not required, cold work only. No hot work permitted under this permit.
Confined Space entry NOT authorised under this permit.
Area barricaded. Lifting plan approved separately.

7. CLOSURE
Work completed 11-Feb-2026 17:40 hrs. Area cleared, blinds removed per checklist.
Permit closed by Issuing Authority.
"""

# ---------------------------------------------------------------------------
# 8. SAFETY DATA SHEET -- the compliance discrepancy
# ---------------------------------------------------------------------------
DOCS["SDS-CRUDE-01_Crude_Oil_Sour.txt"] = """
SAFETY DATA SHEET
In accordance with Manufacture Storage and Import of Hazardous Chemicals Rules

Document No : SDS-CRUDE-01
Revision    : 03
Date        : 15-Jun-2025
Product     : Crude Oil, Sour Grade
Supplier    : Bharat Petrochem Refinery

SECTION 1 - IDENTIFICATION
Product Name : Crude Oil, Sour
Use          : Refinery feedstock
UN Number    : 1267
Class        : 3 Flammable Liquid

SECTION 2 - HAZARD IDENTIFICATION
Highly flammable liquid and vapour.
Contains dissolved hydrogen sulphide. H2S is an acutely toxic gas that rapidly
deadens the sense of smell, so odour is NOT a reliable warning of exposure.
May cause cancer. Contains benzene.
Toxic to aquatic life with long lasting effects.

SECTION 3 - COMPOSITION
Component               CAS No        Concentration
Hydrocarbons, mixed     8002-05-9     Balance
Hydrogen sulphide       7783-06-4     up to 200 ppm dissolved
Benzene                 71-43-2       0.1 to 2 percent

SECTION 4 - FIRST AID MEASURES
Inhalation: Remove to fresh air immediately. Rescuer must wear breathing apparatus.
Do not attempt rescue without respiratory protection. H2S has caused multiple
rescuer fatalities. Administer oxygen if trained. Seek medical attention.
Skin contact: Remove contaminated clothing. Wash with soap and water.
Eye contact: Irrigate with water for 15 minutes.

SECTION 5 - FIRE FIGHTING
Suitable media: Foam, dry chemical powder, carbon dioxide.
Unsuitable: Water jet.
Hazardous combustion products include sulphur dioxide and carbon monoxide.

SECTION 8 - EXPOSURE CONTROLS
Hydrogen sulphide occupational exposure limit:
    8-hour time weighted average : 5 ppm
    Short term exposure limit    : 10 ppm over 15 minutes
Benzene 8-hour TWA: 1 ppm

Engineering controls: Fixed gas detection with alarm. Local exhaust ventilation
where practicable. Closed sampling systems.
Personal protection: Personal H2S monitor mandatory in all sour service areas.
Escape breathing apparatus available.

SECTION 9 - PHYSICAL PROPERTIES
Appearance : Dark brown to black liquid
Flash Point: Below 23 degC
Density    : 850 kg/m3 approximately

SECTION 15 - REGULATORY INFORMATION
Regulated under MSIHC Rules 1989. Storage licensed under PESO.
Reference OISD-STD-105 for work permit requirements in sour service.
"""

# ---------------------------------------------------------------------------
# 9. SHIFT LOG
# ---------------------------------------------------------------------------
DOCS["ShiftLog_CDU_Jan2026.txt"] = """
BHARAT PETROCHEM REFINERY - CRUDE DISTILLATION UNIT
SHIFT LOG BOOK EXTRACT - JANUARY 2026

=== 08-Jan-2026 NIGHT SHIFT (22:00 - 06:00) ===
Shift Supervisor : Mr. Rajesh Kumar
Panel Operator   : Mr. Sunil Rane
Field Operator   : Mr. Ganesh More

22:15 Took over unit from general shift. Unit stable at 108 percent of design rate.
      P-101A running as duty, P-101B on auto standby.
23:40 Routine round completed. Noted minor seepage at P-101A outboard seal area.
      Quantity described as occasional drip. Logged for day shift attention.
01:20 Seepage at P-101A appears unchanged. Continued monitoring.
02:40 Sudden drop in P-101A discharge pressure from 18.5 barg to 11.2 barg.
      Hydrocarbon detector AT-1142 alarm at 34 % LEL.
02:42 Field Operator reports liquid spray from P-101A outboard seal.
02:44 Emergency shutdown of P-101A initiated per SOP-CDU-011. P-101B started.
02:50 P-101A isolated. Spray stopped. Area cordoned. Fire water on standby.
03:10 Gas readings falling. H2S peak 8 ppm recorded on personal monitor.
03:30 Chief Safety Officer on site. Incident classified Tier 2.
04:00 Unit stabilised on P-101B at 96 percent rate.
05:30 Area cleaned. Spill contained in bund. Estimated 380 litres crude.
      Incident report INC-2026-014 initiated.

=== 09-Jan-2026 DAY SHIFT (06:00 - 14:00) ===
Shift Supervisor : Mr. Vikram Nair
14:00 P-101A remains isolated pending maintenance. Investigation team formed.
      Note raised: this is the third seal failure on P-101A. Refer WO-238811
      and WO-221094. Reliability Engineer to review.

=== 15-Jan-2026 DAY SHIFT ===
09:00 E-204 shell side sample sent to lab. Slight hydrocarbon odour noted.
      Lab result pending. Possible tube leak to be investigated.
11:30 Unit rate held at 96 percent as precaution.

=== 22-Jan-2026 NIGHT SHIFT ===
03:00 Routine round. All parameters normal. Vibration on P-101B 3.4 mm/s.
      Discharge 18.6 barg. No abnormality.
"""

# ---------------------------------------------------------------------------
# 10. EQUIPMENT MANUAL EXTRACT
# ---------------------------------------------------------------------------
DOCS["OEM_Manual_Extract_P101_Series.txt"] = """
KIRLOSKAR PROCESS PUMPS
OPERATION AND MAINTENANCE MANUAL - EXTRACT
Model KPP-250-400 Heavy Duty Process Pump

Applicable Tags at Bharat Petrochem: P-101A, P-101B, P-102A, P-102B
Manual Ref: OM-KPP-250-R7

SECTION 6 - MECHANICAL SEAL AND SEAL SUPPORT SYSTEM

6.1 SEAL ARRANGEMENT
This pump is supplied with a cartridge type single mechanical seal with API Plan 11
flush arrangement. Flush is taken from the pump discharge, passed through a
strainer and flow control orifice, and injected into the seal chamber.

6.2 CRITICAL WARNING
The mechanical seal is entirely dependent on continuous flush flow for face
lubrication and heat removal. Interruption of flush flow will cause the seal faces
to run dry. Dry running will destroy the seal within minutes and may result in
loss of containment of the pumped fluid.

6.3 SEAL FLUSH STRAINER MAINTENANCE
The Plan 11 flush line incorporates a Y-type strainer upstream of the flow control
orifice. In services containing entrained solids, coke fines or catalyst carryover,
this strainer will foul progressively.

RECOMMENDED FREQUENCY: The strainer element shall be inspected and cleaned every
90 days in clean service, and every 30 days in services containing solids or coke
fines. Failure to maintain the strainer is the single most common cause of premature
seal failure in this pump range.

6.4 INDICATIONS OF FLUSH RESTRICTION
- Rising seal chamber temperature
- Increased seal face noise
- Intermittent weeping at the seal followed by rapid failure
- Reduction in flush line flow indication where fitted

6.5 SEAL REPLACEMENT
Refer to Section 7 for cartridge removal. Recommended spare: MS-4412-B for
outboard position. Always replace the flush strainer element at the same time as
a seal replacement. Reusing a fouled strainer will cause repeat failure.

SECTION 8 - VIBRATION LIMITS
Acceptance on commissioning: below 2.8 mm/s RMS
Alert level                : 4.5 mm/s RMS
Shutdown level             : 7.1 mm/s RMS
Reference standard ISO 10816 machine class II.

SECTION 9 - LUBRICATION
Bearing lubricant: ISO VG 68 mineral oil.
Oil change interval: 4000 running hours or 6 months whichever is earlier.
Monitor for oil degradation and lube oil contamination at each change.
"""

# ---------------------------------------------------------------------------
# 11. AUDIT REPORT
# ---------------------------------------------------------------------------
DOCS["AUDIT-2026-Q1_Internal_Safety_Audit.txt"] = """
BHARAT PETROCHEM REFINERY
INTERNAL PROCESS SAFETY AUDIT REPORT

Audit Ref     : AUDIT-2026-Q1
Audit Period  : January to March 2026
Auditor       : Mr. Prakash Iyer, Lead Auditor
Scope         : Crude Distillation Unit and associated utilities
Standard      : OISD-STD-105, OISD-STD-130, Factories Act 1948

EXECUTIVE SUMMARY
The audit examined mechanical integrity management, permit to work compliance and
incident investigation effectiveness. Four non-conformances and three observations
were raised. Two non-conformances are classified as Major.

FINDING 1 - MAJOR NON-CONFORMANCE
Ref: NCR-2026-016
Clause: OISD-STD-130 inspection recommendation tracking
Finding: Inspection recommendation 5.2 of report INSP-2024-208 concerning
installation of an erosion shield on E-204 was not implemented and not formally
deferred. The equipment subsequently developed a tube leak recorded under
WO-244501. There is no management of change record covering the non-implementation.
Root cause: No closed loop tracking system exists linking inspection
recommendations to work order execution.
Corrective action required by: 30-Jun-2026.

FINDING 2 - MAJOR NON-CONFORMANCE
Ref: NCR-2026-017
Clause: Factories Act 1948 incident investigation requirements
Finding: Repeat failures of the same mode on the same equipment were not escalated
to root cause investigation. Pump P-101A suffered mechanical seal failure on three
occasions, recorded under WO-221094, WO-238811 and INC-2026-014. Only the third
event triggered an investigation. Both earlier work orders contain written
observations recommending review of the seal flush system; neither was actioned.
Root cause: Work order closure process does not check equipment failure history.
Corrective action required by: 31-May-2026.

FINDING 3 - MINOR NON-CONFORMANCE
Ref: NCR-2026-018
Finding: Inconsistent H2S exposure thresholds across controlled documents.
SOP-CDU-011 clause 4.1 states an alarm threshold of 10 ppm as an 8-hour reference.
SDS-CRUDE-01 Section 8 states an 8-hour TWA of 5 ppm with a 15-minute STEL of 10 ppm.
Permit PTW-5518 applied a work-continuation threshold of 5 ppm.
Three controlled documents state three different operative values for the same
hazard. This creates a foreseeable risk of incorrect field decision making.
Corrective action required by: 30-Apr-2026.

FINDING 4 - MINOR NON-CONFORMANCE
Ref: NCR-2026-019
Finding: Seal support system maintenance is described only in the OEM manual
OM-KPP-250-R7 Section 6.3. It is not reflected in any controlled site procedure
or in the preventive maintenance schedule. The requirement is therefore dependent
on individual knowledge rather than a controlled system.

OBSERVATION 1
Vessel V-301 has incident and maintenance history on record but no site operating
procedure or OEM documentation could be located during the audit. The unit relies
on the knowledge of two long serving operators, both of whom are within five years
of superannuation.

OBSERVATION 2
Document control across the unit is fragmented. Inspection reports, work orders,
permits and procedures reside in four separate systems with no cross referencing.
Auditors required approximately 11 hours to assemble the evidence trail for
Finding 2, which a linked system would have surfaced immediately.

OBSERVATION 3
Corrosion rate trending is performed manually per equipment. There is no systematic
review that would identify accelerating degradation across the equipment population.
"""

# ---------------------------------------------------------------------------
# 12. THE KNOWLEDGE-GAP ASSET (incident + WO but no procedure)
# ---------------------------------------------------------------------------
DOCS["INC-2025-097_Level_Excursion_V301.txt"] = """
BHARAT PETROCHEM REFINERY
INCIDENT INVESTIGATION REPORT

Report No: INC-2025-097
Date of Incident: 22-Nov-2025
Unit: Crude Distillation Unit
Equipment: V-301
Classification: Near Miss - High Potential
Prepared by: Er. Anil Deshmukh, Process Engineer

1. SUMMARY
During a feed rate change, the level in overhead accumulator V-301 rose rapidly and
reached the high level trip setpoint. LSH-3011 actuated and tripped the overhead
pump. Liquid carryover to the downstream compressor K-301 was narrowly avoided.
Had the trip not functioned, liquid ingress to K-301 could have caused
catastrophic mechanical damage and potential loss of containment.

2. SEQUENCE
14:10 Feed rate increase initiated from 96 to 104 percent.
14:22 Overhead condenser duty lagged the rate change. Level in V-301 began rising.
14:31 LT-3010 indicated 78 percent. No operator action taken.
14:38 Level reached 92 percent. LSH-3011 trip actuated.
14:39 Overhead pump tripped. Level stabilised at 94 percent.

3. FINDINGS
3.1 There is no written operating procedure for V-301 level management during
    rate changes. The Panel Operator on duty had two years of experience and
    stated that he had been trained verbally by a senior colleague.
3.2 No alarm was configured between the normal operating band and the trip point.
    The operator therefore received no early warning.
3.3 Interviews established that experienced operators routinely reduce the rate
    ramp gradient when overhead conditions are marginal. This practice is
    effective but exists nowhere in documentation.

4. ROOT CAUSE
Absence of documented operating knowledge. The safe operating envelope for V-301
during transient conditions is held tacitly by a small number of experienced
personnel and has never been captured in a controlled document.

5. CORRECTIVE ACTIONS
CAPA-2025-114 : Develop and issue an operating procedure for V-301 covering
                transient and rate change conditions. Owner: Process Engineer.
                STATUS AS OF MAR-2026: NOT STARTED.
CAPA-2025-115 : Configure a high level pre-alarm on LT-3010 at 80 percent.
                STATUS: Completed.

6. NOTE FROM INVESTIGATION TEAM
The team wishes to record that the two operators whose knowledge prevented
escalation on previous occasions are both due to retire within five years. Their
operational knowledge of V-301 is not documented anywhere.
"""

DOCS["WO-241203_Level_Transmitter_V301.txt"] = """
BHARAT PETROCHEM REFINERY - MAINTENANCE WORK ORDER

Work Order No     : WO-241203
Equipment Tag     : V-301
Equipment Desc    : Overhead Accumulator
Location          : Crude Distillation Unit
Maintenance Type  : Corrective
Priority          : P2
Raised On         : 25-Nov-2025
Completed On      : 26-Nov-2025
Executed By       : Mr. Farhan Qureshi, Instrumentation Engineer

JOB DESCRIPTION
Following near miss INC-2025-097, configure high level pre-alarm on LT-3010 and
verify calibration of level instrumentation on V-301.

WORK PERFORMED
1. LT-3010 calibration verified against sight glass. Transmitter drift of 1.8
   percent of span identified and corrected.
2. High level pre-alarm configured at 80 percent in DCS.
3. LSH-3011 trip function tested by simulation. Trip actuated correctly.
4. Loop check completed on LT-3010, LIC-3010 and LSH-3011.

FINDINGS
Transmitter drift noted. Last documented calibration of LT-3010 was 41 months
prior. The instrument calibration schedule for V-301 instrumentation could not be
located. No OEM documentation for V-301 instrumentation is held on site.

REMARKS
Instrumentation Engineer notes that no equipment file exists for V-301. Datasheets,
calibration history and OEM manuals are not available. Recommend equipment file
reconstruction.
"""

# ---------------------------------------------------------------------------
# 13. HAZOP EXTRACT
# ---------------------------------------------------------------------------
DOCS["HAZOP-CDU-2023_Node4_Extract.txt"] = """
BHARAT PETROCHEM REFINERY
HAZOP STUDY REPORT - EXTRACT

Study Ref   : HAZOP-CDU-2023
Node        : Node 4 - Crude Charge Pumping
Date        : 14-Nov-2023
Chairman    : Mr. Prakash Iyer
Scribe      : Er. Anil Deshmukh
Team        : Process Engineer, Maintenance Engineer, Operations Representative,
              Instrumentation Engineer, Safety Officer

NODE DESCRIPTION
Crude oil transfer from storage tank T-501 through charge pumps P-101A and P-101B
to preheat exchanger train including E-204, and onward to the crude heater F-101.
Design intent: deliver 480 m3/hr of sour crude at 19 barg to the preheat train.

DEVIATION: NO FLOW
Cause 1   : Pump trip on power failure.
Consequence: Loss of feed to heater F-101, potential tube overheating.
Safeguards: Low flow alarm FIC-1103, heater trip on low flow, standby pump auto start.
Action    : None.

DEVIATION: LOSS OF CONTAINMENT AT PUMP
Cause 1   : Mechanical seal failure on P-101A or P-101B.
Consequence: Release of sour crude at grade. Fire risk. H2S exposure risk to
            personnel in the pump bay. Potential for escalation to adjacent
            equipment.
Safeguards: Hydrocarbon detection AT-1142, H2S detection, bunding, remote
            isolation capability, fire water monitors.
Comment   : The team noted that seal reliability is dependent on the seal flush
            system. The team was unable to confirm whether seal flush strainer
            maintenance is included in the preventive maintenance schedule.
Action 4.7: Verify that seal support system maintenance tasks are captured in the
            PM schedule for P-101A and P-101B.
            Owner: Reliability Engineer. Due: Q2 2024.
            STATUS AT INC-2026-014: NOT CLOSED.

DEVIATION: HIGH TEMPERATURE
Cause 1   : Loss of cooling water to seal cooler.
Consequence: Seal face damage, potential seal failure.
Safeguards: Seal chamber temperature indication where fitted.
Comment   : Not all pumps in this node have seal chamber temperature indication.
Action 4.8: Evaluate fitment of seal chamber temperature monitoring on critical
            charge pumps. Owner: Instrumentation Engineer. Due: Q4 2024.
            STATUS: Deferred, no revised date recorded.

DEVIATION: EROSION IN PREHEAT TRAIN
Cause 1   : Solids carryover from crude storage.
Consequence: Erosion corrosion of exchanger shells, particularly at inlet nozzles.
            Progressive wall thinning leading to potential loss of containment.
Safeguards: Periodic thickness survey per API 570.
Comment   : E-204 identified as the most exposed item due to inlet geometry.
Action 4.9: Review adequacy of upstream filtration and consider erosion protection
            at exchanger inlet nozzles. Owner: Process Engineer. Due: Q1 2024.
            STATUS: Partially addressed. Erosion shield recommended by inspection
            but not installed as of Mar-2026.
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    written = 0
    for name, content in DOCS.items():
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        written += 1
    print(f"Wrote {written} documents to {OUT}")
    total = sum(len(c) for c in DOCS.values())
    print(f"Total corpus size: {total:,} characters")


if __name__ == "__main__":
    main()

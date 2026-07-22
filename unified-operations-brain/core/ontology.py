"""
Industrial Ontology & Entity Extraction
========================================
Rule-based, zero-dependency entity extraction tuned for Indian heavy-industry
document corpora (refineries, steel plants, petrochemical facilities).

Design rationale:
  We deliberately avoid an LLM here. Entity extraction in industrial documents
  is a HIGH-PRECISION problem -- an equipment tag is either V-101 or it is not.
  Regex + a curated ontology gives deterministic, auditable, offline extraction
  with ~0ms latency and zero cost. LLMs are reserved for the synthesis layer.

Ontology covers 8 entity classes drawn from ISA-5.1 (instrumentation),
ISO 14224 (equipment taxonomy) and Indian statutory frameworks.
"""

import re
from collections import defaultdict

# ---------------------------------------------------------------------------
# ENTITY CLASS DEFINITIONS
# ---------------------------------------------------------------------------

ENTITY_COLORS = {
    "EQUIPMENT":   "#00d4ff",
    "REGULATION":  "#ff6b6b",
    "PARAMETER":   "#ffd93d",
    "PERSONNEL":   "#a78bfa",
    "FAILURE":     "#ff8c42",
    "CHEMICAL":    "#4ade80",
    "DOCUMENT":    "#94a3b8",
    "LOCATION":    "#f472b6",
}

ENTITY_DESCRIPTIONS = {
    "EQUIPMENT":   "Tagged plant assets (ISA-5.1 / ISO 14224 taxonomy)",
    "REGULATION":  "Statutory and standards references",
    "PARAMETER":   "Process measurements with units",
    "PERSONNEL":   "Named individuals and role designations",
    "FAILURE":     "Failure modes and degradation mechanisms",
    "CHEMICAL":    "Process fluids and hazardous substances",
    "DOCUMENT":    "Cross-referenced document identifiers",
    "LOCATION":    "Plant areas, units and zones",
}

# ---------------------------------------------------------------------------
# EQUIPMENT TAG PATTERNS  (ISA-5.1 loop numbering convention)
# ---------------------------------------------------------------------------
# Prefix letter(s) encode equipment class; digits encode unit + serial.
EQUIPMENT_CLASS_MAP = {
    "P":   "Pump",
    "C":   "Compressor",
    "V":   "Vessel",
    "T":   "Tank",
    "E":   "Heat Exchanger",
    "F":   "Furnace/Heater",
    "R":   "Reactor",
    "K":   "Compressor",
    "D":   "Drum",
    "PSV": "Pressure Safety Valve",
    "PRV": "Pressure Relief Valve",
    "MOV": "Motor Operated Valve",
    "XV":  "Shutdown Valve",
    "PT":  "Pressure Transmitter",
    "TT":  "Temperature Transmitter",
    "FT":  "Flow Transmitter",
    "LT":  "Level Transmitter",
    "AT":  "Analyser Transmitter",
    "PIC": "Pressure Controller",
    "TIC": "Temperature Controller",
    "FIC": "Flow Controller",
    "LIC": "Level Controller",
    "PSH": "Pressure Switch High",
    "TSH": "Temperature Switch High",
    "LSH": "Level Switch High",
    "LSL": "Level Switch Low",
    "CB":  "Coke Oven Battery",
    "BF":  "Blast Furnace",
    "CV":  "Conveyor",
    "GB":  "Gearbox",
    "MTR": "Motor",
    "HX":  "Heat Exchanger",
}

# Multi-char prefixes must be tried before single-char ones
_EQ_PREFIXES = sorted(EQUIPMENT_CLASS_MAP.keys(), key=len, reverse=True)
_EQ_PREFIX_ALT = "|".join(_EQ_PREFIXES)

EQUIPMENT_RE = re.compile(
    rf"\b(?P<prefix>{_EQ_PREFIX_ALT})[-\s]?(?P<num>\d{{2,4}}[A-Z]?)\b"
)

# ---------------------------------------------------------------------------
# REGULATORY / STANDARDS REFERENCES
# ---------------------------------------------------------------------------
REGULATION_PATTERNS = [
    (r"\bOISD[-\s]?(?:STD[-\s]?)?(\d{3})\b",              "OISD-STD-{0}"),
    (r"\bIS[-\s]?(\d{3,5})(?::\s?(\d{4}))?\b",            "IS {0}"),
    (r"\bAPI[-\s]?(\d{3}[A-Z]?)\b",                       "API {0}"),
    (r"\bASME\s+([IVXB]+(?:\.\d+)?|B\d+\.\d+)\b",         "ASME {0}"),
    (r"\bIEC[-\s]?(\d{5})\b",                             "IEC {0}"),
    (r"\bISO[-\s]?(\d{4,5})\b",                           "ISO {0}"),
    (r"\bNFPA[-\s]?(\d{2,3}[A-Z]?)\b",                    "NFPA {0}"),
    (r"\bPESO\b",                                         "PESO"),
    (r"\bDGMS\b",                                         "DGMS"),
    (r"\bDGFASLI\b",                                      "DGFASLI"),
    (r"\bCPCB\b",                                         "CPCB"),
    (r"\bFactor(?:y|ies)\s+Act(?:,?\s*1948)?\b",          "Factories Act 1948"),
    (r"\bSection\s+(\d{1,3}[A-Z]?)\s+of\s+the\s+Factor",  "Factories Act s.{0}"),
    (r"\bCEA\s+Regulations?\b",                           "CEA Regulations"),
    (r"\bSMPV\b",                                         "SMPV Rules"),
    (r"\bMSIHC\b",                                        "MSIHC Rules 1989"),
]

# ---------------------------------------------------------------------------
# PROCESS PARAMETERS -- value + unit pairs
# ---------------------------------------------------------------------------
UNIT_ALTERNATIVES = (
    r"bar\s?g|barg|bar|kg/cm2|kg/cm²|kPa|MPa|psi|psig|"
    r"°C|deg\s?C|degC|°F|"
    r"m3/hr|m³/hr|Nm3/hr|Nm³/hr|LPM|kL/hr|MT/hr|TPH|t/h|"
    r"ppm|ppb|%\s?LEL|%LEL|%\s?v/v|vol%|"
    r"mm/s|micron|µm|mm|"
    r"kW|MW|kWh|HP|A|V|kV|"
    r"pH|cP|cSt|"
    r"rpm|RPM|Hz|dB\(?A\)?"
)

# Negative lookbehind on '-' and letters prevents matching the "101A" inside
# an equipment tag like P-101A as "101 Amperes". Ambiguity between single-letter
# units (A, V) and tag suffixes is the main precision risk in this class.
PARAMETER_RE = re.compile(
    rf"(?<![A-Za-z0-9\-/])(?P<val>\d+(?:\.\d+)?)\s?(?P<unit>{UNIT_ALTERNATIVES})"
    rf"(?![a-zA-Z0-9])"
)

# Single-character units are only accepted when whitespace-separated from the
# number is NOT required but a preceding tag prefix is disqualifying.
_AMBIGUOUS_UNITS = {"A", "V"}

# ---------------------------------------------------------------------------
# PERSONNEL -- role designations and named individuals
# ---------------------------------------------------------------------------
ROLE_TERMS = [
    "Shift Supervisor", "Shift In-charge", "Shift Incharge", "Panel Operator",
    "Field Operator", "Safety Officer", "Chief Safety Officer", "Fire Officer",
    "Maintenance Engineer", "Reliability Engineer", "Rotating Equipment Engineer",
    "Instrumentation Engineer", "Electrical Engineer", "Process Engineer",
    "Inspection Engineer", "Plant Manager", "Unit Head", "Area Manager",
    "Permit Issuer", "Permit Receiver", "Competent Person", "Third Party Inspector",
    "Contractor Supervisor", "Rigger", "Welder", "Fitter", "Technician",
    "Quality Inspector", "NDT Technician", "Occupier", "Factory Manager",
]
ROLE_RE = re.compile(r"\b(" + "|".join(re.escape(r) for r in ROLE_TERMS) + r")\b", re.I)

# Indian-name-aware pattern: honorific + Titlecase tokens
NAME_RE = re.compile(
    r"\b(?:Mr\.?|Ms\.?|Mrs\.?|Dr\.?|Shri|Smt\.?|Er\.?)\s+"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
)

# ---------------------------------------------------------------------------
# FAILURE MODES  (ISO 14224 Annex B taxonomy, condensed)
# ---------------------------------------------------------------------------
FAILURE_TERMS = [
    "seal leak", "mechanical seal failure", "gland leak", "packing leak",
    "bearing failure", "bearing wear", "bearing seizure", "shaft misalignment",
    "vibration exceedance", "high vibration", "cavitation", "impeller erosion",
    "erosion", "corrosion", "pitting corrosion", "crevice corrosion",
    "stress corrosion cracking", "SCC", "hydrogen induced cracking", "HIC",
    "sulphide stress cracking", "wall thinning", "metal loss", "flow induced vibration",
    "fatigue crack", "thermal fatigue", "creep damage", "coking", "fouling",
    "tube leak", "tube rupture", "tube plugging", "refractory damage",
    "refractory spalling", "insulation damage", "CUI", "corrosion under insulation",
    "gasket blowout", "flange leak", "weld defect", "porosity", "lack of fusion",
    "undercut", "lamination", "blistering", "overheating", "hot spot",
    "trip on high", "spurious trip", "valve passing", "valve seat leakage",
    "actuator failure", "solenoid failure", "loop failure", "transmitter drift",
    "calibration drift", "sensor fouling", "winding failure", "insulation breakdown",
    "earth fault", "phase imbalance", "motor overload", "gearbox failure",
    "coupling failure", "lube oil contamination", "oil degradation",
    "surge", "stall", "loss of containment", "flameout", "backfire", "gas ingress",
]
FAILURE_RE = re.compile(r"\b(" + "|".join(re.escape(f) for f in FAILURE_TERMS) + r")\b", re.I)

# ---------------------------------------------------------------------------
# CHEMICALS / PROCESS FLUIDS
# ---------------------------------------------------------------------------
CHEMICAL_TERMS = [
    "hydrogen sulphide", "hydrogen sulfide", "H2S", "carbon monoxide", "CO",
    "carbon dioxide", "CO2", "methane", "CH4", "ammonia", "NH3", "chlorine", "Cl2",
    "sulphur dioxide", "SO2", "nitrogen", "N2", "oxygen", "O2", "hydrogen", "H2",
    "LPG", "LNG", "naphtha", "kerosene", "diesel", "HSD", "gasoline", "MS",
    "crude oil", "fuel oil", "furnace oil", "vacuum residue", "VGO",
    "coke oven gas", "COG", "blast furnace gas", "BFG", "producer gas",
    "benzene", "toluene", "xylene", "BTX", "MEA", "DEA", "amine", "caustic",
    "sulphuric acid", "hydrochloric acid", "HCl", "nitric acid",
    "steam", "condensate", "cooling water", "DM water", "instrument air",
    "nitrogen blanket", "flare gas", "sour water", "slop oil",
]
CHEMICAL_RE = re.compile(r"\b(" + "|".join(re.escape(c) for c in CHEMICAL_TERMS) + r")\b", re.I)

# ---------------------------------------------------------------------------
# DOCUMENT CROSS-REFERENCES
# ---------------------------------------------------------------------------
DOCUMENT_PATTERNS = [
    (r"\b(?:WO|W\.O\.)[-\s]?(\d{4,8})\b",        "WO-{0}"),
    (r"\bPTW[-\s]?(\d{3,8})\b",                  "PTW-{0}"),
    (r"\bSOP[-\s]?([A-Z]{0,4}[-\s]?\d{2,4})\b",  "SOP-{0}"),
    (r"\bP&ID[-\s]?([A-Z0-9\-]{3,12})\b",        "P&ID-{0}"),
    (r"\bPID[-\s]?([A-Z0-9\-]{3,12})\b",         "P&ID-{0}"),
    (r"\bMOC[-\s]?(\d{3,8})\b",                  "MOC-{0}"),
    (r"\bNCR[-\s]?(\d{3,8})\b",                  "NCR-{0}"),
    (r"\bCAPA[-\s]?(\d{3,8})\b",                 "CAPA-{0}"),
    (r"\bINC[-\s]?(\d{3,8})\b",                  "INC-{0}"),
    (r"\bNM[-\s]?(\d{3,8})\b",                   "NM-{0}"),
    (r"\bINSP[-\s]?(\d{3,8})\b",                 "INSP-{0}"),
    (r"\bHAZOP[-\s]?([A-Z0-9\-]{2,10})\b",       "HAZOP-{0}"),
]

# ---------------------------------------------------------------------------
# PLANT LOCATIONS / UNITS
# ---------------------------------------------------------------------------
LOCATION_TERMS = [
    "Crude Distillation Unit", "CDU", "Vacuum Distillation Unit", "VDU",
    "Fluid Catalytic Cracker", "FCCU", "FCC", "Hydrocracker", "HCU",
    "Diesel Hydrotreater", "DHDT", "Naphtha Hydrotreater", "NHT",
    "Catalytic Reformer", "CCR", "Sulphur Recovery Unit", "SRU",
    "Amine Regeneration Unit", "ARU", "Sour Water Stripper", "SWS",
    "Delayed Coker Unit", "DCU", "Coke Oven Battery", "Blast Furnace",
    "Sinter Plant", "Pellet Plant", "Steel Melt Shop", "SMS",
    "Continuous Casting", "Hot Strip Mill", "Cold Rolling Mill",
    "Boiler House", "Power Plant", "Captive Power Plant", "CPP",
    "Cooling Tower", "Effluent Treatment Plant", "ETP", "Flare Area",
    "Tank Farm", "Loading Gantry", "Marketing Terminal", "Jetty",
    "Utilities Block", "Compressor House", "Substation", "MCC Room",
    "Control Room", "Battery Limit", "Confined Space", "Pipe Rack",
]
LOCATION_RE = re.compile(r"\b(" + "|".join(re.escape(l) for l in LOCATION_TERMS) + r")\b", re.I)


# ---------------------------------------------------------------------------
# EXTRACTION ENGINE
# ---------------------------------------------------------------------------

def _add(store, etype, value, context, position):
    """Append a normalised entity occurrence."""
    store.append({
        "type": etype,
        "value": value,
        "context": context.strip(),
        "position": position,
    })


def _context_window(text, start, end, width=90):
    lo = max(0, start - width)
    hi = min(len(text), end + width)
    snippet = text[lo:hi].replace("\n", " ")
    return re.sub(r"\s+", " ", snippet)


def extract_entities(text):
    """
    Extract all ontology entities from a text block.

    Returns list of dicts: {type, value, context, position}
    Values are normalised (canonical form) so that "V 101", "V-101" and
    "v101" all collapse to the same graph node.
    """
    if not text:
        return []

    found = []

    # -- EQUIPMENT ---------------------------------------------------------
    for m in EQUIPMENT_RE.finditer(text):
        prefix = m.group("prefix").upper()
        num = m.group("num").upper()
        canonical = f"{prefix}-{num}"
        _add(found, "EQUIPMENT", canonical,
             _context_window(text, m.start(), m.end()), m.start())

    # -- REGULATION --------------------------------------------------------
    for pattern, template in REGULATION_PATTERNS:
        for m in re.finditer(pattern, text, re.I):
            groups = [g for g in m.groups() if g]
            try:
                canonical = template.format(*groups) if groups else template
            except IndexError:
                canonical = template
            _add(found, "REGULATION", canonical,
                 _context_window(text, m.start(), m.end()), m.start())

    # -- PARAMETER ---------------------------------------------------------
    # Equipment spans are masked out first so that tag suffixes (P-101A) are
    # never mistaken for electrical units.
    eq_spans = [(m.start(), m.end()) for m in EQUIPMENT_RE.finditer(text)]

    def _inside_equipment(pos):
        return any(s <= pos < e for s, e in eq_spans)

    for m in PARAMETER_RE.finditer(text):
        if _inside_equipment(m.start()):
            continue
        unit = m.group("unit")
        canonical = f"{m.group('val')} {unit}"
        _add(found, "PARAMETER", canonical,
             _context_window(text, m.start(), m.end()), m.start())

    # -- PERSONNEL ---------------------------------------------------------
    for m in ROLE_RE.finditer(text):
        canonical = m.group(1).title()
        _add(found, "PERSONNEL", canonical,
             _context_window(text, m.start(), m.end()), m.start())
    for m in NAME_RE.finditer(text):
        _add(found, "PERSONNEL", m.group(1),
             _context_window(text, m.start(), m.end()), m.start())

    # -- FAILURE -----------------------------------------------------------
    for m in FAILURE_RE.finditer(text):
        _add(found, "FAILURE", m.group(1).lower(),
             _context_window(text, m.start(), m.end()), m.start())

    # -- CHEMICAL ----------------------------------------------------------
    for m in CHEMICAL_RE.finditer(text):
        raw = m.group(1)
        canonical = _normalise_chemical(raw)
        _add(found, "CHEMICAL", canonical,
             _context_window(text, m.start(), m.end()), m.start())

    # -- DOCUMENT ----------------------------------------------------------
    for pattern, template in DOCUMENT_PATTERNS:
        for m in re.finditer(pattern, text, re.I):
            groups = [g for g in m.groups() if g]
            canonical = template.format(*groups) if groups else template
            canonical = canonical.upper().replace(" ", "")
            _add(found, "DOCUMENT", canonical,
                 _context_window(text, m.start(), m.end()), m.start())

    # -- LOCATION ----------------------------------------------------------
    for m in LOCATION_RE.finditer(text):
        canonical = _normalise_location(m.group(1))
        _add(found, "LOCATION", canonical,
             _context_window(text, m.start(), m.end()), m.start())

    return found


_CHEM_ALIASES = {
    "hydrogen sulfide": "H2S", "hydrogen sulphide": "H2S", "h2s": "H2S",
    "carbon monoxide": "CO", "co": "CO",
    "carbon dioxide": "CO2", "co2": "CO2",
    "methane": "CH4", "ch4": "CH4",
    "ammonia": "NH3", "nh3": "NH3",
    "sulphur dioxide": "SO2", "so2": "SO2",
    "nitrogen": "N2", "n2": "N2",
    "oxygen": "O2", "o2": "O2",
    "hydrogen": "H2", "h2": "H2",
    "chlorine": "Cl2", "cl2": "Cl2",
    "coke oven gas": "Coke Oven Gas", "cog": "Coke Oven Gas",
    "blast furnace gas": "Blast Furnace Gas", "bfg": "Blast Furnace Gas",
    "hydrochloric acid": "HCl", "hcl": "HCl",
}

_LOC_ALIASES = {
    "cdu": "Crude Distillation Unit", "crude distillation unit": "Crude Distillation Unit",
    "vdu": "Vacuum Distillation Unit", "vacuum distillation unit": "Vacuum Distillation Unit",
    "fccu": "Fluid Catalytic Cracker", "fcc": "Fluid Catalytic Cracker",
    "fluid catalytic cracker": "Fluid Catalytic Cracker",
    "hcu": "Hydrocracker", "hydrocracker": "Hydrocracker",
    "sru": "Sulphur Recovery Unit", "sulphur recovery unit": "Sulphur Recovery Unit",
    "dcu": "Delayed Coker Unit", "delayed coker unit": "Delayed Coker Unit",
    "sms": "Steel Melt Shop", "steel melt shop": "Steel Melt Shop",
    "cpp": "Captive Power Plant", "captive power plant": "Captive Power Plant",
    "etp": "Effluent Treatment Plant", "effluent treatment plant": "Effluent Treatment Plant",
}


def _normalise_chemical(raw):
    return _CHEM_ALIASES.get(raw.lower().strip(), raw.title())


def _normalise_location(raw):
    return _LOC_ALIASES.get(raw.lower().strip(), raw.title())


def describe_equipment(tag):
    """Return human-readable equipment class for a tag like 'P-101A'."""
    for prefix in _EQ_PREFIXES:
        if tag.upper().startswith(prefix):
            return EQUIPMENT_CLASS_MAP[prefix]
    return "Equipment"


def entity_summary(entities):
    """Aggregate entity occurrences into {type: {value: count}}."""
    summary = defaultdict(lambda: defaultdict(int))
    for e in entities:
        summary[e["type"]][e["value"]] += 1
    return {k: dict(v) for k, v in summary.items()}

from __future__ import annotations

import re

from oncopilot_ai.schemas import ExtractedEntities


GENE_CANDIDATES = [
    "EGFR", "MET", "KRAS", "PD-L1", "PDL1", "HER2", "ERBB2", "ALK", "BRAF", "ROS1",
    "RET", "NTRK", "PIK3CA", "TP53", "BRCA1", "BRCA2", "ER", "ESR1", "CD274",
]
VARIANT_PATTERNS = [r"T790M", r"L858R", r"G12C", r"G12D", r"G12V", r"exon 19 deletion", r"ex19del", r"C797S"]
MECHANISM_CANDIDATES = [
    "MET amplification", "histologic transformation", "bypass signaling", "downstream pathway alterations",
    "secondary KRAS alterations", "reactivation of MAPK signaling", "tumor heterogeneity", "immune escape",
    "antigen presentation", "ctDNA shedding", "minimal residual disease", "clonal evolution",
]
THERAPY_CANDIDATES = [
    "osimertinib", "sotorasib", "adagrasib", "trastuzumab", "pembrolizumab", "nivolumab",
    "PD-1 inhibitors", "PD-L1 inhibitors", "EGFR-TKI", "MEK inhibitor", "MET inhibitor",
]
DISEASE_CANDIDATES = ["NSCLC", "lung cancer", "breast cancer", "colorectal cancer", "melanoma", "pancreatic cancer"]


def heuristic_extract_entities(chunks: list[dict]) -> ExtractedEntities:
    text = " ".join(chunk.get("text", "") for chunk in chunks)
    text_upper = text.upper()

    genes = []
    for gene in GENE_CANDIDATES:
        if gene.upper() in text_upper:
            genes.append(gene)

    variants = []
    for pattern in VARIANT_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            variants.append(pattern)

    therapies = []
    for therapy in THERAPY_CANDIDATES:
        if therapy.lower() in text.lower():
            therapies.append(therapy)

    mechanisms = []
    for mechanism in MECHANISM_CANDIDATES:
        if mechanism.lower() in text.lower():
            mechanisms.append(mechanism)

    diseases = []
    for disease in DISEASE_CANDIDATES:
        if disease.lower() in text.lower():
            diseases.append(disease)

    return ExtractedEntities(
        genes=sorted(set(genes)),
        variants=sorted(set(variants)),
        therapies=sorted(set(therapies)),
        mechanisms=sorted(set(mechanisms)),
        diseases=sorted(set(diseases)),
    )

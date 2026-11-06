"""Verify the literal published program without reading target-cohort data."""
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
import argparse

HERE = Path(__file__).resolve().parent
LEAD = "whereas SPP1+ TAMs gene signature includes the following genes:"
SECTION = "Define C1QC+ TAMs, SPP1+ TAMs, and M1/M2 Gene Signatures"


def flatten(el):
    return " ".join("".join(el.itertext()).split())


def verify(data, lock, stored):
    if sha256(data).hexdigest() != lock["source_xml_sha256"]:
        raise ValueError("Source bytes differ from the pinned publisher XML.")
    root = ET.fromstring(data)
    sections = [sec for sec in root.findall(".//sec") if sec.find("title") is not None
                and flatten(sec.find("title")) == SECTION]
    if len(sections) != 1:
        raise ValueError("Expected exactly one signature definition section.")
    paragraphs = [flatten(el) for el in sections[0].findall("p") if LEAD in flatten(el)]
    if len(paragraphs) != 1:
        raise ValueError("Expected exactly one SPP1-positive TAM marker enumeration.")
    tail = paragraphs[0].split(LEAD,1)[1].strip()
    if not tail.endswith("."):
        raise ValueError("Unexpected end of signature paragraph.")
    symbols = tail[:-1].replace(", and ", ", ").split(", ")
    if len(symbols) != len(set(symbols)) or any(not re.fullmatch(r"[A-Z][A-Z0-9-]*",g) for g in symbols):
        raise ValueError("Expected distinct uppercase human gene symbols.")
    normalized = ("\n".join(symbols)+"\n").encode("ascii")
    if (symbols != lock["genes"] or len(symbols) != 15 or lock["anchor"] in symbols
            or normalized != stored or sha256(stored).hexdigest() != lock["gene_list_sha256"]):
        raise ValueError("Published symbols, frozen gene vector and lock do not match.")
    return symbols


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xml",type=Path,help="Publisher XML, if obtained separately.")
    p.add_argument("--fetch",action="store_true",help="Use publisher URL instead of bundled source.")
    args = p.parse_args()
    if args.fetch and args.xml:
        p.error("Choose either --fetch or --xml.")
    lock = json.loads((HERE/"signature_lock.json").read_text(encoding="utf-8"))
    if args.fetch:
        with urlopen(Request(lock["source_xml_url"],headers={"User-Agent":"PASE-source-audit/1.0"}), timeout=45) as resp:
            raw = resp.read()
    else:
        raw = (args.xml or HERE/"source"/"Li_2021_publisher.xml").read_bytes()
    genes = verify(raw,lock,(HERE/"spp1_tam_genes.txt").read_bytes())
    print(f"Verified {len(genes)} source markers; gene-list SHA-256 {lock['gene_list_sha256']}.")

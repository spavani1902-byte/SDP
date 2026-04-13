import pandas as pd
import time
import os

from .extractor import excel_to_bridge
from .parser import parse_excel_full
from .generator import update_mapping


def process_iqac(file_path):

    print("🚀 Starting IQAC Processing...")

    # ======================
    # STEP 1: EXTRACT → BRIDGE
    # ======================
    bridge_file = excel_to_bridge(file_path)
    print("✅ Bridge file created:", bridge_file)

    # ======================
    # STEP 2: PARSE
    # ======================
    parsed = parse_excel_full(bridge_file)
    print("✅ Parsed records:", len(parsed))

    if not parsed:
        raise Exception("No valid questions parsed. Check input format.")

    # ======================
    # STEP 3: GENERATE IQAC
    # ======================
    output_file = f"iqac_output_{int(time.time())}.xlsx"

    update_mapping(output_file, parsed)

    print("✅ IQAC Excel generated:", output_file)

    # ======================
    # STEP 4: LOAD FOR PREVIEW
    # ======================
    try:
        df = pd.read_excel(output_file)
    except Exception as e:
        raise Exception(f"Error reading generated IQAC file: {e}")

    # ======================
    # STEP 5: TABLE NAME
    # ======================
    table_name = "iqac_" + str(int(time.time()))

    print("🎯 IQAC Processing Completed")

    return parsed, table_name
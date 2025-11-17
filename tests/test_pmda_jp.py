import sys, pathlib
import pandas as pd
import numpy as np

# make the project root importable
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pmda_japan_build_db import (
    normalize_column_names,
    normalize_dates,
    deduplicate_with_flags
)

def test_mapping_basic():
    # two "法人番号" columns are typical in PMDA; pandas will auto-rename the 2nd to "法人番号.1"
    df = pd.DataFrame({
        "認証番号": ["123"],
        "販売名": ["Device A"],
        "一般的名称": ["Catheter"],
        "業者名_認証取得者": ["ABC株式会社"],
        "法人番号": ["1234567890123"],
        "業者名_選任外国製造医療機器等製造販売業者": ["XYZ Ltd."],
        "法人番号.1": ["9876543210000"],
        "認証機関コード": ["TUV01"],
        "認証年月日": ["2025/08/01"],
    })
    out = normalize_column_names(df)
    cols = set(out.columns)

    # expected core mappings exist
    assert {"certification_number","brand_name","generic_name",
            "certificate_holder_name","certification_body_code",
            "certification_date"}.issubset(cols)

    # first/second corporate-number columns mapped correctly
    assert "certificate_holder_corporate_number" in cols
    assert "designated_foreign_holder_corporate_number" in cols

def test_dates_to_iso():
    df = pd.DataFrame({
        "certification_date": ["2025/08/01", "01-Aug-2025", None],
        "succession_date": ["", "2024-12-31", "2025/1/5"],
    })
    out = normalize_dates(df, ["certification_date","succession_date"])

    assert out.loc[0, "certification_date"] == "2025-08-01"
    assert out.loc[1, "certification_date"] == "2025-08-01"
    assert pd.isna(out.loc[2, "certification_date"])

    assert out.loc[1, "succession_date"] == "2024-12-31"
    assert out.loc[2, "succession_date"] == "2025-01-05"

def test_deduplicate_with_flags():
    rows = [
        # Group A-1: one exact duplicate + one differing row -> keep all 3, flag=1
        {"certification_number":"A-1","brand_name":"Foo","certificate_holder_name":"Holder","generic_name":"Type1"},
        {"certification_number":"A-1","brand_name":"Foo","certificate_holder_name":"Holder","generic_name":"Type1"},
        {"certification_number":"A-1","brand_name":"Foo","certificate_holder_name":"Holder","generic_name":"Type2"},
        # Group B-2: single row -> keep, flag=0
        {"certification_number":"B-2","brand_name":"Bar","certificate_holder_name":"Other","generic_name":"TypeX"},
        # Group C-3: two exact duplicates only -> collapse to 1, flag=0
        {"certification_number":"C-3","brand_name":"Baz","certificate_holder_name":"Other2","generic_name":"TypeY"},
        {"certification_number":"C-3","brand_name":"Baz","certificate_holder_name":"Other2","generic_name":"TypeY"},
    ]
    df = pd.DataFrame(rows)
    out = deduplicate_with_flags(df)

    # Expect: A-1 -> 3 kept (ambiguous), B-2 -> 1 kept, C-3 -> 1 kept  => total 5
    assert len(out) == 5

    a1 = out[out["certification_number"]=="A-1"]
    assert len(a1) == 3
    assert set(a1["duplicate_flag"].astype(int)) == {1}

    b2 = out[out["certification_number"]=="B-2"]
    assert len(b2) == 1 and int(b2["duplicate_flag"].fillna(0).iloc[0]) == 0

    c3 = out[out["certification_number"]=="C-3"]
    assert len(c3) == 1 and int(c3["duplicate_flag"].fillna(0).iloc[0]) == 0

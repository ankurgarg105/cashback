from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; errors=[]
cards=pd.read_csv(ROOT/"data/cards.csv"); rules=pd.read_csv(ROOT/"data/card_rules.csv")
merchants=pd.read_csv(ROOT/"data/merchants.csv"); mcc=pd.read_csv(ROOT/"data/mcc_master.csv")
if cards.card_id.duplicated().any(): errors.append("Duplicate card_id")
if rules.card_id.isin(cards.card_id).eq(False).any(): errors.append("Unknown card_id in rules")
if merchants.merchant_id.duplicated().any(): errors.append("Duplicate merchant_id")
if mcc.mcc.astype(str).str.len().ne(4).any(): errors.append("MCC must be 4 digits")
if rules.rate.lt(0).any() or rules.cap.lt(0).any(): errors.append("Negative rate/cap")
if errors: raise SystemExit("VALIDATION FAILED: "+ "; ".join(errors))
print("Validation passed.")

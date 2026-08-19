import json
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Card Optimizer India", page_icon="💳", layout="centered")
BASE=Path(__file__).parent; DATA=BASE/"data"
cards=pd.read_csv(DATA/"cards.csv"); rules=pd.read_csv(DATA/"card_rules.csv")
merchants=pd.read_csv(DATA/"merchants.csv",dtype={"likely_mcc":str})
mccs=pd.read_csv(DATA/"mcc_master.csv",dtype={"mcc":str})
offers=pd.read_csv(DATA/"offers.csv")

try:
    from streamlit_local_storage import LocalStorage
    ls=LocalStorage()
except Exception: ls=None

def wallet_get():
    try:
        v=ls.getItem("card_optimizer_wallet") if ls else None
        return json.loads(v) if v else st.session_state.get("wallet",[])
    except Exception: return st.session_state.get("wallet",[])
def wallet_save(v):
    st.session_state["wallet"]=v
    try:
        if ls: ls.setItem("card_optimizer_wallet",json.dumps(v))
    except Exception: pass
if "wallet" not in st.session_state: st.session_state["wallet"]=wallet_get()

def norm(s): return "".join(c.lower() if c.isalnum() else " " for c in str(s)).strip()
def find_merchant(q):
    q=norm(q)
    return merchants[merchants.merchant_name.map(norm).str.contains(q,regex=False)] if q else merchants.iloc[0:0]
def get_rule(cid,typ,key):
    x=rules[(rules.card_id==cid)&(rules.rule_type==typ)&(rules.rule_key.astype(str)==str(key))]
    return x.iloc[0] if not x.empty else None
def calc(cid,amt,mid,mcc,ch):
    c=cards[cards.card_id==cid].iloc[0]; candidates=[]
    for typ,key,label in [("merchant",mid,"Direct merchant"),("channel",ch,"Channel"),("mcc",mcc,"MCC"),("mcc","0000","Fallback")]:
        if key:
            r=get_rule(cid,typ,key)
            if r is not None and r.channel in ("all",ch): candidates.append((r,label))
    if not candidates: return c,0,0,"No mapped benefit","Low"
    r,label=max(candidates,key=lambda x:float(x[0].rate))
    val=amt*float(r.rate)
    if float(r.cap)>0: val=min(val,float(r.cap))
    return c,val,float(r.rate),label,r.confidence

st.title("💳 Card Optimizer India")
st.caption("Your cards vs the wider card market")

with st.expander("⚙️ Database status"):
    st.write(f"Cards: **{len(cards)}**")
    st.write(f"Card rules: **{len(rules)}**")
    st.write(f"Merchants: **{len(merchants)}**")
    st.write(f"MCC records: **{len(mccs)}**")
    st.write(f"Offers: **{len(offers)}**")
    st.caption("Data is maintained in GitHub and can be refreshed by the automated workflow.")

st.header("💼 My Card Wallet")
opts=dict(zip(cards.card_id,cards.card_name))
wallet=st.multiselect("Cards you own",list(opts),default=[x for x in st.session_state["wallet"] if x in opts],format_func=lambda x:opts[x])
if st.button("💾 Save my cards"):
    wallet_save(wallet); st.success(f"{len(wallet)} card(s) saved locally.")
st.caption("No card number, CVV or bank login is stored.")

st.header("🛒 Transaction")
q=st.text_input("Merchant / brand",placeholder="Amazon, Swiggy, Zomato...")
matches=find_merchant(q); mid=None; mcc=""
if not matches.empty:
    name=st.selectbox("Matched merchant",matches.merchant_name.tolist())
    row=matches[matches.merchant_name==name].iloc[0]
    mid,mcc=row.merchant_id,str(row.likely_mcc)
    st.info(f"Likely MCC: **{mcc}** • confidence: **{row.confidence}**")
mcc=st.text_input("MCC (optional; actual statement MCC is best)",value=mcc,max_chars=4)
channel=st.selectbox("Transaction channel",["online","offline","partner_app"])
amount=st.number_input("Transaction amount (₹)",min_value=1.0,value=5000.0,step=500.0)

if st.button("🔎 COMPARE CARDS",type="primary"):
    if not wallet: st.warning("Save at least one card first."); st.stop()
    if not mcc.isdigit(): st.error("Select a merchant or enter a valid MCC."); st.stop()
    own=sorted([calc(x,amount,mid,mcc,channel) for x in wallet],key=lambda x:x[1],reverse=True)
    market=sorted([calc(x,amount,mid,mcc,channel) for x in cards.card_id],key=lambda x:x[1],reverse=True)
    best,mb=own[0],market[0]
    st.divider(); st.subheader("🟢 Best card in YOUR wallet")
    st.success(f"### {best[0].card_name}\n\nEstimated value: **₹{best[1]:,.2f}**")
    st.caption(f"Matched via {best[3]} • confidence {best[4]}")
    st.dataframe(pd.DataFrame([{"Card":x[0].card_name,"Value":f"₹{x[1]:,.2f}","Rate":f"{x[2]*100:.2f}%","Match":x[3],"Confidence":x[4]} for x in own]),hide_index=True,use_container_width=True)
    st.subheader("🔵 Best card in MARKET database")
    st.info(f"🏆 **{mb[0].card_name}** — ₹{mb[1]:,.2f}")
    gap=mb[1]-best[1]
    if mb[0].card_id not in wallet and gap>0.5: st.warning(f"Potential additional value: **₹{gap:,.2f}**")
    elif mb[0].card_id in wallet: st.success("You already own the market-best card in the current database.")
    else: st.success("No material market advantage found.")
    st.dataframe(pd.DataFrame([{"#":i+1,"Card":x[0].card_name,"Value":f"₹{x[1]:,.2f}","Rate":f"{x[2]*100:.2f}%","In wallet":"Yes" if x[0].card_id in wallet else "No","Match":x[3]} for i,x in enumerate(market[:10])]),hide_index=True,use_container_width=True)

with st.expander("Browse database"):
    st.dataframe(cards,hide_index=True,use_container_width=True)

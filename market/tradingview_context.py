"""Optional TradingView technical-analysis confirmation."""
import requests
URL='https://scanner.tradingview.com/global/scan'
PERIODS=('1','5','15','60','240','1D','1W','1M')
IND=('Recommend.Other','Recommend.All','Recommend.MA')
def get_ta(symbol_id,timeout=8):
    cols=[f'{i}|{p}' if p!='1D' else i for p in PERIODS for i in IND]
    try:
        r=requests.post(URL,json={'symbols':{'tickers':[symbol_id]},'columns':cols},headers={'User-Agent':'crypto-research-agent/1.0','Origin':'https://www.tradingview.com'},timeout=timeout); r.raise_for_status(); row=r.json().get('data',[{}])[0].get('d')
        if not row or len(row)!=len(cols): return None
        out={}
        for col,val in zip(cols,row):
            parts=col.split('|'); tf=parts[1] if len(parts)>1 else '1D'
            try: v=float(val)
            except (TypeError,ValueError): continue
            out.setdefault(tf,{})[parts[0].rsplit('.',1)[-1]]=round(v,4)
        return out
    except (requests.RequestException,ValueError,KeyError,IndexError,TypeError): return None

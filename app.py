import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from spc import imr, xbar_r, capability

st.set_page_config(page_title='SPC Studio | Sepp Sina', page_icon='📊', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp {font-family:Inter,sans-serif!important}
.stApp {background:radial-gradient(ellipse at 74% 0%,#172b41 0%,#0b1725 56%,#08111e 100%);color:#e9f0fa}
[data-testid="stAppViewContainer"] {background:transparent}
[data-testid="stHeader"] {background:rgba(8,17,30,.76)}
[data-testid="stSidebar"] {background:linear-gradient(160deg,#15273c,#0b1728 68%);border-right:1px solid #30455c}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {color:#f4c566}
[data-testid="stMetric"] {background:linear-gradient(145deg,#1b344a,#102233);border:1px solid #35516b;border-radius:14px;padding:15px 18px;box-shadow:0 8px 22px rgba(0,0,0,.14)}
[data-testid="stMetricLabel"] {color:#adc2d6}
[data-testid="stMetricValue"] {color:#f6f9fc;font-size:clamp(1.1rem,1.6vw,1.65rem)}
h1,h2,h3 {letter-spacing:-.025em}
h1 {font-size:1.85rem!important}
.block-container {padding-top:1.15rem;max-width:1650px}
div.stButton>button[kind="primary"],div.stDownloadButton>button[kind="primary"] {background:linear-gradient(135deg,#f5c65e,#e9a934);color:#132034;border:1px solid #ffdc82;font-weight:700;box-shadow:0 4px 16px rgba(242,185,75,.18)}
div.stButton>button,div.stDownloadButton>button {border-color:#3a5872;border-radius:10px;transition:all .18s ease}
div.stButton>button:hover,div.stDownloadButton>button:hover {border-color:#f2bd58;color:#ffda8b}
[data-testid="stFileUploader"] {border:1px solid #35506a;border-radius:14px;background:rgba(17,35,54,.48)}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {background-color:#102235;border-color:#3a5872;border-radius:9px}
[data-testid="stTabs"] [role="tablist"] {gap:5px;border:1px solid #304a63;border-radius:11px;background:rgba(13,29,45,.8);padding:4px}
[data-testid="stTabs"] button[role="tab"] {border-radius:8px;color:#c2d0df}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {background:linear-gradient(135deg,#f4c65f,#e8aa38);color:#172335}
[data-testid="stDataFrame"],[data-testid="stTable"] {border:1px solid #304a63;border-radius:12px;overflow:hidden}
[data-testid="stExpander"] {border-color:#304a63;border-radius:11px}
.hero {display:flex;align-items:center;gap:14px;padding:4px 0 18px;border-bottom:1px solid rgba(81,112,139,.32);margin-bottom:16px}
.hero-mark {display:grid;place-items:center;flex:0 0 48px;height:48px;border:1px solid #dcae4e;border-radius:14px;background:linear-gradient(145deg,#243d50,#142536);color:#f4c566;font-size:1.55rem;box-shadow:0 0 22px rgba(242,185,75,.12)}
.hero-copy {flex:1}
.hero h1 {margin:.12rem 0!important}
.eyebrow{color:#f0bd5b;font-size:.76rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase}
.muted{color:#a6b9cc}
.user-chip {display:flex;align-items:center;gap:9px;padding:7px 12px 7px 7px;border:1px solid #304a63;border-radius:12px;background:rgba(15,31,48,.85);color:#e6edf6;font-weight:600;white-space:nowrap}
.avatar {display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#294f78;color:#f8d47e;font-size:.8rem;font-weight:800}
.status {padding:12px 16px;border-radius:12px;background:linear-gradient(100deg,#123b34,#15334a);border:1px solid #31725f;margin:12px 0;color:#d9f4e9}
.brand{color:#f4c566;font-weight:800;letter-spacing:.02em}
@media (max-width:720px) {.hero {flex-wrap:wrap}.user-chip {margin-left:62px}.hero h1 {font-size:1.45rem!important}}
</style>''', unsafe_allow_html=True)

@st.cache_data
def demo():
    rng=np.random.default_rng(42)
    vals=rng.normal(24.98,.047,(30,5))
    vals[26,:]+=0.18
    rows=[]
    for i in range(30):
        for j in range(5):
            rows.append(dict(value=vals[i,j],subgroup=i+1,shift=['A','B','C'][i%3],cavity=f'C{j+1}',station='Injection 01',date=(pd.Timestamp('2026-10-01')+pd.Timedelta(days=i)).date()))
    return pd.DataFrame(rows)

def parse_upload(upload):
    if upload.name.lower().endswith('.csv'):
        raw=pd.read_csv(upload)
    else:
        raw=pd.read_excel(upload)
    raw.columns=[str(c).strip().lower().replace(' ','_') for c in raw.columns]
    for alias in ('value','measurement','diameter','dimension','reading','result'):
        if alias in raw.columns:
            raw=raw.rename(columns={alias:'value'});break
    if 'value' not in raw:
        raise ValueError('A numeric column named value or measurement is required.')
    raw['value']=pd.to_numeric(raw['value'],errors='coerce')
    raw=raw.dropna(subset=['value']).copy()
    if raw.empty: raise ValueError('No valid numeric measurements found.')
    return raw

def chart(values,cl,ucl,lcl,title,flags=None):
    values=np.asarray(values); x=np.arange(1,len(values)+1)
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=x,y=values,mode='lines+markers',name='Measured',line=dict(color='#56c8ff',width=2),marker=dict(size=6,color='#78d5ff')))
    for y,label,color,dash in [(ucl,'UCL','#f5756c','dash'),(cl,'CL','#4cce99','solid'),(lcl,'LCL','#f5756c','dash')]:
        fig.add_hline(y=y,line_color=color,line_dash=dash,annotation_text=f'{label} {y:.4f}',annotation_position='top right')
    if flags is not None and len(flags):
        fig.add_trace(go.Scatter(x=x[flags],y=values[flags],mode='markers',name='Beyond limits',marker=dict(size=13,color='#ff735e',symbol='circle-open',line=dict(width=3,color='#ff735e'))))
    fig.update_layout(title=title,height=300,margin=dict(l=15,r=20,t=55,b=20),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#d9e6f5'),xaxis=dict(title='Observation / subgroup',gridcolor='#273d53'),yaxis=dict(gridcolor='#273d53'),legend=dict(orientation='h',y=1.15),hovermode='x unified')
    return fig

def pdf_report(metrics,analysis,lsl,usl,source):
    buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=letter)
    c.setFont('Helvetica-Bold',18);c.drawString(50,745,'Process Capability & SPC Studio')
    c.setFont('Helvetica',10);c.drawString(50,723,'Prepared by Sepp Sina | Engineering Analysis Report')
    lines=[f'Dataset: {source}',f'Chart: {analysis["kind"]}',f'Samples: {metrics["n"]}',f'LSL / USL: {lsl:.4f} / {usl:.4f}',f'Mean: {metrics["mean"]:.5f}',f'Within sigma: {metrics["within_sigma"]:.5f}',f'Overall sigma: {metrics["overall_sigma"]:.5f}',f'Cp: {metrics["cp"]:.3f}   Cpk: {metrics["cpk"]:.3f}',f'Pp: {metrics["pp"]:.3f}   Ppk: {metrics["ppk"]:.3f}',f'Chart signals beyond limits: X={len(analysis["x_ooc"])} / R={len(analysis["r_ooc"])}',f'Outside specification: {metrics["below"]+metrics["above"]} samples']
    c.setFont('Helvetica',11)
    for i,line in enumerate(lines):c.drawString(50,680-i*28,line)
    c.setFont('Helvetica-Oblique',9);c.drawString(50,295,'Control limits are estimated from the selected dataset, not a frozen Phase-II baseline.')
    c.drawString(50,279,'Check stability and measurement system suitability before capability conclusions.')
    c.save();buf.seek(0);return buf.getvalue()

with st.sidebar:
    st.markdown('## ◈ SPC Studio')
    st.caption('Industrial quality intelligence')
    st.markdown('**Sepp Sina**')
    st.divider()
    st.markdown('#### Data & Setup')
    uploaded=st.file_uploader('Import measurements',type=['csv','xlsx'],help='Column value is required; subgroup, shift, cavity, station and date are optional.')
    st.caption('No file? A labeled synthetic demonstration dataset is loaded.')
    st.markdown('#### Specifications')
    lsl=st.number_input('Lower spec limit (LSL)',value=24.70,format='%.4f')
    usl=st.number_input('Upper spec limit (USL)',value=25.30,format='%.4f')
    requested=st.selectbox('SPC method',['Xbar-R','I-MR'])
    st.divider()
    st.caption('Sepp Sina • Version 1.0')

try:
    frame=parse_upload(uploaded) if uploaded else demo()
    source=uploaded.name if uploaded else 'Synthetic demo data (not production)'
except Exception as exc:
    st.error(f'Import error: {exc}');st.stop()

st.markdown('<div class="hero"><div class="hero-mark">◈</div><div class="hero-copy"><div class="eyebrow">Quality engineering workspace</div><h1>Process Capability & SPC Studio</h1><div class="muted">Statistical process control · Process capability · Manufacturing insights</div></div><div class="user-chip"><span class="avatar">SS</span><span>Sepp Sina</span></div></div>',unsafe_allow_html=True)
if not uploaded:st.info('DEMO MODE — Synthetic example measurements. Upload your own CSV/XLSX for analysis.',icon='🧪')
filter_cols=st.columns(4)
for col,key in zip(filter_cols,['shift','cavity','station','date']):
    if key in frame:
        options=sorted(frame[key].dropna().astype(str).unique().tolist())
        with col:
            selected=st.selectbox(key.title(),['All']+options,key=f'filter_{key}')
        if selected!='All':frame=frame[frame[key].astype(str)==selected].copy()
if lsl>=usl:st.error('LSL must be lower than USL.');st.stop()
if len(frame)<3:st.warning('At least 3 observations are needed after filtering.');st.stop()
try:
    analysis=xbar_r(frame) if requested=='Xbar-R' else imr(frame['value'].to_numpy())
    metrics=capability(frame['value'].to_numpy(),lsl,usl,analysis['within_sigma'])
except ValueError as exc:
    st.error(str(exc));st.info('Try I-MR for individual observations or remove filters that break complete equal-size subgroups.');st.stop()

signals=len(analysis['x_ooc'])+len(analysis['r_ooc'])
status='SIGNALS DETECTED' if signals else 'NO LIMIT VIOLATIONS'
cols=st.columns(6)
for col,(label,val) in zip(cols,[('Status','Signals' if signals else 'In control'),('Cp',f'{metrics["cp"]:.2f}'),('Cpk',f'{metrics["cpk"]:.2f}'),('Mean',f'{metrics["mean"]:.3f}'),('Within σ',f'{metrics["within_sigma"]:.3f}'),('Samples',str(metrics['n']))]):
    col.metric(label,val)
st.markdown(f'<div class="status">{"⚠️" if signals else "✓"} <b>{status}</b> — {signals} point(s) beyond estimated 3σ control limits. Capability indices do not establish stability.</div>',unsafe_allow_html=True)

t1,t2,t3,t4=st.tabs(['📈 Control Charts','🎯 Capability','▥ Distribution','⚙ Comparisons & Reports'])
with t1:
    st.plotly_chart(chart(analysis['x'],analysis['x_cl'],analysis['x_ucl'],analysis['x_lcl'],'X̄ chart — subgroup means' if requested=='Xbar-R' else 'Individuals chart',analysis['x_ooc']),use_container_width=True)
    st.plotly_chart(chart(analysis['r'],analysis['r_cl'],analysis['r_ucl'],analysis['r_lcl'],'R chart — subgroup ranges' if requested=='Xbar-R' else 'Moving range chart',analysis['r_ooc']),use_container_width=True)
    st.caption('Rule implemented: points beyond three-sigma control limits. Run rules, trend tests, and frozen baseline limits are planned enhancements.')
with t2:
    c1,c2,c3,c4=st.columns(4)
    for col,k in zip((c1,c2,c3,c4),('cp','cpk','pp','ppk')):col.metric(k.upper() if k in ('cp','pp') else k.capitalize(),f'{metrics[k]:.3f}')
    st.write(f'**Observed out-of-specification:** {metrics["below"]} below LSL, {metrics["above"]} above USL.')
    if signals:st.warning('Process instability detected. Investigate special causes before interpreting capability as a reliable long-term prediction.')
    elif metrics['cpk']<1.33:st.warning('Cpk is below a commonly used 1.33 reference threshold; confirm your customer-specific acceptance criteria.')
    else:st.success('No 3σ limit violations detected and Cpk ≥ 1.33. Additional stability checks and customer requirements still apply.')
with t3:
    vals=frame['value'].to_numpy(dtype=float)
    fig=go.Figure()
    fig.add_trace(go.Histogram(x=vals,nbinsx=min(35,max(8,int(np.sqrt(len(vals))))),name='Observed',marker_color='#57b9e8',opacity=.8,histnorm='probability density'))
    if metrics['overall_sigma']>0:
        xs=np.linspace(min(vals.min(),lsl),max(vals.max(),usl),250)
        fig.add_trace(go.Scatter(x=xs,y=norm.pdf(xs,metrics['mean'],metrics['overall_sigma']),name='Normal reference',line=dict(color='#f2bd58',width=3)))
    for limit,label in [(lsl,'LSL'),(usl,'USL')]:fig.add_vline(x=limit,line_color='#ff746c',line_dash='dash',annotation_text=label)
    fig.update_layout(height=420,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',title='Measurement distribution',xaxis_title='Measured value',yaxis_title='Density')
    st.plotly_chart(fig,use_container_width=True)
    st.caption('Normal curve is a visual reference, not a normality test. Validate distributional assumptions before extrapolating defect rates.')
with t4:
    st.subheader('Compare manufacturing segments')
    dims=[c for c in ('shift','cavity','station') if c in frame]
    if dims:
        dim=st.selectbox('Compare by',dims)
        summary=frame.groupby(dim)['value'].agg(['count','mean','std','min','max']).reset_index()
        st.dataframe(summary,use_container_width=True,hide_index=True)
        fig=go.Figure()
        for name,g in frame.groupby(dim):fig.add_trace(go.Box(y=g['value'],name=str(name),boxpoints='outliers'))
        fig.update_layout(height=380,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',yaxis_title='Measurement')
        st.plotly_chart(fig,use_container_width=True)
    else:st.info('Add shift, cavity, or station columns to compare segments.')
    st.subheader('Export engineering results')
    st.download_button('⬇ Download PDF summary',data=pdf_report(metrics,analysis,lsl,usl,source),file_name='spc_quality_report.pdf',mime='application/pdf',type='primary')
    st.download_button('⬇ Download filtered measurements (CSV)',data=frame.to_csv(index=False),file_name='spc_filtered_data.csv',mime='text/csv')
    with st.expander('Data preview'):st.dataframe(frame.head(100),use_container_width=True)

st.divider()
st.caption('Sepp Sina  •  SPC Studio v1.0  •  Engineering decisions require validated measurement systems and appropriate control plans.')

"""Build the self-contained interactive sales dashboard from project CSVs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


orders = load_csv(ROOT / "Data" / "facts" / "fact_orders.csv")
products = {row["product_id"]: row for row in load_csv(ROOT / "Data" / "dimensions" / "dim_product.csv")}
regions = {row["region_id"]: row for row in load_csv(ROOT / "Data" / "regions_raw.csv")}

records = []
customers = {}
months = {}
region_names = sorted({value.get("region", "Unassigned") for value in regions.values()})
categories = sorted({value.get("expected_category", "Unassigned").strip() or "Unassigned" for value in products.values()})
product_ids = sorted(products)
region_index = {value: i for i, value in enumerate(region_names)}
category_index = {value: i for i, value in enumerate(categories)}
product_index = {value: i for i, value in enumerate(product_ids)}
for row in orders:
    if row["customer_id"] and row["customer_id"] not in customers:
        customers[row["customer_id"]] = len(customers)
    if len(row["order_date"]) >= 7 and row["order_date"][:7] not in months:
        months[row["order_date"][:7]] = len(months)

for row in orders:
    product = products.get(row["product_id"], {})
    region = regions.get(row["region_id"], {})
    date = row["order_date"]
    customer = row["customer_id"]
    month = date[:7] if len(date) >= 7 else "Unknown"
    region_name = region.get("region", "Unassigned")
    category = product.get("expected_category", "Unassigned").strip() or "Unassigned"
    pid = row["product_id"] if row["product_id"] in product_index else ""
    records.append(
        [customers.get(customer, -1), months.get(month, -1), region_index.get(region_name, -1),
         category_index.get(category, -1), product_index.get(pid, -1),
         round(float(row["sales_amount"] or 0), 2), round(float(row["profit"] or 0), 2)]
    )

data = json.dumps(
    [records, list(customers), list(months), region_names, categories,
     [[pid, products[pid].get("product_name", "Unassigned product")] for pid in product_ids]],
    separators=(",", ":"), ensure_ascii=False,
)
template = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sales performance dashboard</title>
<style>
:root{color-scheme:dark;--bg:#0c1018;--panel:#121925;--panel2:#171f2d;--line:#263247;--text:#edf2fa;--muted:#8f9db2;--cyan:#67d6c0;--blue:#78aaff;--orange:#ffb86b;--red:#ff7c83;--radius:16px;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 10% -8%,#1b3041 0,transparent 35%),var(--bg);color:var(--text);font-size:14px}.wrap{max-width:1440px;margin:auto;padding:32px 36px 48px}.top{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:24px}.eyebrow{color:var(--cyan);font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}.title{font-size:30px;letter-spacing:-.04em;margin:8px 0 6px}.subtitle{margin:0;color:var(--muted)}.filters{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end}.filter{display:grid;gap:5px;color:var(--muted);font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase}.filter select{min-width:132px;background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:9px;padding:10px 34px 10px 12px;font:inherit;font-size:13px;text-transform:none;letter-spacing:0;outline:none}.filter select:focus{border-color:var(--cyan)}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}.kpi,.panel{background:linear-gradient(145deg,rgba(24,34,49,.96),rgba(17,24,36,.96));border:1px solid rgba(91,111,141,.22);border-radius:var(--radius);box-shadow:0 12px 36px #0002}.kpi{padding:18px 20px;min-height:116px}.kpi-label{color:var(--muted);font-size:12px}.kpi-value{font-size:27px;font-weight:650;letter-spacing:-.035em;margin:10px 0 5px;font-variant-numeric:tabular-nums}.kpi-note{color:var(--muted);font-size:11px}.layout{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(320px,1fr);gap:16px}.panel{padding:19px 20px;min-width:0}.panel.wide{grid-column:1/-1}.panel-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:14px}.panel h2{font-size:14px;margin:0;font-weight:620}.panel-sub{font-size:11px;color:var(--muted);margin-top:5px}.legend{display:flex;gap:14px;flex-wrap:wrap;color:var(--muted);font-size:11px}.legend span{display:flex;align-items:center;gap:6px}.dot{width:8px;height:8px;border-radius:50%;background:var(--cyan)}.dot.orange{background:var(--orange)}.chart{width:100%;height:260px;display:block;overflow:visible}.chart text{fill:var(--muted);font-size:10px;font-family:inherit}.chart .grid{stroke:var(--line);stroke-width:1}.chart .area{fill:url(#areaFill)}.chart .sales-line{fill:none;stroke:var(--cyan);stroke-width:2.4}.chart .profit-line{fill:none;stroke:var(--orange);stroke-width:2.1}.chart .bar{fill:var(--blue)}.chart .bar.profit{fill:var(--orange)}.chart .bar.category{fill:var(--cyan)}.chart .point{stroke:var(--panel);stroke-width:2}.chart .hover{fill:transparent;cursor:crosshair}.chart .focus-line{stroke:#98a7bd;stroke-dasharray:3 4;opacity:.65}.tooltip{position:fixed;z-index:5;pointer-events:none;background:#222d3e;border:1px solid #36455d;border-radius:8px;padding:9px 11px;font-size:11px;line-height:1.6;box-shadow:0 8px 24px #0005;display:none}.tip-muted{color:#aab7c9}.bars{display:grid;gap:13px}.bar-row{display:grid;grid-template-columns:minmax(92px,1fr) minmax(80px,2fr) auto;gap:10px;align-items:center;font-size:12px}.bar-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#dce4ef}.track{height:8px;background:#222d3d;border-radius:10px;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,#58bcae,#7ce0c8);border-radius:10px}.bar-val{font-variant-numeric:tabular-nums;color:#b9c5d5;font-size:11px;text-align:right}.rank{color:var(--muted);width:20px}.product-name{display:flex;gap:8px;align-items:center}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:12px}th{text-align:right;color:var(--muted);font-size:10px;letter-spacing:.06em;text-transform:uppercase;font-weight:600;padding:9px 8px;border-bottom:1px solid var(--line)}td{text-align:right;padding:11px 8px;border-bottom:1px solid rgba(38,50,71,.7);font-variant-numeric:tabular-nums}th:first-child,td:first-child{text-align:left}.pname{display:flex;align-items:center;gap:9px;min-width:150px}.rankno{color:var(--muted);font-size:10px}.pill{display:inline-block;color:#bceee4;background:#1a3939;border:1px solid #24514d;border-radius:99px;padding:3px 7px;font-size:10px}.empty{height:200px;display:grid;place-items:center;color:var(--muted)}.foot{margin-top:15px;color:#728199;font-size:10px}.positive{color:var(--cyan)}.negative{color:var(--red)}
@media(max-width:900px){.wrap{padding:24px 20px}.top{display:block}.filters{justify-content:flex-start;margin-top:18px}.kpis{grid-template-columns:repeat(2,1fr)}.layout{grid-template-columns:1fr}.panel.wide{grid-column:auto}}
@media(max-width:520px){.wrap{padding:20px 14px}.title{font-size:25px}.kpi{padding:14px;min-height:103px}.kpi-value{font-size:22px}.filters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.filter select{min-width:0;width:100%;padding:10px 5px;font-size:12px}.panel{padding:16px 13px}.bar-row{grid-template-columns:minmax(70px,1fr) minmax(55px,1.4fr) auto;gap:7px}.chart{height:240px}}
</style></head>
<body><main class="wrap">
<header class="top"><div><div class="eyebrow">Commerce intelligence</div><h1 class="title">Sales performance</h1><p class="subtitle">Revenue, profitability and product mix at a glance</p></div>
<div class="filters" aria-label="Dashboard filters"><label class="filter">Year<select id="year"><option value="all">All years</option></select></label><label class="filter">Region<select id="region"><option value="all">All regions</option></select></label><label class="filter">Category<select id="category"><option value="all">All categories</option></select></label></div></header>
<section class="kpis" aria-live="polite"><article class="kpi"><div class="kpi-label">Revenue</div><div class="kpi-value" id="revenue">—</div><div class="kpi-note">Total sales amount</div></article><article class="kpi"><div class="kpi-label">Profit</div><div class="kpi-value" id="profit">—</div><div class="kpi-note" id="margin">Profit margin —</div></article><article class="kpi"><div class="kpi-label">Orders</div><div class="kpi-value" id="orders">—</div><div class="kpi-note">Distinct order IDs</div></article><article class="kpi"><div class="kpi-label">Customers</div><div class="kpi-value" id="customers">—</div><div class="kpi-note">Distinct customer IDs</div></article></section>
<section class="layout"><article class="panel"><div class="panel-head"><div><h2>Monthly sales trend</h2><div class="panel-sub">Revenue and profit over time</div></div><div class="legend"><span><i class="dot"></i>Revenue</span><span><i class="dot orange"></i>Profit</span></div></div><svg id="trend" class="chart" role="img" aria-label="Monthly revenue and profit trend"></svg></article>
<article class="panel"><div class="panel-head"><div><h2>Revenue by category</h2><div class="panel-sub">Ranked by sales amount</div></div></div><div id="categories" class="bars"></div></article>
<article class="panel"><div class="panel-head"><div><h2>Profit by region</h2><div class="panel-sub">Ranked by profit contribution</div></div></div><div id="regions" class="bars"></div></article>
<article class="panel"><div class="panel-head"><div><h2>Top products</h2><div class="panel-sub">Highest revenue in current selection</div></div></div><div class="table-wrap"><table><thead><tr><th>Product</th><th>Revenue</th><th>Profit</th><th>Margin</th></tr></thead><tbody id="products"></tbody></table></div></article>
</section><div class="foot">Source: project order facts and product/region dimensions. Returns are included as recorded; unknown dates are included in totals but not the monthly trend.</div></main><div class="tooltip" id="tooltip" role="tooltip"></div>
<script>
const [RAW, CUSTOMER_KEYS, MONTH_KEYS, REGION_KEYS, CATEGORY_KEYS, PRODUCT_KEYS] = __DATA__;
const DATA = RAW.map(r=>{const month=r[1]<0?'Unknown':MONTH_KEYS[r[1]];return {customer:r[0],month,year:month==='Unknown'?'Unknown':month.slice(0,4),region:REGION_KEYS[r[2]]||'Unassigned',category:CATEGORY_KEYS[r[3]]||'Unassigned',product:r[4]<0?'Unassigned':PRODUCT_KEYS[r[4]][0],name:r[4]<0?'Unassigned product':PRODUCT_KEYS[r[4]][1],sales:r[5],profit:r[6]}});
const $ = id => document.getElementById(id);
const money = n => new Intl.NumberFormat('en-IN',{maximumFractionDigits:0}).format(n);
const exact = n => new Intl.NumberFormat('en-IN',{maximumFractionDigits:2,minimumFractionDigits:2}).format(n);
const uniq = a => [...new Set(a)].sort((x,y)=>x.localeCompare(y,undefined,{numeric:true}));
for (const [id, vals] of [['year',uniq(DATA.map(d=>d.year).filter(v=>v!=='Unknown'))],['region',uniq(DATA.map(d=>d.region))],['category',uniq(DATA.map(d=>d.category))]]) for(const v of vals){const o=document.createElement('option');o.value=v;o.textContent=v;$ (id).append(o)}
['year','region','category'].forEach(id=>$(id).addEventListener('change',render));
function filtered(){const y=$('year').value,r=$('region').value,c=$('category').value;return DATA.filter(d=>(y==='all'||d.year===y)&&(r==='all'||d.region===r)&&(c==='all'||d.category===c))}
function aggregate(rows,key){const m=new Map();for(const d of rows){const k=key(d);if(!m.has(k))m.set(k,{key:k,revenue:0,profit:0,orders:0,customers:new Set(),count:0});const a=m.get(k);a.revenue+=d.sales;a.profit+=d.profit;a.orders++;if(d.customer>=0)a.customers.add(d.customer);a.count++}return [...m.values()]}
function render(){const rows=filtered(),rev=rows.reduce((a,d)=>a+d.sales,0),prof=rows.reduce((a,d)=>a+d.profit,0),customers=new Set(rows.map(d=>d.customer).filter(v=>v>=0));$('revenue').textContent=money(rev);$('profit').textContent=money(prof);$('orders').textContent=money(rows.length);$('customers').textContent=money(customers.size);$('margin').textContent=`Profit margin ${rev?(prof/rev*100).toFixed(1):'0.0'}%`;
const months=aggregate(rows,d=>d.month).filter(a=>a.key!=='Unknown').sort((a,b)=>a.key.localeCompare(b.key));drawTrend(months);drawBars('categories',aggregate(rows,d=>d.category).sort((a,b)=>b.revenue-a.revenue),'revenue',false);drawBars('regions',aggregate(rows,d=>d.region).sort((a,b)=>b.profit-a.profit),'profit',true);drawProducts(rows)}
function drawBars(id,items,field,isProfit){const root=$(id);root.innerHTML='';if(!items.length){root.innerHTML='<div class="empty">No data for this selection</div>';return}const max=Math.max(...items.map(x=>Math.max(0,x[field])));for(const a of items){const row=document.createElement('div');row.className='bar-row';const nm=document.createElement('div');nm.className='bar-name';nm.textContent=a.key;nm.title=a.key;const track=document.createElement('div');track.className='track';const fill=document.createElement('div');fill.className='fill';if(isProfit)fill.style.background='linear-gradient(90deg,#e79c54,#ffc37f)';fill.style.width=`${max?Math.max(0,a[field])/max*100:0}%`;track.append(fill);const val=document.createElement('div');val.className='bar-val';val.textContent=money(a[field]);row.append(nm,track,val);root.append(row)}}
function drawProducts(rows){const items=aggregate(rows,d=>d.product).map(a=>{const sample=rows.find(d=>d.product===a.key);return {...a,name:sample?.name||a.key}}).sort((a,b)=>b.revenue-a.revenue).slice(0,10),body=$('products');body.innerHTML='';if(!items.length){body.innerHTML='<tr><td colspan="4" class="empty">No data for this selection</td></tr>';return}items.forEach((a,i)=>{const tr=document.createElement('tr');const margin=a.revenue?a.profit/a.revenue*100:0;tr.innerHTML=`<td><div class="pname"><span class="rankno">${String(i+1).padStart(2,'0')}</span><span>${escapeHtml(a.name)}</span></div></td><td>${money(a.revenue)}</td><td>${money(a.profit)}</td><td><span class="pill">${margin.toFixed(1)}%</span></td>`;body.append(tr)})}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function drawTrend(items){const svg=$('trend'),W=Math.max(320,svg.clientWidth||620),H=260,L=48,R=12,T=10,B=35,w=W-L-R,h=H-T-B;svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.innerHTML='';if(!items.length){svg.innerHTML=`<text x="${W/2}" y="${H/2}" text-anchor="middle">No dated orders for this selection</text>`;return}const max=Math.max(1,...items.map(a=>a.revenue)),scaleY=v=>T+h-(v/max*h),scaleX=i=>L+(items.length===1?w/2:i*w/(items.length-1));let out='<defs><linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#67d6c0" stop-opacity=".22"/><stop offset="1" stop-color="#67d6c0" stop-opacity="0"/></linearGradient></defs>';for(let i=0;i<4;i++){const y=T+h*i/3,val=max*(1-i/3);out+=`<line class="grid" x1="${L}" y1="${y}" x2="${W-R}" y2="${y}"/><text x="${L-7}" y="${y+3}" text-anchor="end">${money(val)}</text>`}const pts=items.map((a,i)=>[scaleX(i),scaleY(a.revenue)]),line=pts.map((p,i)=>`${i?'L':'M'}${p[0]},${p[1]}`).join(' '),area=`${line} L${pts.at(-1)[0]},${T+h} L${pts[0][0]},${T+h} Z`;out+=`<path class="area" d="${area}"/><path class="sales-line" d="${line}"/>`;const ppts=items.map((a,i)=>[scaleX(i),scaleY(a.profit)]);out+=`<path class="profit-line" d="${ppts.map((p,i)=>`${i?'L':'M'}${p[0]},${p[1]}`).join(' ')}"/>`;const step=Math.max(1,Math.ceil(items.length/7));items.forEach((a,i)=>{if(i%step===0||i===items.length-1)out+=`<text x="${scaleX(i)}" y="${H-10}" text-anchor="middle">${a.key.slice(2)}</text>`;out+=`<circle class="point" cx="${scaleX(i)}" cy="${scaleY(a.revenue)}" r="3.5" fill="#67d6c0"/><circle class="point" cx="${scaleX(i)}" cy="${scaleY(a.profit)}" r="3" fill="#ffb86b"/>`});out+=`<line class="focus-line" id="focus" y1="${T}" y2="${T+h}" style="display:none"/><rect class="hover" x="${L}" y="${T}" width="${w}" height="${h}" id="hit"/>`;svg.innerHTML=out;const hit=svg.querySelector('#hit'),focus=svg.querySelector('#focus'),tip=$('tooltip');hit.addEventListener('mousemove',e=>{const box=svg.getBoundingClientRect(),x=(e.clientX-box.left)*W/box.width,idx=Math.max(0,Math.min(items.length-1,Math.round((x-L)/w*(items.length-1)))),a=items[idx];focus.setAttribute('x1',scaleX(idx));focus.setAttribute('x2',scaleX(idx));focus.style.display='';tip.innerHTML=`<strong>${a.key}</strong><br>Revenue: ${exact(a.revenue)}<br>Profit: ${exact(a.profit)}<br><span class="tip-muted">${a.orders.toLocaleString()} orders</span>`;tip.style.display='block';tip.style.left=`${Math.min(e.clientX+12,innerWidth-190)}px`;tip.style.top=`${Math.max(10,e.clientY-50)}px`});hit.addEventListener('mouseleave',()=>{focus.style.display='none';tip.style.display='none'})}
render();new ResizeObserver(()=>drawTrend(aggregate(filtered(),d=>d.month).filter(a=>a.key!=='Unknown').sort((a,b)=>a.key.localeCompare(b.key)))).observe($('trend'));
</script></body></html>'''

output = ROOT / "dashboard.html"
output.write_text(template.replace("__DATA__", data), encoding="utf-8")
print(f"Wrote {output} ({output.stat().st_size:,} bytes, {len(records):,} order rows)")

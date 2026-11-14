/* Lightweight responsive traffic trend chart. No external analytics SDK.
 * Data comes exclusively from the owner-authorized Supabase RPC.
 */
const NS='http://www.w3.org/2000/svg';
const createSvg=(name,attrs={},label)=>{
  const el=document.createElementNS(NS,name);
  for(const [key,value] of Object.entries(attrs))el.setAttribute(key,String(value));
  if(label!==undefined)el.textContent=label;
  return el;
};
const numberValue=value=>Math.max(0,Number.isFinite(Number(value))?Math.round(Number(value)):0);
export const shortNumber=value=>new Intl.NumberFormat(undefined,{maximumFractionDigits:0}).format(numberValue(value));
export const periodLabel={ '1h':'Last hour', '1d':'Last 24 hours','7d':'Last 7 days','15d':'Last 15 days','30d':'Last 30 days' };
export const chartTimestamp=(stamp,period)=>{
  const date=new Date(stamp);
  if(!Number.isFinite(date.valueOf()))return '—';
  if(period==='1h')return date.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'});
  if(period==='1d')return date.toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
  return date.toLocaleDateString(undefined,{month:'short',day:'numeric',timeZone:'UTC'});
};
export function renderTrafficChart(root,rawSeries,period){
  root.replaceChildren();
  const series=Array.isArray(rawSeries)?rawSeries.map(item=>({
    at:typeof item?.at==='string'?item.at:'',
    views:numberValue(item?.views)
  })).filter(p=>Number.isFinite(new Date(p.at).getTime())):[];
  if(!series.length){
    const p=document.createElement('p');p.className='muted';p.textContent='No timeline data available yet.';root.append(p);
    return;
  }
  // Keep SVG text readable on phones instead of shrinking a 780px chart by half.
  const compact=root.clientWidth<490;
  const width=compact?420:780,height=compact?275:300;
  const left=compact?42:53,right=compact?12:15,top=23,bottom=46;
  const plotWidth=width-left-right,plotHeight=height-top-bottom;
  const maxValue=Math.max(1,...series.map(p=>p.views));
  const maxY=Math.max(4,Math.ceil(maxValue/4)*4);
  const x=i=>left+(series.length===1?0:(i/(series.length-1))*plotWidth);
  const y=v=>top+plotHeight-(v/maxY)*plotHeight;
  const plotBottom=top+plotHeight;
  const svg=createSvg('svg',{viewBox:`0 0 ${width} ${height}`,class:'traffic-chart-svg',
    role:'img','aria-label':'Page views over '+(periodLabel[period]||'selected period')});
  svg.append(createSvg('title',{},'CozyLoops tracked page view trend'));
  for(let tick=0;tick<=4;tick++){
    const value=Math.round(maxY*tick/4),level=y(value);
    svg.append(createSvg('line',{x1:left,y1:level,x2:width-right,y2:level,class:'traffic-chart-grid'}));
    svg.append(createSvg('text',{x:left-10,y:level+4,'text-anchor':'end',class:'traffic-chart-axis'},shortNumber(value)));
  }
  const labels=compact
    ?new Set([0,Math.floor((series.length-1)/2),series.length-1])
    :new Set([0,Math.floor((series.length-1)/4),Math.floor((series.length-1)/2),Math.floor((series.length-1)*3/4),series.length-1]);
  for(const index of labels){
    svg.append(createSvg('text',{x:x(index),y:height-13,'text-anchor':index===0?'start':index===series.length-1?'end':'middle',class:'traffic-chart-axis'},chartTimestamp(series[index].at,period)));
  }
  const coordinates=series.map((p,i)=>[x(i),y(p.views)]);
  const line=coordinates.map(([px,py],i)=>(i?'L':'M')+px.toFixed(2)+' '+py.toFixed(2)).join(' ');
  const shade=line+` L ${x(series.length-1)} ${plotBottom} L ${x(0)} ${plotBottom} Z`;
  svg.append(createSvg('path',{d:shade,class:'traffic-chart-area'}));
  svg.append(createSvg('path',{d:line,class:'traffic-chart-line'}));
  const hover=document.createElement('p');hover.className='traffic-chart-selection';hover.setAttribute('role','status');hover.setAttribute('aria-live','polite');
  hover.textContent='Choose a point on the chart to see its exact value.';
  const displaySelected=(index,marker)=>{
    for(const point of svg.querySelectorAll('.traffic-chart-dot'))point.classList.remove('selected');
    marker.classList.add('selected');
    hover.textContent=chartTimestamp(series[index].at,period)+' · '+shortNumber(series[index].views)+' tracked page view'+(series[index].views===1?'':'s');
  };
  coordinates.forEach(([px,py],i)=>{
    const marker=createSvg('circle',{cx:px,cy:py,r:4.3,class:'traffic-chart-dot'});
    svg.append(marker);
    const target=createSvg('rect',{x:Math.max(left,px-plotWidth/Math.max(1,series.length-1)/2),y:top-3,
      width:Math.min(plotWidth/Math.max(1,series.length-1),width-right-px+plotWidth/Math.max(1,series.length-1)/2),
      height:plotHeight+6,fill:'transparent',tabindex:'0',role:'button',
      'aria-label':chartTimestamp(series[i].at,period)+', '+series[i].views+' views'});
    target.addEventListener('pointerenter',()=>displaySelected(i,marker));
    target.addEventListener('focus',()=>displaySelected(i,marker));
    target.addEventListener('click',()=>displaySelected(i,marker));
    svg.append(target);
  });
  root.append(svg,hover);
  if(series.every(point=>point.views===0)){
    const p=document.createElement('p');p.className='muted';p.textContent='No consenting visits recorded in this period.';root.append(p);
  }
}

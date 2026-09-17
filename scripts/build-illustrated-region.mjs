// Trip-authored SVG geometry remains separate from the derived routeMap output.
export function buildIllustratedRegion(map, colors) {
  const art = map.region.illustration;
  if (!art) return null;
  const point = (id) => {
    const p = art.points[id];
    if (!p || ![p.x,p.y,p.tx,p.ty].every(Number.isFinite)) throw new Error(`Missing illustrated point: ${id}`);
    return [p.x,p.y];
  };
  const edges = art.edges.map(e => ({...e, points:[point(e.from),...(e.via || []),point(e.to)]}));
  const distance = ps => ps.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p[0]-ps[i][0],p[1]-ps[i][1]),0);
  function connect(from,to) {
    const direct = edges.find(e => (e.from === from && e.to === to) || (e.from === to && e.to === from));
    if (direct) return direct.from === from ? direct.points : [...direct.points].reverse();
    const queue=[{id:from,cost:0,points:[point(from)]}], done=new Set();
    while(queue.length) {
      queue.sort((a,b)=>a.cost-b.cost); const item=queue.shift();
      if(item.id===to) return item.points;
      if(done.has(item.id)) continue; done.add(item.id);
      for(const edge of edges) {
        if(edge.from!==item.id && edge.to!==item.id) continue;
        const forward=edge.from===item.id, next=forward?edge.to:edge.from;
        const ps=forward?edge.points:[...edge.points].reverse();
        if(!done.has(next)) queue.push({id:next,cost:item.cost+distance(ps),points:[...item.points,...ps.slice(1)]});
      }
    }
    throw new Error(`No illustrated road from ${from} to ${to}`);
  }
  const path = ps => ps.map((p,i)=>`${i?'L':'M'}${p[0]} ${p[1]}`).join(' ');
  const arrow = ps => {
    let remain=distance(ps)/2;
    for(let i=1;i<ps.length;i++) {
      const a=ps[i-1],b=ps[i],len=distance([a,b]);
      if(remain<=len) {const t=remain/len;return {x:a[0]+(b[0]-a[0])*t,y:a[1]+(b[1]-a[1])*t,angle:Math.atan2(b[1]-a[1],b[0]-a[0])*180/Math.PI};}
      remain-=len;
    }
  };
  const places=map.places.map(p=>({id:p.id,...art.points[p.id],geo:p.geo,lines:art.points[p.id].lines || [p.nameZh || p.name],size:29,color:colors[((map.routes.find(r=>r.placeIds.includes(p.id))?.day||1)-1)%colors.length],query:p.query || p.nameZh || p.name,days:map.routes.filter(r=>r.placeIds.includes(p.id)).map(r=>r.day),hiddenLabel:(art.hiddenLabels||[]).includes(p.id)}));
  const visible=places.filter(p=>!p.hiddenLabel);
  const routes=map.routes.map((r, routeIndex)=>{
    const legs=r.placeIds.slice(1).map((id,i)=>connect(r.placeIds[i],id));
    const used = new Set();
    const arrows = legs.filter(ps => {
      const key = [JSON.stringify(ps), JSON.stringify([...ps].reverse())].sort()[0];
      if (used.has(key)) return false; used.add(key); return true;
    }).map(arrow).filter(Boolean);
    return {laneOffset:map.region.id === 'lugu-lake' ? (routeIndex ? 6 : -6) : 0,day:r.day,color:colors[(r.day-1)%colors.length],placeIds:r.placeIds,paths:legs.map(path),arrows,label:art.dayLabels[String(r.day)] || ''};
  });
  const dailyLayouts=Object.fromEntries(routes.map(r=>{
    const ids=[...new Set(r.placeIds)];
    return [String(r.day),{places:ids,roles:Object.fromEntries(ids.map(id=>[id,id===r.placeIds[0] && id===r.placeIds.at(-1)?'起点 / 终点':id===r.placeIds[0]?'起点':id===r.placeIds.at(-1)?'终点':'途经点'])),labels:Object.fromEntries(ids.map(id=>[id,{x:art.points[id].tx,y:art.points[id].ty,anchor:art.points[id].anchor}])),transport:[]}];
  }));
  return {id:map.region.id,label:map.region.label,countryCode:map.region.countryCode,scope:'trip-illustration',mapMode:'original-illustration',templateId:'autumn-2026-original',days:routes.map(r=>r.day),canvas:{width:1100,height:1120},baseImage:art.baseImage,title:map.region.title,ariaLabel:`${map.region.label}原创手绘行程示意图`,description:map.region.description,disclaimer:map.disclaimer,heading:{text:map.region.label+' · 旅行手绘地图',x:55,y:80,size:43},subtitle:art.subtitle,legend:{x:55,y:155,gap:38,columns:2,columnGap:460},annotations:[],places,overviewPlaceIds:visible.map(p=>p.id),routes,dailyLayouts,illustrated:true,roads:edges.map(e=>path(e.points)),notes:art.notes};
}

// HTTPS map links use verified provider records; no automatic driving or timer-based app retries.
const mapPlaces=config.mapPlaces||[],mapBindings=new WeakSet();
const mapProvider=city=>config.mapProviders[city]||config.mapProvider;
const mapName=q=>String(q||'').normalize('NFKC').replace(/\s+/g,' ').trim().toLowerCase();
function findMapPlace(q,city='',key=''){
 const provider=mapProvider(city),matches=mapPlaces.filter(p=>p.provider===provider&&p.city===city&&p.verified&&(!key||p.key===key)&&(key||[p.name,...p.aliases].some(a=>mapName(a)===mapName(q))));
 return matches.length===1?matches[0]:null;
}
function mapTarget(q,city='',native=true,key=''){
 const provider=mapProvider(city),p=findMapPlace(q,city,key),name=p?.name||String(q||'').trim(),copy=[city,name].filter(Boolean).join(' ');
 const params=new URLSearchParams(provider==='amap'?{src:'travel-roadbook',callnative:native?'1':'0'}:{api:'1'});
 let mode='search',url;
 if(provider==='amap'){
  if(p?.placeId){params.set('poiid',p.placeId);url='https://uri.amap.com/poidetail?';mode='place'}
  else if(p?.shareUrl){const shared=new URL(p.shareUrl);if(shared.hostname==='uri.amap.com')shared.searchParams.set('callnative',native?'1':'0');return{url:shared.href,mode:'place',provider,name,copy,place:p,webControl:shared.hostname==='uri.amap.com'}}
  else{params.set('keyword',name);if(city)params.set('city',city);params.set('view','list');url='https://uri.amap.com/search?'}
 }else{
  let query=[name,city].filter(Boolean).join(', ');
  if(p?.placeId){params.set('query_place_id',p.placeId);mode='place'}
  else if(p?.shareUrl){return{url:p.shareUrl,mode:'place',provider,name,copy,place:p,webControl:false}}
  else if(p?.coordinates?.crs==='wgs84'){query=p.coordinates.lat+','+p.coordinates.lon;mode='point'}
  params.set('query',query||'地点待确认');url='https://www.google.com/maps/search/?';
  // Maps URLs have a 2048-character limit; only fallback search text may be shortened.
  while((url+params).length>2048&&params.get('query').length>1)params.set('query',params.get('query').slice(0,Math.ceil(params.get('query').length*.8)));
 }
 return{url:url+params,mode,provider,name,copy,place:p,webControl:provider==='amap'};
}
const mapUrl=(q,city='',native=true,key='')=>mapTarget(q,city,native,key).url;
function mapLinkHtml(q,city='',key='',classes='btn alt'){
 const t=mapTarget(q,city,true,key),label=t.mode==='place'?'查看地图地点':t.mode==='point'?'查看地图参考点':'查找地点';
 return `<a class="${classes}" data-roadbook-map data-map-query="${esc(q)}" data-map-city="${esc(city)}" data-map-key="${esc(key)}" href="${esc(t.url)}" target="_blank" rel="noopener noreferrer"><span>${label}</span><svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M7 17 17 7M7 7h10v10"/></svg></a>`;
}
function bindHotelMaps(){
 document.querySelectorAll('.hotel-row[data-map-query]').forEach(row=>{
  const a=row.querySelector('.hotel-map-link'),q=row.dataset.mapQuery,city=row.dataset.mapCity,key=row.dataset.mapKey||'',t=mapTarget(q,city,true,key);
  a.href=t.url;a.setAttribute('data-roadbook-map','');a.dataset.mapQuery=q;a.dataset.mapCity=city;a.dataset.mapKey=key;
  a.querySelector('span').textContent=t.mode==='place'?'地图地点':t.mode==='point'?'参考点':'查找';
  a.setAttribute('aria-label',`${t.provider==='amap'?'高德':'Google Maps'}：${t.name}`);
  let note=t.place?.note||'';if(t.place?.addressReview)note+=' 地图登记地址与订单文字有差异，请核对。';if(t.place?.referenceOnly)note+=' 这是参考位置，实际入口待确认。';if(t.mode==='search')note+=' 地图地点尚未绑定，请核对城市、分店与地址。';if(t.mode==='point')note+=' 坐标仅作参考，实际入口待确认。';
  if(note&&!row.querySelector('.map-verification-note')){const el=document.createElement('p');el.className='hotel-note map-verification-note';el.textContent=note;row.querySelector('.hotel-info').append(el)}
 });
}
function bindMapRecovery(){
 document.querySelectorAll('[data-roadbook-map]').forEach(a=>{
  if(mapBindings.has(a))return;mapBindings.add(a);
  a.addEventListener('click',()=>{setTimeout(()=>{
   const host=a.closest('.hotel-row')?.querySelector('.hotel-info')||a.closest('.food-actions,.actions');if(!host)return;
   const q=a.dataset.mapQuery,city=a.dataset.mapCity,key=a.dataset.mapKey,t=mapTarget(q,city,true,key),web=mapTarget(q,city,false,key);
   host.querySelector('.map-recovery')?.remove();const box=document.createElement('div');box.className='map-recovery';
   const fallback=document.createElement('a');fallback.className='btn alt';fallback.href=web.url;fallback.target='_blank';fallback.rel='noopener noreferrer';fallback.textContent=web.webControl?'网页版地图':'备用地图入口';
   const button=document.createElement('button');button.type='button';button.className='btn alt';button.textContent='复制地点名称';
   const status=document.createElement('p');status.className='map-recovery-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');
   let hint=/MicroMessenger/i.test(navigator.userAgent)?'微信内跳转受限时，可在系统浏览器打开或复制地点名称。':'跳转不顺时，可尝试备用入口或复制地点名称。';
   if(t.provider==='google')hint+=' Google Maps 是否进入 App 由设备和浏览器决定，备用入口也可能打开 App。';
   if(t.mode==='search')hint+=' 当前为名称查找，请核对城市与分店。';if(t.mode==='point'||t.place?.referenceOnly)hint+=' 此处是参考位置，实际入口仍需确认。';if(t.place?.addressReview)hint+=' 地图与订单地址文字有差异，请核对。';if(t.place?.note)hint+=' '+t.place.note;status.textContent=hint;
   button.addEventListener('click',async()=>{
    let done=false;try{if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(t.copy);done=true}}catch{}
    if(!done){const input=document.createElement('textarea');input.value=t.copy;input.readOnly=true;input.style.cssText='position:fixed;top:0;left:0;opacity:0;font-size:16px';document.body.append(input);input.select();try{done=document.execCommand('copy')}catch{}input.remove();button.focus({preventScroll:true})}
    if(done){button.textContent='已复制';status.textContent='已复制：'+t.copy}
    else{status.textContent='请长按下方名称复制。';let input=box.querySelector('input');if(!input){input=document.createElement('input');input.readOnly=true;input.setAttribute('aria-label','可手动复制的地点名称');box.append(input)}input.value=t.copy;input.focus();input.select()}
   });box.append(fallback,button,status);host.append(box);
  },0)});
 });
}
bindHotelMaps();

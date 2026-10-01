function setTravelerAt(progress,smoothTurn=true){
 if(!routeLegs.length){document.getElementById('route-play').hidden=true;['route-traveler','local-traveler'].forEach(id=>{const n=document.getElementById(id);if(n)n.style.display='none'});return}
 const length=routeLegLengths.reduce((a,b)=>a+b,0),distance=length*Math.max(0,Math.min(1,progress));
 let index=0,covered=0;for(let i=0;i<routeLegLengths.length;i++){index=i;if(distance<=covered+routeLegLengths[i])break;covered+=routeLegLengths[i]}
 const path=routeLegs[index],localDistance=Math.max(0,Math.min(routeLegLengths[index],distance-covered));
 const point=path.getPointAtLength(localDistance),before=path.getPointAtLength(Math.max(0,localDistance-4)),after=path.getPointAtLength(Math.min(routeLegLengths[index],localDistance+4));
 const dx=after.x-before.x,dy=after.y-before.y;
 const inFocus=path.dataset.mapView==='focus',legIndex=Number(path.dataset.leg??index);
 const traveler=document.getElementById(inFocus?'local-traveler':'route-traveler'),heading=document.getElementById(inFocus?'local-heading':'route-heading'),sprite=document.getElementById(inFocus?'local-cat-sprite':'cat-sprite');
 ['route-traveler','local-traveler'].forEach(id=>{const node=document.getElementById(id);if(node){node.style.display=node===traveler?'':'none';node.setAttribute('visibility',node===traveler?'visible':'hidden')}});
 const segment=config.routeSegments[legIndex]||{},mode=segment.mode||'unknown';
 const boxes={plane:'0 0 512 512',car:'512 0 512 512',train:'0 512 512 512',bike:'512 512 512 512'};
 let source=boxes[mode]?legIndex:-1;
 if(source<0){for(let j=legIndex-1;j>=0;j--){if(boxes[(config.routeSegments[j]||{}).mode]){source=j;break}}}
 if(source<0)source=config.routeSegments.findIndex(s=>boxes[s.mode]);
 const displayMode=source>=0?config.routeSegments[source].mode:'unknown',inherited=!boxes[mode]&&source>=0;
 if(sprite){sprite.setAttribute('viewBox',boxes[displayMode]||boxes.plane);sprite.style.display=boxes[displayMode]?'':'none'}
 const note=document.getElementById('local-mode-note');if(note)note.textContent='';
 let dot=heading.querySelector('.unknown-vehicle');if(!dot){dot=document.createElementNS('http://www.w3.org/2000/svg','circle');dot.setAttribute('class','unknown-vehicle');dot.setAttribute('r','6');dot.setAttribute('fill','#ac712c');heading.append(dot)}dot.style.display=!sprite||boxes[displayMode]?'none':'';
 const symbol=document.getElementById('transport-mode');if(symbol)symbol.textContent=({plane:'✈',train:'火车',car:'汽车',bike:'自行车'}[displayMode]||'待确认');
 const face=dx<0?1:-1,tilt=Math.max(-15,Math.min(15,Math.atan2(dy,Math.abs(dx))*180/Math.PI*(dx<0?-1:1)));
 traveler.setAttribute('transform','translate('+point.x+' '+point.y+')');heading.setAttribute('transform',sprite?'rotate('+tilt+') scale('+face+' 1)':'');heading.dataset.facing=dx<0?'left':'right';heading.dataset.mode=mode;heading.dataset.displayMode=displayMode;heading.dataset.inherited=String(inherited);heading.dataset.sourceLeg=String(source);
 const labels={train:'火车',car:'汽车',bike:'自行车',plane:'飞机'};
 const status=document.getElementById('map-status');status.textContent=(path.dataset.from||segment.from||config.routeCities[index]||'出发地')+' → '+(path.dataset.to||segment.to||config.routeCities[index+1]||'目的地')+' · '+(labels[mode]||('交通待确认'+(inherited?'（插画沿用'+labels[displayMode]+'）':'')));
}

(()=>{
 const track=document.querySelector('.daynav .shell'),list=document.querySelector('.route-grid');
 function revealTab(){const active=track.querySelector('[aria-selected="true"]');if(!active)return;const a=active.getBoundingClientRect(),b=track.getBoundingClientRect();if(a.left<b.left+10||a.right>b.right-10)track.scrollLeft+=a.left-b.left-(b.width-a.width)/2}
 new MutationObserver(revealTab).observe(track,{subtree:true,attributes:true,attributeFilter:['aria-selected']});
 function revealRoute(){const active=list.querySelector('[aria-pressed="true"]');if(!active)return;const a=active.getBoundingClientRect(),b=list.getBoundingClientRect();if(a.top<b.top||a.bottom>b.bottom)list.scrollTop+=a.top-b.top-(b.height-a.height)/2}
 new MutationObserver(revealRoute).observe(list,{subtree:true,attributes:true,attributeFilter:['aria-pressed']});
 const preview=document.getElementById('route-preview');new MutationObserver(()=>{if(!preview.hidden&&!matchMedia('(prefers-reduced-motion: reduce)').matches)preview.animate([{opacity:.4,transform:'translateY(-6px)'},{opacity:1,transform:'none'}],{duration:220,easing:'ease-out'})}).observe(preview,{attributes:true,attributeFilter:['hidden']});
})();

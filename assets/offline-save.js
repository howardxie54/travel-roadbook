document.getElementById('download').addEventListener('click',event=>{
event.preventDefault();const copy=document.documentElement.cloneNode(true);
// Daily content is regenerated from embedded data; do not duplicate large photos in the export.
copy.querySelector('#days').replaceChildren();const preview=copy.querySelector('#route-preview');if(preview)preview.hidden=true;
copy.querySelectorAll('.route-leg').forEach(path=>{path.style.strokeDasharray='';path.style.strokeDashoffset=''});
copy.querySelectorAll('.map-recovery').forEach(e=>e.remove());
const blob=new Blob(['<!doctype html>\n'+copy.outerHTML],{type:'text/html;charset=utf-8'}),link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='旅行路书.html';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
});

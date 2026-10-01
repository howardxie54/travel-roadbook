    function freezeDayMotion(){
      if(!dayMotion)return;
      const motion=dayMotion,current=dayPanels[activeDay];
      if(motion.settling){
        const matrix=new DOMMatrixReadOnly(getComputedStyle(current).transform);
        motion.x=matrix.m41;
        const states=motion.indices.map(n=>({n,transform:getComputedStyle(dayPanels[n]).transform,opacity:getComputedStyle(dayPanels[n]).opacity}));
        motion.settling=false;motion.animations.forEach(a=>a.cancel());motion.animations=[];
        states.forEach(s=>{dayPanels[s.n].style.transform=s.transform;dayPanels[s.n].style.opacity=s.opacity});
      }
    }
    function prepareDayMotion(targets,mode='gesture'){
      if(!dayMotion){
        const current=dayPanels[activeDay],rect=current.getBoundingClientRect(),viewport=daysContainer.getBoundingClientRect();
        // Travel across the clipping viewport, including its gutters. Keep layout size separate.
        dayMotion={width:viewport.width,panelWidth:rect.width,left:rect.left-viewport.left,top:rect.top-viewport.top,x:0,indices:[],animations:[],settling:false,target:activeDay,mode};
        daysContainer.style.height=`${rect.height}px`;
        daysContainer.style.overflow='hidden';
      }
      const motion=dayMotion;
      [activeDay,...targets].filter(n=>n>=0&&n<trip.length).forEach(n=>{
        if(motion.indices.includes(n))return;
        if(n!==activeDay&&motion.indices.some(existing=>existing!==activeDay&&Math.sign(existing-activeDay)===Math.sign(n-activeDay)))return;
        const panel=dayPanels[n];
        motion.indices.push(n);panel.hidden=false;panel.style.position='absolute';panel.style.left=`${motion.left}px`;panel.style.top=`${motion.top}px`;panel.style.width=`${motion.panelWidth}px`;
        if(n!==activeDay){panel.inert=true;panel.setAttribute('aria-hidden','true');panel.style.pointerEvents='none'}
      });
      paintDayMotion(motion.x);
    }
    function paintDayMotion(x){
      if(!dayMotion)return;
      const motion=dayMotion;motion.x=x;
      motion.indices.forEach(n=>{
        const offset=n<activeDay?-motion.width:n>activeDay?motion.width:0,panel=dayPanels[n];
        const incoming=n!==activeDay&&Math.sign(n-activeDay)===Math.sign(-x);
        const reveal=motion.mode==='switch'?1:Math.max(0,Math.min(1,(Math.abs(x)/motion.width-.38)/.18));
        panel.style.transform=`translate3d(${offset+x}px,0,0)`;
        panel.style.opacity=String(n===activeDay?1:incoming?reveal:0);
      });
    }
    function settleDayMotion(target){
      if(!dayMotion)return;
      if(reducedMotion.matches||window.__instantInteraction){showDay(target);return}
      freezeDayMotion();
      const motion=dayMotion,to=target>activeDay?-motion.width:target<activeDay?motion.width:0;
      motion.target=target;motion.settling=true;selectDayTab(target);
      const easing=getComputedStyle(document.documentElement).getPropertyValue('--ease-out').trim()||'cubic-bezier(.23,1,.32,1)';
      motion.animations=motion.indices.map(n=>{
        const panel=dayPanels[n],offset=n<activeDay?-motion.width:n>activeDay?motion.width:0;
        const frames=[{transform:getComputedStyle(panel).transform},{transform:`translate3d(${offset+to}px,0,0)`}];
        // The current page remains opaque; only the incoming page needs a fade.
        if(n!==activeDay){frames[0].opacity=getComputedStyle(panel).opacity;frames[1].opacity=n===target?1:0}
        return panel.animate(frames,{duration:260,easing,fill:'forwards'});
      });
      Promise.all(motion.animations.map(a=>a.finished)).then(()=>{
        if(dayMotion!==motion||!motion.settling)return;
        const next=queuedDay;showDay(target);if(next!==null)switchDay(next);
      }).catch(()=>{});
    }
    function switchDay(i){
      const next=Math.min(trip.length-1,Math.max(0,Number(i)||0));
      if(dayMotion?.settling){queuedDay=next;return}
      queuedDay=null;
      if(next===activeDay){if(dayMotion)settleDayMotion(activeDay);return}
      if(reducedMotion.matches||window.__instantInteraction||!dayPanels[next].animate){showDay(next);return}
      if(dayMotion){clearDayMotion()}
      prepareDayMotion([next],'switch');settleDayMotion(next);
    }

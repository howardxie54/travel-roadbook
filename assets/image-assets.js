const foodAssetData=__FOOD_IMAGES__;
const foodImages={};
for(const [key,value] of Object.entries(foodAssetData.images)){
 if(typeof value==='string'){foodImages[key]=value;continue}
 const src=foodAssetData.resources[value.resource];
 const svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="'+value.viewBox+'"><image href="'+src+'" width="'+value.width+'" height="'+value.height+'"/></svg>';
 foodImages[key]='data:image/svg+xml;base64,'+btoa(svg);
}

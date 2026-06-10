/* Renderer for converting API JSON into bubble UI blocks with nested bubbles */
function formatNumber(n){
  if(typeof n !== 'number') return n;
  return n.toLocaleString();
}

// translations loaded from /static/translations.json
let __bubbleTranslations = {};
async function loadBubbleTranslations(){
  try{
    const r = await fetch('/static/translations.json', {cache:'no-store'});
    if(r.ok) __bubbleTranslations = await r.json();
  }catch(e){
    __bubbleTranslations = {};
  }
}

function prettyKey(k){
  if(!k) return '';
  // keep hashes and numeric indexes unchanged
  if(/^#\d+$/.test(String(k))) return k;
  // insert spaces for camelCase and underscores
  const s = String(k).replace(/([a-z0-9])([A-Z])/g, '$1 $2').replace(/[_-]+/g,' ').trim();
  return s.replace(/\s+/g,' ').replace(/\b\w/g, c => c.toUpperCase());
}

function translateKey(k){
  if(!k && k !== 0) return '';
  const ks = String(k);
  if(/^#\d+$/.test(ks)) return ks;
  // exact
  if(__bubbleTranslations[ks]) return __bubbleTranslations[ks];
  // case-insensitive match
  const found = Object.keys(__bubbleTranslations).find(t => t.toLowerCase() === ks.toLowerCase());
  if(found) return __bubbleTranslations[found];
  // fallback to pretty version (Title Case)
  return prettyKey(ks);
}

function createBubble(title, obj, nested = false){
  const el = document.createElement('div');
  el.className = nested ? 'bubble nested-bubble' : 'bubble';
  const h = document.createElement('h3'); h.className='bubble-title'; h.textContent = translateKey(title);
  el.appendChild(h);
  const content = document.createElement('div'); content.className='bubble-content';

  // If primitive, show full value
  if(obj === null || typeof obj !== 'object'){
    const row = document.createElement('div'); row.className='row';
    const k = document.createElement('div'); k.className='key'; k.textContent = '';
    const v = document.createElement('div'); v.className='val'; v.textContent = String(obj);
    row.appendChild(k); row.appendChild(v); content.appendChild(row);
    el.appendChild(content);
    return el;
  }

  // For arrays, show count and nested small bubbles for items
  if(Array.isArray(obj)){
    const row = document.createElement('div'); row.className='row';
    const k = document.createElement('div'); k.className='key'; k.textContent = translateKey('count');
    const v = document.createElement('div'); v.className='val'; v.textContent = obj.length;
    row.appendChild(k); row.appendChild(v); content.appendChild(row);

    const nestedGrid = document.createElement('div'); nestedGrid.className = 'nested-grid';
    // show all items (no limit)
    for(let i=0;i<obj.length;i++){
      nestedGrid.appendChild(createBubble(`#${i+1}`, obj[i], true));
    }
    content.appendChild(nestedGrid);
    // apply same post-processing to nested grid (place very tall sub-bubbles on their own row)
    try{ postProcessGrid(nestedGrid); }catch(e){}
    el.appendChild(content);
    return el;
  }

  // For objects, show primitive key rows first
  const keys = Object.keys(obj);
  keys.forEach(kname=>{
    const val = obj[kname];
    if(val === null || typeof val !== 'object'){
      const row = document.createElement('div'); row.className='row';
      const k = document.createElement('div'); k.className='key'; k.textContent = translateKey(kname);
      const v = document.createElement('div'); v.className='val';
      if(typeof val === 'number') v.textContent = formatNumber(val);
      else if(typeof val === 'string') v.textContent = val.length>48?val.slice(0,48)+'…':val;
      else v.textContent = String(val);
      row.appendChild(k); row.appendChild(v); content.appendChild(row);
    }
  });

  // For nested objects/arrays, create small nested bubbles inside this bubble
  const nestedKeys = keys.filter(kname => obj[kname] && typeof obj[kname] === 'object');
  if(nestedKeys.length){
    const nestedGrid = document.createElement('div'); nestedGrid.className = 'nested-grid';
    nestedKeys.forEach(kname=>{
      nestedGrid.appendChild(createBubble(kname, obj[kname], true));
    });
    content.appendChild(nestedGrid);
    // post-process nested grid too
    try{ postProcessGrid(nestedGrid); }catch(e){}
  }

  el.appendChild(content);
  return el;
}

function renderJsonToBubbles(container, data, titleKey){
  container.innerHTML = '';
  if(!data) return;
  // If root is array, create bubble per item with index or using titleKey
  if(Array.isArray(data)){
    const grid = document.createElement('div'); grid.className='bubble-grid';
    data.forEach((it,i)=>{
      let title = `#${i+1}`;
      if(titleKey && it && typeof it === 'object' && it[titleKey]) title = String(it[titleKey]);
      grid.appendChild(createBubble(title, it));
    });
    container.appendChild(grid);
    // post-process: put very tall bubbles on their own row
    postProcessGrid(grid);
    return;
  }
  // If root is object, create bubble per key
  if(typeof data === 'object'){
    const grid = document.createElement('div'); grid.className='bubble-grid';
    Object.keys(data).forEach(k=>{
      grid.appendChild(createBubble(k, data[k]));
    });
    container.appendChild(grid);
    // post-process: put very tall bubbles on their own row
    postProcessGrid(grid);
    return;
  }

  // fallback
  container.textContent = JSON.stringify(data);
}

// auto attach helper — finds elements with data-api and fetches + renders
document.addEventListener('DOMContentLoaded', async ()=>{
  await loadBubbleTranslations();
  document.querySelectorAll('[data-api]').forEach(el=>{
    const url = el.getAttribute('data-api');
    const titleKey = el.getAttribute('data-title') || null;
    const btn = el.querySelector('[data-action="load"]');
    const out = el.querySelector('.api-output') || el;
    const loadFn = async ()=>{
      out.innerHTML = '<div class="loader">Chargement…</div>';
      try{
        const r = await fetch(url, {cache:'no-store'});
        const j = await r.json();
        renderJsonToBubbles(out, j, titleKey);
      }catch(e){
        out.innerHTML = '<div class="error">Erreur: '+e+'</div>';
      }
    };
    if(btn) btn.addEventListener('click', loadFn); else loadFn();
  });
});

function postProcessGrid(grid){
  try{
    const items = Array.from(grid.children).filter(n => n.classList && n.classList.contains('bubble'));
    if(items.length === 0) return;
    const heights = items.map(i => i.scrollHeight || i.offsetHeight);
    const avg = heights.reduce((a,b)=>a+b,0)/heights.length;
    const threshold = Math.max(420, avg * 1.4);
    items.forEach(it=>{
      if((it.scrollHeight || it.offsetHeight) > threshold){
        it.classList.add('bubble--full');
      } else {
        it.classList.remove('bubble--full');
      }
    });
  }catch(e){
    // ignore
  }
}

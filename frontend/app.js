/* ATLAS — no bundler, CDN, framework or external API. Data comes only from FastAPI. */
(() => {
  'use strict';

  const PATHS = {
    'layout-dashboard': '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    'building-2': '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h2m4 0h2M8 10h2m4 0h2M8 14h2m4 0h2"/>',
    sparkles: '<path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3ZM5 19l.8 2.2L8 22l-2.2.8L5 25l-.8-2.2L2 22l2.2-.8L5 19ZM20 15l.8 2.2L23 18l-2.2.8L20 21l-.8-2.2L17 18l2.2-.8L20 15Z" transform="translate(0 -2)"/>',
    'notebook-text': '<rect x="5" y="3" width="16" height="18" rx="2"/><path d="M9 3v18M12 8h5M12 12h5M12 16h5M3 7h4M3 12h4M3 17h4"/>',
    'code-2': '<path d="m8 8-4 4 4 4m8-8 4 4-4 4m-3-11-2 14"/>',
    activity: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    'arrow-up-right': '<path d="M7 17 17 7M7 7h10v10"/>',
    'arrow-right': '<path d="M4 12h16m-7-7 7 7-7 7"/>',
    'refresh-cw': '<path d="M20 11a8 8 0 0 0-14.5-4.5L3 9m0-5v5h5M4 13a8 8 0 0 0 14.5 4.5L21 15m0 5v-5h-5"/>',
    database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v7c0 1.7 4 3 9 3s9-1.3 9-3V5M3 12v7c0 1.7 4 3 9 3s9-1.3 9-3v-7"/>',
    'info': '<circle cx="12" cy="12" r="10"/><path d="M12 11v6M12 7h.01"/>',
    'users': '<path d="M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M18 4a4 4 0 0 1 0 8m4 8v-2a4 4 0 0 0-3-3.87"/><circle cx="9" cy="7" r="4"/>',
    'wallet': '<rect x="2" y="5" width="20" height="16" rx="2"/><path d="M2 9h20M16 15h2M6 5V3h13"/>',
    'target': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    'ruler': '<path d="m4 16 12-12 4 4-12 12-4-4ZM9 11l3 3m1-7 3 3"/>',
    'chevron-right': '<path d="m9 18 6-6-6-6"/>',
    'chevron-left': '<path d="m15 18-6-6 6-6"/>',
    'lightbulb': '<path d="M9 18h6m-5 4h4M9 14a6 6 0 1 1 6 0v4H9v-4Z"/>',
    'alert-circle': '<circle cx="12" cy="12" r="10"/><path d="M12 7v6m0 4h.01"/>',
    'alert-triangle': '<path d="M10 3.5 1.5 19a2 2 0 0 0 1.8 3h17.4a2 2 0 0 0 1.8-3L14 3.5a2.3 2.3 0 0 0-4 0Z"/><path d="M12 9v5m0 4h.01"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/>',
    x: '<path d="M5 5 19 19M19 5 5 19"/>',
    'shield-check': '<path d="M12 22c-6-3-9-7-9-12V5l9-3 9 3v5c0 5-3 9-9 12Z"/><path d="m8 12 3 3 5-5"/>',
    'scan-search': '<path d="M4 9V4h5M15 4h5v5M4 15v5h5M15 20h5v-5"/><circle cx="11" cy="11" r="4"/><path d="m14 14 3 3"/>',
    'lock-keyhole': '<rect x="4" y="10" width="16" height="12" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 15v3"/>',
    'check-circle': '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    'bar-chart': '<path d="M4 20V11m6 9V5m6 15v-8m4 8V8"/>',
    'layers': '<path d="m12 2 10 6-10 6L2 8l10-6Zm-10 10 10 6 10-6M2 16l10 6 10-6"/>',
    'file-check': '<path d="M14 2H5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9l-7-7Z M14 2v7h7m-14 7 3 3 5-5"/>',
  };
  const svg = name => `<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${PATHS[name] || PATHS.info}</svg>`;
  const enhanceIcons = root => (root || document).querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = svg(el.dataset.icon); });
  const $ = sel => document.querySelector(sel);
  const safe = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const nf = new Intl.NumberFormat('en-DK');
  const shortDKK = value => {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
    const n = Number(value);
    if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + 'B';
    if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(2) + 'M';
    if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'K';
    return nf.format(Math.round(n));
  };
  const num = n => n !== null && n !== undefined && Number.isFinite(Number(n)) ? nf.format(Number(n)) : '—';
  const yearValue = n => n === null || n === undefined ? '—' : String(n);
  const dkk = n => n == null ? '—' : 'DKK ' + nf.format(Math.round(n));
  const pct = (a,b) => b ? (100*a/b).toFixed(1)+'%' : '0%';
  const gradeTag = grade => `<span class="energy-chip grade-${safe(grade)}" aria-label="Energy rating ${safe(grade)}">${safe(grade)}</span>`;
  const state = {summary:null, breakdown:null, view:'overview',page:1,pageSize:12,pages:1,propertiesTotal:0,fetchID:0,loading:false,drawerLastFocus:null};
  let searchTimer;
  let toastTimer;

  async function fetchJSON(url, options={}) {
    const response = await fetch(url, {headers:{Accept:'application/json', ...options.headers}, ...options});
    let data;
    try { data = await response.json(); } catch { throw new Error('Invalid JSON response from server'); }
    if (!response.ok) {
      const detail = typeof data.detail === 'string' ? data.detail : (Array.isArray(data.detail) ? data.detail.map(x=>x.msg).join('; ') : 'Unexpected server error');
      throw new Error(detail || `HTTP ${response.status}`);
    }
    return data;
  }
  function showError(error) {
    $('#apiError').classList.remove('hidden');
    $('#apiErrorText').textContent = error?.message || 'Unable to reach the backend.';
    $('#sidebarStatus').classList.remove('ready');
    $('#sidebarStatusText').textContent = 'API unavailable';
  }
  function hideError() {
    $('#apiError').classList.add('hidden');
    $('#sidebarStatus').classList.add('ready');
    $('#sidebarStatusText').textContent = 'API connected';
  }
  function toast(message) {
    clearTimeout(toastTimer);
    $('#toast').textContent = message;
    $('#toast').classList.remove('hidden');
    toastTimer = setTimeout(() => $('#toast').classList.add('hidden'), 2800);
  }

  async function loadOverview() {
    try {
      const [summary, breakdown, watch] = await Promise.all([
        fetchJSON('/analytics/summary'),
        fetchJSON('/analytics/breakdown'),
        fetchJSON('/properties?page_size=5&sort=priority')
      ]);
      state.summary = summary;
      state.breakdown = breakdown;
      hideError();
      renderKpis(summary);
      renderRatings(breakdown.energy_ratings, summary.total_properties);
      renderTypes(breakdown.building_types);
      renderWatchlist(watch.items);
      renderInsights(summary, breakdown);
      $('#method-data').textContent = `${num(summary.total_properties)} properties · ${num(summary.total_assets)} assets · ${num(summary.total_inspections)} inspections`;
    } catch(e) { showError(e); }
  }
  function renderKpis(s) {
    const cells = [
      ['Total properties',num(s.total_properties),'Validated building records','building-2',''],
      ['Estimated investment','DKK '+shortDKK(s.total_estimated_retrofit_cost_dkk),'Assumption-based scenario','wallet','teal'],
      ['High priority',num(s.high_priority_properties),pct(s.high_priority_properties,s.total_properties)+' of the portfolio','target','orange'],
      ['Weighted cost per m²',num(s.portfolio_weighted_cost_per_m2_dkk),'DKK · portfolio-weighted','ruler','blue']
    ];
    $('#kpiGrid').innerHTML = cells.map(([label,value,foot,icon,tone]) => `<article class="kpi-card"><div class="kpi-icon ${tone}">${svg(icon)}</div><div class="kpi-label">${safe(label)}</div><div class="kpi-value">${safe(value)}</div><div class="kpi-foot">${safe(foot)}</div></article>`).join('');
  }
  function renderRatings(items,total) {
    const max=Math.max(...items.map(x=>x.property_count),1);
    $('#ratingsChart').innerHTML = items.map(item=>`<div class="rating-row" title="${safe(pct(item.property_count,total))} of properties"><span class="rating-pill grade-${safe(item.label)}">${safe(item.label)}</span><div class="bar-track"><div class="bar-fill grade-${safe(item.label)}" style="width:${100*item.property_count/max}%"></div></div><span class="rating-count">${num(item.property_count)}</span></div>`).join('');
  }
  function renderTypes(items) {
    const max=Math.max(...items.map(x=>x.cost_dkk),1);
    $('#typesChart').innerHTML = items.map(item=>`<div class="type-row"><div class="type-head"><span class="name">${safe(item.label)}</span><span class="value">${(item.cost_dkk/1e9).toFixed(2)}B</span></div><div class="type-track"><div class="type-fill" style="width:${100*item.cost_dkk/max}%"></div></div></div>`).join('');
  }
  function renderWatchlist(items) {
    $('#watchlist').innerHTML = items.map((p,i)=>`<button type="button" class="watch-row" data-property="${safe(p.id)}"><span class="watch-num">${String(i+1).padStart(2,'0')}</span><span><span class="watch-name" style="display:block">${safe(p.name)}</span><span class="watch-meta" style="display:block">${safe(p.building_type)} · ${safe(p.id)}</span></span><span class="watch-score">${num(p.priority_score)} / 100</span><span class="watch-cost">${shortDKK(p.estimated_maintenance_cost_dkk)}</span><span class="watch-chevron">${svg('chevron-right')}</span></button>`).join('');
  }
  function renderInsights(s,b) {
    const mostExpensive=b.building_types[0];
    const high=b.priorities.find(x=>x.label==='High');
    const items=[
      ['target',`${pct(s.high_priority_properties,s.total_properties)} flagged high priority`,`${num(s.high_priority_properties)} properties score at least 70 on the screening index.`],
      ['layers',`${safe(mostExpensive?.label || 'No category')} leads modelled spending`,`${shortDKK(mostExpensive?.cost_dkk)} DKK of scenario cost across ${num(mostExpensive?.property_count)} properties.`],
      ['file-check',`${num(s.properties_with_imputed_fields)} properties have imputed fields`,`Year or area was filled from building-type medians; ${num(s.unknown_energy_ratings)} ratings remain unknown.`],
    ];
    $('#insights').innerHTML=items.map(([icon,title,body])=>`<div class="insight-item"><span class="insight-marker">${svg(icon)}</span><div><strong>${title}</strong><p>${body}</p></div></div>`).join('');
  }

  function currentFilters(){
    const p=new URLSearchParams({page:String(state.page),page_size:String(state.pageSize),sort:$('#sortProperties').value,priority:$('#priorityFilter').value});
    const more={q:$('#propertySearch').value.trim(),building_type:$('#typeFilter').value,district:$('#districtFilter').value,energy_rating:$('#ratingFilter').value};
    Object.entries(more).forEach(([k,v])=>{ if(v) p.set(k,v); });
    return p;
  }
  async function loadProperties(){
    const id=++state.fetchID;
    $('#propertyRows').innerHTML='<tr><td colspan="6" class="table-empty">Loading properties…</td></tr>';
    try{
      const data=await fetchJSON('/properties?'+currentFilters().toString());
      if(id!==state.fetchID) return;
      state.pages=data.pages;state.propertiesTotal=data.total;
      $('#propertiesCounter').textContent=num(data.total)+' properties';
      $('#resultsCaption').textContent=`${num(data.total)} matching properties`;
      $('#paginationInfo').textContent=data.total ? `Showing ${num((data.page-1)*data.page_size+1)}–${num((data.page-1)*data.page_size+data.items.length)} of ${num(data.total)}` : 'No matching properties';
      $('#pageIndicator').textContent=`${data.pages ? data.page : 0} / ${data.pages}`;
      $('#prevPage').disabled=data.page<=1;
      $('#nextPage').disabled=data.page>=data.pages;
      if(!data.items.length){$('#propertyRows').innerHTML='<tr><td colspan="6" class="table-empty">No properties match these filters. Try a broader search.</td></tr>';return;}
      $('#propertyRows').innerHTML=data.items.map(p=>`<tr class="table-row-action" tabindex="0" role="button" data-property="${safe(p.id)}" aria-label="Open ${safe(p.name)} details"><td><div class="prop-main">${safe(p.name)}</div><div class="prop-sub">${safe(p.id)} · Built ${yearValue(p.built_year)}</div></td><td><div>${safe(p.building_type)}</div><div class="table-sub">${safe(p.district)}</div></td><td>${gradeTag(p.energy_rating)}</td><td><span class="priority-meter"><span class="priority-track"><span class="priority-fill" style="display:block;width:${Math.max(0,Math.min(100,p.priority_score))}%"></span></span><span class="priority-num">${num(p.priority_score)}</span></span></td><td class="money-cell">${dkk(p.estimated_maintenance_cost_dkk)}</td><td><button type="button" class="table-arrow" data-property="${safe(p.id)}" aria-label="Open ${safe(p.name)}">${svg('arrow-up-right')}</button></td></tr>`).join('');
    }catch(e){if(id!==state.fetchID)return;showError(e);$('#propertyRows').innerHTML=`<tr><td colspan="6" class="table-empty">Could not load properties: ${safe(e.message)}</td></tr>`;}
  }
  function renderAssetHierarchy(deep){
    const baseline=deep.energy_baseline;
    const coverage=deep.coverage||[];
    const absent=coverage.filter(x=>x.status!=='assessed');
    const systemCards=deep.systems.map(s=>`<details class="asset-system" ${s.type==='HVAC'?'open':''}><summary><span>${safe(s.type)}</span><span class="asset-subtitle">${num(s.assets.length)} asset types · view inspection and investment</span></summary><div class="asset-body">${s.assets.map(a=>{
      const i=a.intervention;
      return `<article class="asset-line"><div class="asset-line-head"><strong>${safe(a.name)}</strong><span class="asset-condition-pill ${a.condition_score>=4?'is-poor':''}">${num(a.condition_score)}/5</span></div><div class="asset-line-meta">${num(a.quantity)} ${safe(a.unit)} · ${dkk(a.unit_cost_dkk)} / ${safe(a.unit)} · installed ${yearValue(a.installed_year)}</div><p>${safe(a.inspection.finding)} · Confidence: ${safe(a.inspection.confidence)}</p>${i?`<div class="asset-intervention"><div><span>INTERVENTION</span><strong>${dkk(i.cost_dkk)}</strong></div><div><span>ASSUMED ENERGY SAVINGS / YEAR</span><strong>${num(i.annual_savings_kwh)} kWh</strong></div><div><span>ANNUAL BILL SAVINGS</span><strong>${dkk(i.annual_savings_dkk)}</strong></div><div><span>NPV · 4% DISCOUNT</span><strong>${dkk(i.npv_dkk)}</strong></div></div>${i.prerequisite_intervention_id?`<p class="asset-dependency">Dependency: ${safe(i.prerequisite_intervention_id)} must be funded first.</p>`:''}`:'<div class="asset-noaction">No retrofit intervention modelled for this asset at present.</div>'}</article>`;
    }).join('')}</div></details>`).join('');
    return `<div class="detail-hierarchy"><h3 class="detail-section-title">Site → systems → assets → interventions</h3><div class="detail-id">${safe(deep.property.site_name)} · ${safe(deep.property.site_id)}</div><div class="detail-energy"><div><small>ASSUMED ANNUAL ENERGY USE</small><strong>${num(baseline.annual_energy_kwh)} kWh</strong></div><div><small>ASSUMED INTENSITY</small><strong>${num(baseline.intensity_kwh_m2_year)} kWh/m²</strong></div></div>${systemCards}<h3 class="detail-section-title">Assessment coverage</h3><div class="coverage-grid">${coverage.map(c=>`<div class="coverage-pill ${c.status}"><strong>${safe(c.system_type)}</strong><span>${safe(c.status.replaceAll('_',' '))}</span></div>`).join('')}</div>${absent.length?`<p class="detail-note">${num(absent.filter(c=>c.status==='not_inspected').length)} system categories lack an assessment. Missing data are not interpreted as good condition or a zero-cost finding.</p>`:''}<p class="detail-note">Calculated asset quantities, energy demand and estimated benefits are synthetic proxies. Multiple measures may produce overlapping savings; modelled totals are not verified reductions.</p></div>`;
  }

  async function openProperty(id){
    state.drawerLastFocus=document.activeElement;
    $('#drawerShade').classList.remove('hidden');
    $('#propertyDrawer').setAttribute('aria-hidden','false');
    $('#drawerTitle').textContent='Loading property…';
    $('#drawerBody').innerHTML='<p class="empty-placeholder">Loading building components…</p>';
    requestAnimationFrame(()=>{$('#drawerShade').classList.add('open');$('#propertyDrawer').classList.add('open');$('#drawerClose').focus();});
    try{
      const [data,deep]=await Promise.all([fetchJSON('/properties/'+encodeURIComponent(id)),fetchJSON('/properties/'+encodeURIComponent(id)+'/assets')]);
      const p=data.property;
      $('#drawerTitle').textContent=p.name;
      const components=data.components;
      $('#drawerBody').innerHTML=`<div class="detail-id">${safe(p.id)} · BUILT ${yearValue(p.built_year)} · ${safe(p.district.toUpperCase())}</div><div class="detail-chips"><span class="detail-chip">${safe(p.building_type)}</span><span class="detail-chip">Energy ${safe(p.energy_rating)}</span><span class="detail-chip">Priority ${num(p.priority_score)} / 100</span></div><div class="detail-metrics"><div class="detail-metric"><small>ESTIMATED RETROFIT COST</small><strong>${shortDKK(p.estimated_maintenance_cost_dkk)} DKK</strong></div><div class="detail-metric"><small>COST PER M²</small><strong>${num(p.estimated_cost_per_m2_dkk)} DKK</strong></div><div class="detail-metric"><small>FLOOR AREA</small><strong>${num(p.floor_area_m2)} m²</strong></div><div class="detail-metric"><small>SCREENING PRIORITY</small><strong>${num(p.priority_score)} / 100</strong></div></div><h3 class="detail-section-title">Component assessment</h3>${components.map(c=>`<div class="detail-component"><div class="component-top"><span>${safe(c.component_type)}</span><span>${dkk(c.estimated_maintenance_cost_dkk)}</span></div><div class="component-condition"><div class="${c.condition_score>=4?'condition-high':''}" style="width:${20*c.condition_score}%"></div></div><div class="component-bottom"><span>Condition ${num(c.condition_score)} / 5 · ${c.intervention_recommended?'Intervention suggested':'No intervention flagged'}</span><span>Installed ${yearValue(c.installed_year)}</span></div></div>`).join('')}${p.year_imputed||p.area_imputed?`<div class="detail-warning">${svg('alert-triangle')} <span>Some values are imputed (${[p.year_imputed?'construction year':'',p.area_imputed?'floor area':''].filter(Boolean).join(', ')}). Validate these before investment decisions.</span></div>`:''}<p class="detail-note">Component costs and priority are synthetic scenario estimates, not observed prices or an engineering assessment. Component condition: 1 = excellent, 5 = critical.</p>`;
      $('#drawerBody').insertAdjacentHTML('beforeend',renderAssetHierarchy(deep));
    }catch(e){ $('#drawerBody').innerHTML=`<div class="detail-warning">${safe(e.message)}</div>`; }
  }
  function closeProperty(){
    $('#propertyDrawer').classList.remove('open');$('#drawerShade').classList.remove('open');
    $('#propertyDrawer').setAttribute('aria-hidden','true');
    setTimeout(()=>$('#drawerShade').classList.add('hidden'),290);
    if(state.drawerLastFocus?.isConnected)state.drawerLastFocus.focus();
  }

  async function ask(question) {
    if(state.loading)return;
    question=question.trim();
    if(question.length<10){toast('Please enter at least 10 characters.');return;}
    state.loading=true;
    $('#askSubmit').disabled=true;$('#askSubmit').textContent='Analysing…';
    $('#askResults').innerHTML='<div class="empty-placeholder">Interpreting question and checking the database…</div>';
    try{
      const result=await fetchJSON('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question})});
      renderAnswer(result);
      $('#askResults').scrollIntoView({block:'nearest',behavior:'smooth'});
    }catch(e){
      $('#askResults').innerHTML=`<div class="alert" role="alert">${svg('alert-circle')}<div><strong>Could not answer this question.</strong><p>${safe(e.message)}</p></div></div>`;
    }finally{
      state.loading=false;$('#askSubmit').disabled=false;$('#askSubmit').innerHTML=`Run analysis ${svg('arrow-up-right')}`;
    }
  }
  function renderAnswer(result) {
    let rows=result.rows||[];
    // Do not infer numeric fields or labels: display only the returned DB-backed evidence.
    const cols=rows.length ? Object.keys(rows[0]) : [];
    const formatCell=(key,v)=>{
      if(v===null)return '—';
      if(typeof v==='number'){
        if(key==='built_year'||key==='installed_year') return yearValue(v);
        if(key.endsWith('_dkk'))return dkk(v);
        return num(v);
      }
      if((key==='id'||key==='property_id') && /^P\d{5}$/.test(v))return `<button type="button" data-property="${safe(v)}">${safe(v)}</button>`;
      return safe(v);
    };
    const displayName=k=>k.replaceAll('_',' ').replace(/\bdkk\b/g,'DKK').replace(/\bm2\b/g,'m²');
    const table=rows.length?`<div class="evidence-table-wrap"><table class="evidence-table"><thead><tr>${cols.map(k=>`<th>${safe(displayName(k).toUpperCase())}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(k=>`<td>${formatCell(k,r[k])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:'<p class="empty-placeholder">No matching records were found.</p>';
    $('#askResults').innerHTML=`<div class="answer-card"><div class="answer-header"><strong>${svg('check-circle')} Database-verified answer</strong><span class="planner-badge">${safe(result.planner==='llm'?'LLM PLANNER':result.planner==='rules_fallback'?'RULES FALLBACK':'RULES PLANNER')}</span></div><p class="answer-question">${safe(result.question)}</p><p class="answer-text">${safe(result.verified_answer)}</p></div><div class="evidence-heading"><span>Evidence from SQLite</span><span class="evidence-count">${num(result.row_count)} row(s) returned</span></div>${table}<details class="sql-details"><summary>View executed SQL &amp; query plan</summary><pre class="sql-code">${safe(result.sql)}</pre><div class="sql-params"><strong>Bound parameters:</strong> ${safe(JSON.stringify(result.sql_parameters))}<br><strong>Validated plan:</strong> ${safe(JSON.stringify(result.interpreted_plan,null,2))}</div></details><p class="detail-note">${safe(result.evidence)}</p>`;
  }

  async function loadRoadmap(){
    const btn=$('#planSubmit');
    const budget=Number($('#planBudget').value)*1000000;
    const price=Number($('#planPrice').value);
    const strategy=$('#planStrategy').value;
    if(!Number.isFinite(budget)||budget<100000||budget>2000000000 || !Number.isFinite(price)||price<.1||price>10){toast('Enter a valid budget and energy price.');return;}
    btn.disabled=true;btn.textContent='Calculating…';
    $('#roadmapKpis').innerHTML='<div class="empty-placeholder">Calculating constrained budget allocations…</div>';
    try{
      const query=new URLSearchParams({annual_budget_dkk:String(budget),strategy,energy_price_dkk_kwh:String(price),start_year:'2027',end_year:'2030'});
      const r=await fetchJSON('/planning/roadmap?'+query);
      const t=r.totals;
      $('#roadmapKpis').innerHTML=[
        ['Funded interventions',num(t.funded_interventions),'Across 2027–2030'],
        ['Scenario investment',shortDKK(t.investment_dkk)+' DKK','Four-year allocation'],
        ['Annual energy avoided',num(t.annual_energy_savings_kwh)+' kWh','If all funded measures perform as assumed'],
        ['Unfunded backlog',shortDKK(t.unfunded_cost_dkk)+' DKK',num(t.unfunded_interventions)+' additional interventions']
      ].map(x=>`<div class="roadmap-stat"><small>${safe(x[0])}</small><strong>${safe(x[1])}</strong><span>${safe(x[2])}</span></div>`).join('');
      $('#roadmapTimeline').innerHTML=r.years.map(y=>`<div class="roadmap-year"><div class="roadmap-year-header"><strong>${y.year}</strong><span>${num(y.funded_interventions)} interventions · ${shortDKK(y.investment_dkk)} / ${shortDKK(y.budget_dkk)} DKK</span></div><div class="roadmap-progress"><div style="width:${Math.min(100,100*y.investment_dkk/y.budget_dkk)}%"></div></div><div class="roadmap-year-foot"><span>Estimated energy savings: ${num(y.annual_energy_savings_kwh)} kWh/year</span><span>Unspent: ${shortDKK(y.unspent_dkk)} DKK</span></div></div>`).join('');
      const rows=r.selected_preview;
      $('#roadmapCounter').textContent=`${num(t.funded_interventions)} funded · first ${rows.length} displayed`;
      $('#roadmapProjects').innerHTML=rows.length?`<table class="roadmap-table"><thead><tr><th>YEAR</th><th>PROPERTY / ASSET</th><th>INVESTMENT</th><th>ANNUAL ENERGY</th><th>PRIORITY</th></tr></thead><tbody>${rows.map(x=>`<tr><td>${x.year}</td><td><button type="button" data-property="${safe(x.property_id)}">${safe(x.property_name)}</button><span>${safe(x.asset_name)}${x.prerequisite_intervention_id?' · dependency':''}</span></td><td>${dkk(x.cost_dkk)}</td><td>${num(x.estimated_savings_kwh_year)} kWh</td><td>${num(x.priority_score)}</td></tr>`).join('')}</tbody></table>`:'<p class="empty-placeholder">No interventions fit this budget. Try a larger budget or different strategy.</p>';
      $('#roadmapDisclaimer').textContent=r.methodology;
      state.roadmapLoaded=true;
    }catch(err){
      $('#roadmapKpis').innerHTML=`<div class="alert" role="alert">${safe(err.message)}</div>`;
    }finally{btn.disabled=false;btn.innerHTML='Calculate roadmap '+svg('arrow-up-right');}
  }

  function navigate(view,updateHash=true){
    const supported=['overview','properties','intelligence','planning','method'];
    if(!supported.includes(view))view='overview';
    state.view=view;
    document.querySelectorAll('.view').forEach(el=>el.classList.toggle('active',el.id==='view-'+view));
    document.querySelectorAll('.nav-link[data-view]').forEach(el=>{ const current=el.dataset.view===view;el.classList.toggle('active',current); if(current)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current'); });
    $('#breadcrumb').textContent={overview:'OVERVIEW',properties:'PROPERTY EXPLORER',intelligence:'ASK INTELLIGENCE',planning:'INVESTMENT ROADMAP',method:'METHODOLOGY'}[view];
    if(updateHash && window.location.hash!=='#'+view)history.pushState(null,'','#'+view);
    $('#sidebar').classList.remove('mobile-open');$('#mobileShade').classList.remove('mobile-open');
    window.scrollTo({top:0,behavior:'instant'});
    if(view==='properties')loadProperties();
    if(view==='planning' && !state.roadmapLoaded)loadRoadmap();
  }
  function setListeners(){
    document.addEventListener('click',event=>{
      const route=event.target.closest('[data-view],[data-go]');
      if(route){navigate(route.dataset.view||route.dataset.go);return;}
      const prop=event.target.closest('[data-property]');
      if(prop){openProperty(prop.dataset.property);return;}
      const suggestion=event.target.closest('[data-question]');
      if(suggestion){$('#questionInput').value=suggestion.dataset.question;$('#questionInput').focus();return;}
    });
    document.addEventListener('keydown',event=>{
      if(event.key==='Escape' && $('#propertyDrawer').classList.contains('open'))closeProperty();
      if((event.key==='Enter'||event.key===' ') && event.target.matches('tr[data-property]')){event.preventDefault();openProperty(event.target.dataset.property);}
      if(event.key==='Tab' && $('#propertyDrawer').classList.contains('open')){
        const focusables=Array.from($('#propertyDrawer').querySelectorAll('button:not(:disabled),a[href],input:not(:disabled)'));
        if(!focusables.length)return;
        const first=focusables[0],last=focusables[focusables.length-1];
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
      }
    });
    $('#drawerClose').addEventListener('click',closeProperty);
    $('#drawerShade').addEventListener('click',closeProperty);
    $('#menuButton').addEventListener('click',()=>{$('#sidebar').classList.add('mobile-open');$('#mobileShade').classList.add('mobile-open');});
    $('#mobileShade').addEventListener('click',()=>{$('#sidebar').classList.remove('mobile-open');$('#mobileShade').classList.remove('mobile-open');});
    $('#refreshButton').addEventListener('click',()=>{loadOverview();toast('Refreshing dashboard data…');});
    $('#retryButton').addEventListener('click',()=>{loadOverview();if(state.view==='properties')loadProperties();});
    ['typeFilter','districtFilter','ratingFilter','priorityFilter','sortProperties'].forEach(id=>$('#'+id).addEventListener('change',()=>{state.page=1;loadProperties();}));
    $('#propertySearch').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.page=1;loadProperties();},300);});
    $('#prevPage').addEventListener('click',()=>{if(state.page>1){state.page--;loadProperties();}});
    $('#nextPage').addEventListener('click',()=>{if(state.page<state.pages){state.page++;loadProperties();}});
    $('#askForm').addEventListener('submit',e=>{e.preventDefault();ask($('#questionInput').value);});
    $('#planningForm').addEventListener('submit',e=>{e.preventDefault();loadRoadmap();});
    window.addEventListener('popstate',()=>navigate(location.hash.slice(1)||'overview',false));
    window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)||'overview',false));
  }

  enhanceIcons();
  setListeners();
  navigate(location.hash.slice(1)||'overview',false);
  loadOverview();
})();

import { renderTrafficChart, shortNumber, periodLabel } from './traffic-chart.js';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.119.0';
const url='https://yqmrunstyhrhnvxoyrap.supabase.co'; // Supabase Project URL (public)
const publishableKey='sb_publishable_HqkcpvBz8P8KJTZFgefrWQ_rFxKPMNh'; // sb_publishable_... (public, never secret/service_role)
const $=id=>document.getElementById(id);
if(url&&publishableKey){
  $('setup').classList.add('hide');
  const supabase=createClient(url,publishableKey);
  document.querySelectorAll('.admin-nav button').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('.admin-nav button').forEach(b=>b.classList.toggle('active',b===button));document.querySelectorAll('.admin-panel').forEach(panel=>panel.classList.toggle('active',panel.id==='panel-'+button.dataset.panel));}));
  const seoBase='https://cozyloops.site/';
  $('check-seo-health').addEventListener('click',async()=>{
    const button=$('check-seo-health'),notice=$('seo-health-message');
    button.disabled=true;
    notice.className='notice';notice.textContent='Checking live SEO files...';
    $('seo-page-count').textContent='—';$('seo-sitemap-count').textContent='—';
    try{
      const [manifestResponse,sitemapResponse]=await Promise.all([
        fetch('../posts/manifest.json',{cache:'no-store'}),
        fetch('../sitemap.xml',{cache:'no-store'})
      ]);
      if(!manifestResponse.ok||!sitemapResponse.ok)throw Error('One of the public SEO files is unavailable (HTTP '+manifestResponse.status+'/'+sitemapResponse.status+').');
      const slugs=await manifestResponse.json(),xml=await sitemapResponse.text();
      if(!Array.isArray(slugs)||!slugs.every(v=>typeof v==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(v)))throw Error('Article manifest is not valid.');
      const parsed=new DOMParser().parseFromString(xml,'application/xml');
      if(parsed.querySelector('parsererror'))throw Error('Sitemap XML is invalid.');
      const urls=Array.from(parsed.getElementsByTagName('loc'),node=>node.textContent.trim());
      const expected=new Set([seoBase,...slugs.map(slug=>seoBase+'posts/'+slug+'/')]);
      $('seo-page-count').textContent=String(slugs.length);$('seo-sitemap-count').textContent=String(urls.length);
      if(urls.length!==expected.size||urls.some(url=>!expected.has(url)))throw Error('Sitemap and published SEO article list do not match.');
      notice.textContent='SEO files verified: '+slugs.length+' generated pages and '+urls.length+' unique sitemap URLs. Google indexing is not verified.';
      notice.className='success';
    }catch(err){notice.textContent='SEO health check: '+err.message;notice.className='error';}
    finally{button.disabled=false;}
  });
  const postForm=$('post-form'),postList=$('posts-list'),postMsg=$('posts-message');
  let postRows=[],editingPost=null,editingGitHubSource=false;
  const slugify=v=>v.toLowerCase().trim().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,180);
  const postField=k=>$('post-'+k);
  let analyticsPeriod='30d', analyticsRequest=0;
  const loadVisitorAnalytics=async()=>{
    const request=++analyticsRequest;
    const msg=$('visitor-analytics-message'),root=$('visitor-stats'),top=$('top-viewed-posts'),chart=$('traffic-chart');
    const period=analyticsPeriod;
    document.querySelectorAll('[data-analytics-range]').forEach(button=>{
      const selected=button.dataset.analyticsRange===period;
      button.classList.toggle('active',selected);
      button.setAttribute('aria-pressed',String(selected));
    });
    $('traffic-chart-title').textContent='Page view trend · '+(periodLabel[period]||'Selected period');
    $('top-articles-period').textContent='('+String(periodLabel[period]||'Selected period').toLowerCase()+')';
    $('traffic-chart-zone').textContent=period==='1h'?'5-minute buckets':period==='1d'?'Hourly buckets':'Daily buckets · UTC';
    msg.textContent='Loading traffic for '+(periodLabel[period]||period).toLowerCase()+'...';msg.className='muted';
    chart.replaceChildren();root.replaceChildren();top.replaceChildren();
    $('traffic-chart-compare').textContent='';
    const loading=document.createElement('p');loading.className='muted';loading.textContent='Loading real page views...';chart.append(loading);
    let data,error;
    try{
      ({data,error}=await supabase.rpc('cozyloop_analytics_range',{p_period:period}));
    }catch(err){error=err;}
    if(request!==analyticsRequest)return;
    chart.replaceChildren();
    if(error||!data||!Array.isArray(data.series)){
      msg.textContent='Time-range analytics require the owner-only Supabase setup. Run supabase/page_view_analytics_range.sql in your project SQL Editor after page_view_analytics.sql. '+(error?.message?'('+error.message+')':'');
      msg.className='error';
      const setupLink=document.createElement('a');
      setupLink.href='https://github.com/houssamel4ur-lang/crochet/blob/main/supabase/page_view_analytics_range.sql';
      setupLink.target='_blank';setupLink.rel='noopener noreferrer';
      setupLink.textContent='Open analytics SQL ↗';
      msg.append(document.createTextNode(' '),setupLink);
      const p=document.createElement('p');p.className='muted';
      p.textContent='No chart data available. Existing recorded views are not deleted.';
      chart.append(p);
      return;
    }
    const metrics=[
      ['Page views',data.total_page_views],
      ['Home views',data.home_views],
      ['Article views',data.article_views],
      ['Previous period',data.previous_page_views]
    ];
    for(const [name,value] of metrics){
      const box=document.createElement('div');box.className='stat-box';
      const num=document.createElement('strong');num.textContent=shortNumber(value);
      const label=document.createElement('span');label.textContent=name;
      box.append(num,label);root.append(box);
    }
    renderTrafficChart(chart,data.series,period);
    const current=Number(data.total_page_views)||0,previous=Number(data.previous_page_views)||0;
    const difference=current-previous;
    const comparison=$('traffic-chart-compare');
    comparison.textContent=previous>0
      ?(difference>=0?'+':'')+((difference/previous)*100).toFixed(1)+'% vs the previous equivalent period ('+shortNumber(previous)+' tracked views).'
      :current>0?'No recorded views in the previous equivalent period.':'No tracked views in either period.';
    const values=Array.isArray(data.top_articles)?data.top_articles:[];
    if(!values.length){
      const p=document.createElement('p');p.textContent='No tracked article views in this period.';top.append(p);
    }else{
      const list=document.createElement('ol');list.className='summary-list';
      for(const item of values){
        const article=postRows.find(p=>p.slug===item.slug);
        const row=document.createElement('li');row.textContent=(article?.title||item.slug)+' — '+shortNumber(item.views)+' views';list.append(row);
      }
      top.append(list);
    }
    msg.textContent='Updated · '+new Date().toLocaleTimeString()+' · Based on consenting, daily-deduplicated page views.';
    msg.className='muted';
  };
  document.querySelectorAll('[data-analytics-range]').forEach(button=>button.addEventListener('click',()=>{
    if(analyticsPeriod===button.dataset.analyticsRange)return;
    analyticsPeriod=button.dataset.analyticsRange;
    loadVisitorAnalytics();
  }));
  $('analytics-refresh').addEventListener('click',loadVisitorAnalytics);
  const renderStats=()=>{
    const total=postRows.length;
    const published=postRows.filter(p=>p.status==='published').length;
    const drafts=postRows.filter(p=>p.status==='draft'&&!p.scheduled_at).length;
    const groups=[...new Set(postRows.map(p=>p.category).filter(Boolean))].length;
    const values=[['Database posts',total],['Published',published],['Drafts',drafts],['Scheduled',postRows.filter(p=>scheduleLabel(p)==='scheduled').length],['Active sections',groups]];
    for(const id of ['dashboard-stats','analytics-stats']){
      const root=$(id);root.replaceChildren();
      for(const [name,value] of values){
        const box=document.createElement('div');box.className='stat-box';
        const number=document.createElement('strong');number.textContent=String(value);
        const label=document.createElement('span');label.textContent=name;
        box.append(number,label);root.append(box);
      }
    }
    const recent=$('dashboard-recent');recent.replaceChildren();
    for(const p of postRows.slice(0,5)){
      const line=document.createElement('p');line.textContent=p.title+' · '+scheduleLabel(p);recent.append(line);
    }
    if(!postRows.length){const p=document.createElement('p');p.className='notice';p.textContent='No database posts yet.';recent.append(p);}
    const byCategory=new Map();
    for(const p of postRows){const name=p.category||'Uncategorized';byCategory.set(name,(byCategory.get(name)||0)+1);}
    const categoriesRoot=$('analytics-categories');categoriesRoot.replaceChildren();
    if(!byCategory.size){const p=document.createElement('p');p.textContent='No article categories yet.';categoriesRoot.append(p);}
    else{
      const list=document.createElement('ul');list.className='summary-list';
      for(const [name,count] of [...byCategory].sort((a,b)=>b[1]-a[1])){const item=document.createElement('li');item.textContent=name+': '+count+' post(s)';list.append(item);}
      categoriesRoot.append(list);
    }
  };
  // These six starter articles were deliberately deleted by the owner.
  const permanentlyRemovedSlugs=new Set(["crochet-for-absolute-beginners","how-to-read-crochet-patterns","easy-crochet-scarf-guide","amigurumi-basics","choosing-crochet-yarn","crochet-stitch-counting"]);
  let postListFilter='all';
  document.querySelectorAll('[data-post-filter]').forEach(button=>button.addEventListener('click',()=>{
    postListFilter=button.dataset.postFilter;
    postForm.classList.add('hide');postList.classList.remove('hide');
    loadPosts();
  }));
  let githubEditorPosts=[],githubPublishedSlugs=new Set(),editorialCatalogLoaded=false;
  let schedulerReady=false, schedulerInstalled=false, editingPublished=false, originalPostSlug='';
  const scheduleZone=Intl.DateTimeFormat().resolvedOptions().timeZone;
  const scheduleLabel=post=>post.status==='draft'&&post.scheduled_at?'scheduled':post.status||'draft';
  const scheduleDate=value=>new Date(value).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'})+' ('+scheduleZone+')';
  const localInput=value=>{const date=new Date(value);return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);};
  const updateScheduleFields=()=>{
    const scheduled=postField('status').value==='scheduled';
    $('post-schedule-fields').classList.toggle('hide',!scheduled);
    $('post-scheduled-at').required=scheduled;
    $('post-schedule-zone').textContent='Timezone: '+scheduleZone+'. The selected time is saved as UTC. Automatic publishing runs every minute; SEO pages update on the hourly build.';
    const value=$('post-scheduled-at').value,date=new Date(value);
    $('post-schedule-preview').textContent=scheduled&&value&&!Number.isNaN(date.getTime())?'Publish on '+scheduleDate(date):'';
  };
  postField('status').addEventListener('change',updateScheduleFields);
  $('post-scheduled-at').addEventListener('input',updateScheduleFields);
  const checkScheduler=async()=>{
    schedulerReady=false;schedulerInstalled=false;
    try{const {data,error}=await supabase.rpc('article_scheduler_status');schedulerInstalled=!error&&typeof data==='boolean';schedulerReady=schedulerInstalled&&data===true;}catch{}
    postField('status').querySelector('option[value="scheduled"]').disabled=!schedulerReady;
    $('scheduler-health').textContent=schedulerReady?'Automatic publishing is active. Schedule a new article or an unpublished draft.':'Automatic publishing needs server activation. Normal draft and published saves remain available.';
  };
  const loadPosts=async()=>{
    postMsg.textContent='Loading posts...';postMsg.className='';
    const {data,error}=await supabase.from('articles')
      .select('*')
      .order('created_at',{ascending:false});
    if(error){postMsg.textContent='Could not load posts: '+error.message;postMsg.className='error';return;}
    await checkScheduler();
    postRows=(data||[]).filter(p=>!permanentlyRemovedSlugs.has(p.slug));
    githubEditorPosts=[];editorialCatalogLoaded=false;
    try{
      const response=await fetch('../content/github_articles.json',{cache:'no-store'});
      if(!response.ok)throw Error('GitHub article catalog returned '+response.status);
      const items=await response.json();
      if(!Array.isArray(items))throw Error('GitHub article catalog is not a list');
      githubPublishedSlugs=new Set(items.filter(p=>p?.status==='published').map(p=>p.slug));editorialCatalogLoaded=true;
      const savedSlugs=new Set(postRows.map(p=>p.slug));
      githubEditorPosts=items.filter(p=>p&&p.status==='published'&&typeof p.slug==='string'
        &&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(p.slug)
        &&!permanentlyRemovedSlugs.has(p.slug)&&!savedSlugs.has(p.slug)
        &&typeof p.content==='string'&&p.content.trim());
    }catch(error){console.warn('Could not load GitHub editorial articles:',error.message);}
    updatePostSections();renderStats();loadVisitorAnalytics();
    postMsg.textContent=postRows.length+' Supabase post(s), '+githubEditorPosts.length+' GitHub article(s) available for editing.';
    postList.replaceChildren();
    const scheduled=postRows.filter(p=>p.status==='draft'&&p.scheduled_at).sort((a,b)=>new Date(a.scheduled_at)-new Date(b.scheduled_at));
    $('scheduled-posts-nav').textContent='🗓 Scheduled ('+scheduled.length+')';
    $('posts-heading').textContent=postListFilter==='scheduled'?'Scheduled Posts':'Posts';
    if(postListFilter==='scheduled')postMsg.textContent=scheduled.length+' scheduled post(s), ordered by publication time. Use Edit to change the time or save as Draft to cancel.';
    const displayed=postListFilter==='scheduled'?scheduled:[...githubEditorPosts,...postRows];
    if(!displayed.length){
      const p=document.createElement('p');p.className='notice';
      p.textContent=postListFilter==='scheduled'?'No scheduled posts yet. Create a post and choose Scheduled to set its publication time.':'No posts yet. Click New Post to create one.';postList.append(p);
    }
    for(const post of displayed){
      const isGithub=githubEditorPosts.includes(post);
      const row=document.createElement('div');row.className='post-row';
      const name=document.createElement('strong');name.textContent=post.title;
      const info=document.createElement('small');
      info.textContent=(post.category||'Uncategorized')+' · '+scheduleLabel(post)+' · '+post.slug+(post.scheduled_at&&post.status==='draft'?' · '+scheduleDate(post.scheduled_at):'')
        +(isGithub?' · GitHub article (not yet in Supabase)':'');
      const actions=document.createElement('div');actions.className='post-actions';
      const edit=document.createElement('button');edit.type='button';edit.className='secondary';
      edit.textContent=isGithub?'Edit & Import':'Edit';
      if(isGithub)edit.classList.add('editorial-import');
      edit.addEventListener('click',()=>openPost(post));
      actions.append(edit);
      if(!isGithub){
        const del=document.createElement('button');del.type='button';del.className='danger';
        del.textContent='Delete';del.addEventListener('click',()=>deletePost(post));
        actions.append(del);
      }
      row.append(name,info,actions);postList.append(row);
    }
  };
  const insertPostText=(before,after='')=>{
    const area=postField('content'),start=area.selectionStart,end=area.selectionEnd,selected=area.value.slice(start,end);
    area.setRangeText(before+(selected||'Your text')+after,start,end,'select');area.focus();
  };
  $('post-add-article-section').addEventListener('click',()=>{
    const name=prompt('Article section heading (for example: Materials & Tools):');
    if(name===null)return;
    const heading=name.trim().replace(/^#+\s*/, '').replace(/\s+/g,' ');
    if(!heading||heading.length>120){
      $('post-form-message').textContent='Section heading must have 1–120 characters.';
      $('post-form-message').className='error';return;
    }
    const area=postField('content');
    const at=area.selectionStart;
    const prefix=area.value.slice(0,at).endsWith('\n\n')?'':'\n\n';
    const text=prefix+'## '+heading+'\n\nWrite this section here.\n\n';
    area.setRangeText(text,at,area.selectionEnd,'end');
    const start=at+text.indexOf('Write this section here.');
    area.setSelectionRange(start,start+'Write this section here.'.length);
    area.focus();
    $('post-form-message').textContent='Section added. Replace the placeholder, then save the post.';
    $('post-form-message').className='success';
  });
  $('post-insert-heading').addEventListener('click',()=>insertPostText('## '));
  $('post-insert-list').addEventListener('click',()=>insertPostText('- '));
  $('post-insert-bold').addEventListener('click',()=>insertPostText('**','**'));
  $('post-insert-image').addEventListener('click',()=>{
    const url=prompt('Paste image HTTPS URL:');if(url===null)return;
    try{const u=new URL(url.trim());if(u.protocol!=='https:')throw Error('Use HTTPS.');
      const alt=prompt('Image description (alt text):')||'Crochet project';
      insertPostText('![',']('+u.href+')');
      const area=postField('content'),selected=area.value.slice(area.selectionStart,area.selectionEnd);
      area.setRangeText(alt,area.selectionStart,area.selectionEnd,'end');
    }catch(err){$('post-form-message').textContent='Invalid image URL: '+err.message;$('post-form-message').className='error';}
  });
  const previewInline=value=>{
    const escapeText=str=>String(str).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const pieces=String(value).split(/(!\[[^\]]*\]\(https:\/\/[^\s)]+\))/g);
    return pieces.map(part=>{
      const image=part.match(/^!\[([^\]]*)\]\((https:\/\/[^\s)]+)\)$/);
      if(image)return '<img loading="lazy" style="max-width:100%;border-radius:12px;margin:12px 0" src="'+escapeText(image[2])+'" alt="'+escapeText(image[1])+'">';
      return escapeText(part).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
    }).join('');
  };
  const renderPreview=source=>String(source).split(/\n\s*\n/).map(block=>{
    const lines=block.split(/\n/);
    if(lines.every(line=>/^[-*] /.test(line.trim())))return '<ul>'+lines.map(line=>'<li>'+previewInline(line.trim().slice(2))+'</li>').join('')+'</ul>';
    return lines.map(line=>{
      const match=line.match(/^(#{1,3})\s+(.+)$/);
      if(match){const level=Math.min(3,Math.max(2,match[1].length));return '<h'+level+'>'+previewInline(match[2])+'</h'+level+'>';}
      return '<p>'+previewInline(line)+'</p>';
    }).join('');
  }).join('');
  $('post-preview-toggle').addEventListener('click',()=>{
    const preview=$('post-preview');preview.classList.toggle('hide');
    if(!preview.classList.contains('hide'))preview.innerHTML=renderPreview(postField('content').value);
  });
  postField('content').addEventListener('input',()=>{
    if(!$('post-preview').classList.contains('hide'))$('post-preview').innerHTML=renderPreview(postField('content').value);
  });
  const imageBucket='ARTICLE IMAGE';
  const uploadArticleImage=async (file,kind='inline')=>{
    if(!file)throw Error('Select an image first.');
    const allowed=['image/jpeg','image/png','image/webp','image/gif'];
    if(!allowed.includes(file.type))throw Error('Only JPG, PNG, WebP and GIF images are allowed.');
    if(file.size===0)throw Error('The selected file is empty.');
    if(file.size>5*1024*1024)throw Error('Image must be smaller than 5 MB.');
    const bytes=new Uint8Array(await file.slice(0,16).arrayBuffer());
    const startsWith=(pattern)=>pattern.every((byte,index)=>bytes[index]===byte);
    const actualType=startsWith([0xff,0xd8,0xff])?'image/jpeg':
      startsWith([0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a])?'image/png':
      startsWith([0x47,0x49,0x46,0x38])?'image/gif':
      startsWith([0x52,0x49,0x46,0x46])&&String.fromCharCode(...bytes.slice(8,12))==='WEBP'?'image/webp':'';
    if(actualType!==file.type)throw Error('The file contents do not match the claimed image format.');
    if(file.type==='image/gif')throw Error('Animated GIF uploads are not supported for editorial photos. Use a JPG, PNG or WebP still image.');
    // Convert legitimate photos to efficient WebP while preserving their content.
    let bitmap;
    try{bitmap=await createImageBitmap(file);}catch{throw Error('The image could not be decoded. Export it again as a valid JPG, PNG or WebP.');}
    let converted;
    try{
      if(bitmap.width>8000||bitmap.height>8000)throw Error('Image dimensions are too large; maximum 8000 px per side.');
      const minWidth=kind==='cover'?900:640;
      if(bitmap.width<minWidth)throw Error('This '+kind+' image is blurry at article size. Upload at least '+minWidth+' px width.');
      const scale=Math.min(1,1800/Math.max(bitmap.width,bitmap.height));
      const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(bitmap.width*scale));canvas.height=Math.max(1,Math.round(bitmap.height*scale));
      const ctx=canvas.getContext('2d');if(!ctx)throw Error('Image optimization is unavailable in this browser.');
      ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
      converted=await new Promise(resolve=>canvas.toBlob(resolve,'image/webp',.87));
      if(!converted||converted.type!=='image/webp')throw Error('WebP conversion failed.');
    }finally{bitmap.close();}
    const path='posts/'+crypto.randomUUID()+'.webp';
    const {error}=await supabase.storage.from(imageBucket).upload(path,converted,{contentType:'image/webp',upsert:false});
    if(error)throw error;
    const {data}=supabase.storage.from(imageBucket).getPublicUrl(path);
    if(!data?.publicUrl)throw Error('Image uploaded but no public URL was returned.');
    return data.publicUrl;
  };
  $('upload-cover').addEventListener('click',async()=>{
    const btn=$('upload-cover'),msg=$('post-upload-message');btn.disabled=true;msg.textContent='Uploading image...';msg.className='muted';
    try{
      const url=await uploadArticleImage($('post-cover-file').files[0],'cover');
      postField('image').value=url;msg.textContent='Cover uploaded successfully. Save the post to use it.';msg.className='success';
    }catch(err){msg.textContent='Upload failed: '+err.message;msg.className='error';}
    finally{btn.disabled=false;}
  });
  $('post-upload-inline').addEventListener('click',()=>$('post-inline-file').click());
  $('post-inline-file').addEventListener('change',async()=>{
    const input=$('post-inline-file'),btn=$('post-upload-inline'),msg=$('post-upload-message');
    if(!input.files?.length)return;
    btn.disabled=true;msg.textContent='Uploading inline image...';msg.className='muted';
    try{
      const file=input.files[0],url=await uploadArticleImage(file);
      const alt=file.name.replace(/\.[^.]+$/,'').replace(/[-_]/g,' ').replace(/[\[\]()]/g,' ');
      const area=postField('content'),start=area.selectionStart,end=area.selectionEnd;
      area.setRangeText('\n\n!['+alt+']('+url+')\n\n',start,end,'end');
      area.dispatchEvent(new Event('input'));msg.textContent='Image inserted. Save the post to publish it.';msg.className='success';
    }catch(err){msg.textContent='Upload failed: '+err.message;msg.className='error';}
    finally{btn.disabled=false;input.value='';}
  });
  const defaultSections=['Beginner Tutorials','Free Patterns','Amigurumi','Crochet Tips'];
  const updatePostSections=()=>{
    const select=postField('category'),current=select.value;
    const sections=[...new Set([...defaultSections,...postRows.map(p=>p.category).filter(Boolean)])];
    select.replaceChildren();
    for(const name of sections){const option=document.createElement('option');option.value=name;option.textContent=name;select.append(option);}
    if(sections.includes(current))select.value=current;
  };
  $('add-post-section').addEventListener('click',()=>{
    const raw=prompt('New section name (e.g. Crochet Bags):');
    if(raw===null)return;
    const name=raw.trim().replace(/\\s+/g,' ');
    if(!name||name.length>70){$('post-form-message').textContent='Section name must be 1–70 characters.';$('post-form-message').className='error';return;}
    const select=postField('category');
    const existing=[...select.options].find(o=>o.value.toLowerCase()===name.toLowerCase());
    if(existing){select.value=existing.value;return;}
    const option=document.createElement('option');option.value=name;option.textContent=name;select.append(option);select.value=name;
    $('post-form-message').textContent='Section added to this post. Save the post to keep it.';$('post-form-message').className='success';
  });
  const openPost=(post=null)=>{
    editingPublished=post?.status==='published';
    originalPostSlug=post?.slug||'';
    editingPost=post?.id||null;
    editingGitHubSource=!!post&&!post.id;
    postForm.reset();$('post-preview').classList.add('hide');updatePostSections();postField('slug').dataset.auto='true';postForm.classList.remove('hide');postList.classList.add('hide');
    $('post-form-heading').textContent=editingGitHubSource?'Edit & Import GitHub Article':post?'Edit Post':'New Post';
    for(const key of ['title','slug','category','excerpt','content','status'])if(post&&post[key]!=null)postField(key).value=post[key];
    postField('image').value=post?.image_url||'';
    if(post?.status==='draft'&&post.scheduled_at){postField('status').value='scheduled';$('post-scheduled-at').value=localInput(post.scheduled_at);}
    updateScheduleFields();
    $('post-form-message').textContent=editingGitHubSource?'This article is on GitHub. Save to import it into Supabase and edit it from Posts. Keep the slug unchanged to preserve its URL.':'';postField('title').focus();
  };
  $('new-post').addEventListener('click',()=>openPost());
  $('refresh-posts').addEventListener('click',loadPosts);
  $('cancel-post').addEventListener('click',()=>{postForm.classList.add('hide');postList.classList.remove('hide');});
  postField('title').addEventListener('input',()=>{
    if(!editingPost&&(!postField('slug').value||postField('slug').dataset.auto==='true')){
      postField('slug').value=slugify(postField('title').value);postField('slug').dataset.auto='true';
    }
  });
  postField('slug').addEventListener('input',()=>{postField('slug').dataset.auto='false';});
  postForm.addEventListener('submit',async e=>{
    e.preventDefault();const btn=$('save-post'),msg=$('post-form-message');btn.disabled=true;msg.textContent='Saving...';msg.className='';
    try{
      const title=postField('title').value.trim(),slug=postField('slug').value.trim().toLowerCase();
      if(editingGitHubSource&&!confirm('Import this GitHub article into Supabase using its current URL?')){msg.textContent='Import cancelled.';return;}
      const image=postField('image').value.trim();
      if(!title||!slug||!postField('content').value.trim())throw Error('Title, slug and content are required.');
      if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug))throw Error('Slug must use lowercase letters, numbers and hyphens.');
      if(image){const u=new URL(image);if(u.protocol!=='https:'||!u.hostname)throw Error('Image URL must use HTTPS.');}
      const payload={title,slug,category:postField('category').value,excerpt:postField('excerpt').value.trim(),content:postField('content').value.trim(),image_url:image||null,status:postField('status').value};
      const mode=postField('status').value;
      if(editingPublished&&originalPostSlug!==slug)throw Error('Published article URLs cannot be renamed here. Keep the original slug to protect search rankings and incoming links.');
      // Existing public articles must remain editable even when their historic assets
      // predate the stricter image standard; apply the gate to new publications.
      if(mode==='published'&&!editingPublished&&!editingGitHubSource&&!githubPublishedSlugs.has(slug)){
        const wordCount=(payload.content.match(/\b[\w'-]+\b/g)||[]).length;
        const headings=(payload.content.match(/^##\s+.+/gm)||[]).length;
        const photos=[...payload.content.matchAll(/!\[([^\]]+)\]\((https:\/\/[^\s)]+)\)/g)];
        if(!image)throw Error('Publish checklist: add a cover image first.');
        if(title.length<20||title.length>95)throw Error('Publish checklist: use a descriptive article title (20–95 characters).');
        if(payload.excerpt.length<70||payload.excerpt.length>180)throw Error('Publish checklist: write a unique 70–180 character summary.');
        if(headings<3)throw Error('Publish checklist: include at least three useful main sections (## Heading).');
        if(wordCount<300)throw Error('Publish checklist: add substantial, original step-by-step content before publishing.');
        const isWebP=url=>/\.webp(?:\?.*)?$/i.test(new URL(url).pathname);
        if(!isWebP(image)||photos.filter(m=>isWebP(m[2])).length<2)
          throw Error('Publish checklist: include a WebP cover and at least two descriptive WebP images inside the article.');
      }
      if(mode==='scheduled'){
        await checkScheduler();
        if(!schedulerReady)throw Error('Automatic publishing is not active. Activate the server scheduler first.');
        if(!editorialCatalogLoaded)throw Error('Could not verify existing public URLs. Refresh Posts before scheduling.');
        if(editingPublished||editingGitHubSource||githubPublishedSlugs.has(slug))throw Error('Scheduling is for new articles and unpublished drafts. This URL is already published on GitHub.');
        const date=new Date($('post-scheduled-at').value);
        if(!Number.isFinite(date.getTime())||date.getTime()<=Date.now()+60000)throw Error('Choose a publication time at least one minute in the future.');
        payload.status='draft';payload.scheduled_at=date.toISOString();
      }else if(schedulerInstalled){payload.scheduled_at=null;}
      const result=editingPost?await supabase.from('articles').update(payload).eq('id',editingPost).select('id'):await supabase.from('articles').insert(payload).select('id');
      if(result.error)throw result.error;
      if(!result.data?.length)throw Error('No article was saved.');
      postForm.classList.add('hide');postList.classList.remove('hide');await loadPosts();
      postMsg.textContent=mode==='scheduled'?'Post scheduled for '+scheduleDate(payload.scheduled_at)+'. To cancel, edit it and save as Draft.':'Post saved successfully.';postMsg.className='success';
    }catch(err){msg.textContent=err.message;msg.className='error';}
    finally{btn.disabled=false;}
  });
  const deletePost=async post=>{
    if(!confirm('Permanently delete "'+post.title+'"?'))return;
    const {data,error}=await supabase.from('articles').delete().eq('id',post.id).select('id');
    if(error||!data?.length){postMsg.textContent='Delete failed: '+(error?.message||'Permission denied');postMsg.className='error';return;}
    await loadPosts();postMsg.textContent='Post deleted.';postMsg.className='success';
  };
  const themeFields=['site_name','site_description','logo_url','favicon_url','primary_color','secondary_color','background_color','text_color','heading_font','body_font','border_radius'];
  const themeDefaults={primary_color:'#63846d',secondary_color:'#c77d87',background_color:'#fff9f0',text_color:'#29372d'};
  const loadTheme=async()=>{
    const msg=$('theme-message');msg.textContent='';
    const {data,error}=await supabase.from('site_settings').select(themeFields.join(',')).eq('id',1).maybeSingle();
    if(error){msg.textContent='Could not load theme: '+error.message;msg.className='error';return;}
    if(!data){msg.textContent='No site settings row found (id 1).';msg.className='error';return;}
    for(const key of themeFields){const input=$('theme-'+key);const val=data[key];input.value=key.endsWith('_color')?(/^#[0-9a-f]{6}$/i.test(val||'')?val:themeDefaults[key]):(val??'');}
  };
  $('save-theme').addEventListener('click',async()=>{
    const btn=$('save-theme'),msg=$('theme-message');btn.disabled=true;msg.textContent='Saving...';msg.className='';
    try{
      const payload={};
      for(const key of themeFields){
        const input=$('theme-'+key);let value=input.value.trim();
        if(key==='border_radius'){value=value===''?0:Number(value);if(!Number.isInteger(value)||value<0||value>50)throw Error('Corner radius must be 0–50.');}
        if((key==='logo_url'||key==='favicon_url')&&value){const u=new URL(value);if(u.protocol!=='https:')throw Error(key+' must use HTTPS.');}
        if(key.endsWith('_color')&&!/^#[0-9a-f]{6}$/i.test(value))throw Error('Invalid color for '+key);
        payload[key]=value;
      }
      if(!payload.site_name)throw Error('Site name cannot be empty.');
      const {data,error}=await supabase.from('site_settings').update(payload).eq('id',1).select('id');
      if(error)throw error;
      if(!data?.length)throw Error('No settings were updated. Check your Super Admin permissions.');
      msg.textContent='Theme saved successfully.';msg.className='success';
    }catch(err){msg.textContent=err.message;msg.className='error';}
    finally{btn.disabled=false;}
  });
  const platforms=['pinterest','instagram','facebook','tiktok','youtube','whatsapp','email'];
  const socialRows=new Map();
  const socialFields=$('social-fields');
  for(const platform of platforms){
    const section=document.createElement('div');section.className='social-item';
    const label=document.createElement('label');label.htmlFor='social-'+platform;label.textContent=platform.charAt(0).toUpperCase()+platform.slice(1);
    const input=document.createElement('input');input.id='social-'+platform;input.type=platform==='email'?'email':'text';input.placeholder=platform==='email'?'contact@example.com':platform==='whatsapp'?'https://wa.me/123456789':'https://...';
    const visibility=document.createElement('label');visibility.className='visibility';
    const check=document.createElement('input');check.type='checkbox';check.id='visible-'+platform;
    visibility.append(check,document.createTextNode('Visible on website'));
    section.append(label,input,visibility);socialFields.append(section);
  }
  const loadSocial=async()=>{
    $('social-message').textContent='';
    const {data,error}=await supabase.from('social_links').select('id,platform,url,is_visible').in('platform',platforms);
    if(error){$('social-message').textContent='Could not load links: '+error.message;$('social-message').className='error';return;}
    socialRows.clear();
    for(const row of data||[])socialRows.set(row.platform,row);
    for(const platform of platforms){
      const row=socialRows.get(platform);
      $('social-'+platform).value=row?.url||'';
      $('visible-'+platform).checked=!!row?.is_visible;
    }
  };
  const syncContact=()=>{
    for(const p of ['email','whatsapp']){
      $('contact-'+p).value=$('social-'+p).value;
      $('contact-'+p+'-visible').checked=$('visible-'+p).checked;
    }
  };
  $('save-contact').addEventListener('click',async()=>{
    const button=$('save-contact'),msg=$('contact-message');button.disabled=true;msg.textContent='Saving...';msg.className='';
    try{
      for(const p of ['email','whatsapp']){
        const value=$('contact-'+p).value.trim(),visible=$('contact-'+p+'-visible').checked;
        if(visible&&!value)throw Error('Add '+p+' before making it visible.');
        if(p==='email'&&value&&!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(value))throw Error('Invalid email address.');
        if(p==='whatsapp'&&value){const u=new URL(value);if(u.protocol!=='https:'||u.hostname!=='wa.me')throw Error('Use a valid https://wa.me/ WhatsApp link.');}
        const existing=socialRows.get(p);
        const payload={platform:p,url:value,is_visible:visible};
        const result=existing?await supabase.from('social_links').update(payload).eq('id',existing.id):await supabase.from('social_links').insert(payload);
        if(result.error)throw result.error;
      }
      await loadSocial();syncContact();msg.textContent='Contact details saved.';msg.className='success';
    }catch(err){msg.textContent=err.message;msg.className='error';}
    finally{button.disabled=false;}
  });
  $('save-social').addEventListener('click',async()=>{
    const button=$('save-social');button.disabled=true;
    const msg=$('social-message');msg.textContent='Saving...';msg.className='';
    try{
      for(const platform of platforms){
        const value=$('social-'+platform).value.trim(),visible=$('visible-'+platform).checked;
        if(visible&&!value)throw Error('Add a link before making '+platform+' visible.');
        if(value){
          if(platform==='email'){
            if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))throw Error('Invalid email address.');
          }else{
            const parsed=new URL(value);
            if(!['https:','http:'].includes(parsed.protocol))throw Error('Invalid URL for '+platform);
          }
        }
        const existing=socialRows.get(platform);
        const payload={platform,url:value,is_visible:visible};
        const result=existing?await supabase.from('social_links').update(payload).eq('id',existing.id):await supabase.from('social_links').insert(payload);
        if(result.error)throw Error(platform+': '+result.error.message);
      }
      msg.textContent='Changes saved successfully.';msg.className='success';await loadSocial();msg.textContent='Changes saved successfully.';
    }catch(err){msg.textContent=err.message;msg.className='error';}
    finally{button.disabled=false;}
  });
  const show=async()=>{
    const {data,error:authError}=await supabase.auth.getUser();
    const user=authError?null:data?.user;
    let allowed=false;
    if(user){
      const {data:role,error}=await supabase.rpc('is_super_admin');
      allowed=!error&&role===true;
    }
    $('login').classList.toggle('hide',!!user);
    $('dashboard').classList.toggle('hide',!allowed);
    $('denied-logout').classList.toggle('hide',!user||allowed);
    if(allowed){
      $('message').textContent='';
      $('welcome').textContent='Signed in as '+user.email;
      await Promise.all([loadSocial(),loadTheme(),loadPosts()]);
      syncContact();
    }else if(user){
      $('message').textContent='This account does not have Super Admin access.';
      $('message').className='error';
    }else if(authError){
      $('message').textContent='Session could not be verified. Please sign in again.';
      $('message').className='error';
    }
  };
  $('denied-logout').addEventListener('click',async()=>{
    const btn=$('denied-logout');btn.disabled=true;
    try{
      const {error}=await supabase.auth.signOut();
      if(error)throw error;
      $('message').textContent='';
      await show();
    }catch(error){$('message').textContent=error.message;$('message').className='error';}
    finally{btn.disabled=false;}
  });
  $('login').addEventListener('submit',async e=>{
    e.preventDefault();$('message').textContent='';
    const button=$('login').querySelector('button');button.disabled=true;
    try{
      const {error}=await supabase.auth.signInWithPassword({email:$('email').value,password:$('password').value});
      if(error)throw error;
      $('password').value='';await show();
    }catch(err){$('message').textContent=err.message;$('message').className='error';}
    finally{button.disabled=false;}
  });
  $('logout').addEventListener('click',async()=>{await supabase.auth.signOut();$('message').textContent='';await show();});
  await show();
}

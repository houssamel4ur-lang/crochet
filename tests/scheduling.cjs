// All writes remain in memory. Run with the local site served on port 8765.
const {chromium}=require('playwright');
const fs=require('fs');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  try{
    for(const active of [false,true]){
      const page=await browser.newPage({timezoneId:'Africa/Casablanca',viewport:{width:390,height:844}});
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      const mock=fs.readFileSync('tests/mock-admin-supabase.mjs','utf8').replace("name==='is_super_admin'?", "name==='article_scheduler_status'?{data:"+active+",error:null}:name==='is_super_admin'?");
      await page.route('https://esm.sh/@supabase/supabase-js@2',r=>r.fulfill({contentType:'application/javascript',body:mock}));
      await page.goto('http://127.0.0.1:8765/admin/');
      await page.locator('#dashboard').waitFor({state:'visible'});
      await page.locator('[data-panel="posts"][data-post-filter="all"]').click();
      await page.waitForFunction(()=>!document.querySelector('#scheduler-health').textContent.includes('Checking'));
      assert.equal(await page.locator('option[value="scheduled"]').isDisabled(),!active);
      await page.locator('#new-post').click();
      await page.locator('#post-title').fill('Schedule regression article');
      await page.locator('#post-excerpt').fill('A mock-only scheduled draft.');
      await page.locator('#post-content').fill('## Instructions\n\nChain ten.');
      if(active){
        await page.locator('#post-status').selectOption('scheduled');
        await page.locator('#post-scheduled-at').fill('2020-01-01T12:00');
        await page.locator('#save-post').click();
        await page.getByText('Choose a publication time at least one minute in the future.').waitFor();
        assert.equal(await page.evaluate(()=>window.__mockAdminRows.length),0);
        const target=await page.evaluate(()=>{const d=new Date(Date.now()+3600000);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16)});
        await page.locator('#post-scheduled-at').fill(target);
        await page.locator('#save-post').click();
        await page.waitForFunction(()=>window.__mockAdminRows.length===1);
        const row=await page.evaluate(()=>window.__mockAdminRows[0]);
        assert.equal(row.status,'draft');assert.ok(row.scheduled_at.endsWith('Z'));
        await page.locator('#scheduled-posts-nav').click();
        await page.getByRole('heading',{name:'Scheduled Posts',exact:true}).waitFor();
        assert.equal(await page.locator('#posts-list .post-row').count(),1,'scheduled view excludes other posts');
        const item=page.locator('.post-row').filter({hasText:'Schedule regression article'});
        await item.getByRole('button',{name:'Edit',exact:true}).click();
        assert.equal(await page.locator('#post-scheduled-at').inputValue(),target,'UTC roundtrip preserves local minute');
        const later=await page.evaluate(()=>{const d=new Date(Date.now()+7200000);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16)});
        await page.locator('#post-scheduled-at').fill(later);
        await page.locator('#save-post').click();
        await page.waitForFunction(old=>window.__mockAdminRows[0].scheduled_at!==old,row.scheduled_at);
        await item.getByRole('button',{name:'Edit',exact:true}).click();
        await page.locator('#post-status').selectOption('draft');
        await page.locator('#save-post').click();
        await page.waitForFunction(()=>window.__mockAdminRows[0].scheduled_at===null);
        assert.equal(await page.evaluate(()=>window.__mockAdminRows[0].status),'draft');
        await page.getByText('No scheduled posts yet.',{exact:false}).waitFor();
        assert.equal(await page.locator('#posts-list .post-row').count(),0,'cancelled schedules leave the scheduled view');
        await page.locator('[data-post-filter="all"]').click();
        await page.getByRole('heading',{name:'Posts',exact:true}).waitFor();
        assert.equal(await page.locator('#posts-list .post-row').filter({hasText:'Schedule regression article'}).count(),1,'draft remains in all posts');
      }else{
        await page.locator('#save-post').click();
        await page.waitForFunction(()=>window.__mockAdminRows.length===1);
        assert.equal(await page.evaluate(()=>window.__mockAdminRows[0].status),'draft');
      }
      assert.deepEqual(errors,[]);
      await page.close();
    }
    console.log('Scheduling UI: inactive server, draft saves, past-time rejection, UTC roundtrip, reschedule and cancel passed.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

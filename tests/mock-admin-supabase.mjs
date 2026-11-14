// Test-only Supabase replacement. Never deployed or used by production admin.
const rows = [];
let counter = 0;
const defaults = {
 site_name:'CozyLoops',site_description:'Crochet tutorials',primary_color:'#4f694c',
 secondary_color:'#f4e4d8',background_color:'#fbf8f2',text_color:'#29342d',
 heading_font:'Georgia',body_font:'System',border_radius:17,
 logo_url:'',favicon_url:''
};
window.__mockAdminRows = rows;
class Query {
  constructor(table) { this.table=table; this.where=[]; this.operation='read'; this.payload=null; }
  select() { return this; }
  eq(key,val) { this.where.push(row=>row[key]===val); return this; }
  in(key,vals) { this.where.push(row=>vals.includes(row[key])); return this; }
  order() { return this; }
  maybeSingle() { return this.execute(true); }
  insert(payload) { this.operation='insert'; this.payload=payload; return this; }
  update(payload) { this.operation='update'; this.payload=payload; return this; }
  delete() { this.operation='delete'; return this; }
  async execute(single=false) {
    const source=this.table==='articles'?rows:this.table==='site_settings'?[{id:1,...defaults}]:[];
    const matching=source.filter(row=>this.where.every(fn=>fn(row)));
    if(this.operation==='insert'){
      const payloads=Array.isArray(this.payload)?this.payload:[this.payload];
      const created=payloads.map(payload=>({id:'test-id-'+(++counter),created_at:new Date().toISOString(),...payload}));
      if(this.table==='articles')rows.push(...created);
      return {data:created,error:null};
    }
    if(this.operation==='update'){
      for(const row of matching)Object.assign(row,this.payload);
      return {data:matching,error:null};
    }
    if(this.operation==='delete'){
      for(const row of matching){
        const index=source.indexOf(row);
        if(index!==-1)source.splice(index,1);
      }
      return {data:matching,error:null};
    }
    return {data:single?(matching[0]||null):matching,error:null};
  }
  then(resolve,reject){return this.execute().then(resolve,reject);}
}
export function createClient(){
  return {
    auth:{
      getUser:async()=>({data:{user:{id:'fake-owner',email:'owner@example.invalid'}},error:null}),
      signOut:async()=>({error:null}),
      signInWithPassword:async()=>({error:null})
    },
    rpc:async(name,args={})=>{
      if(name==='is_super_admin')return {data:true,error:null};
      if(name==='cozyloop_analytics_range'){
        const period=args.p_period||'30d',count=period==='1h'?12:period==='1d'?24:period==='7d'?7:period==='15d'?15:30;
        const step=period==='1h'?300000:period==='1d'?3600000:86400000;
        const end=Date.now();
        const series=Array.from({length:count},(_,i)=>({
          at:new Date(end-(count-1-i)*step).toISOString(),
          views:i===count-1?7:i===count-3?3:0
        }));
        return {data:{
          period,bucket_minutes:step/60000,total_page_views:10,home_views:4,
          article_views:6,previous_page_views:5,
          top_articles:[{slug:'crochet-patterns-for-beginners-guide',views:6}],
          series
        },error:null};
      }
      return {data:{total_page_views:0,home_views:0,article_views:0,today_page_views:0,top_articles:[]},error:null};
    },
    from:table=>new Query(table),
    storage:{from:()=>({upload:async()=>({error:null}),getPublicUrl:()=>({data:{publicUrl:'https://example.invalid/image.jpg'}})})}
  };
}

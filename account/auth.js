import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.119.0';

// Public publishable key only. Never use the admin service-role key in this page.
const supabase=createClient(
  'https://yqmrunstyhrhnvxoyrap.supabase.co',
  'sb_publishable_HqkcpvBz8P8KJTZFgefrWQ_rFxKPMNh',
  {auth:{detectSessionInUrl:true,persistSession:true,autoRefreshToken:true}}
);
const byId=id=>document.getElementById(id);
const views=[...document.querySelectorAll('[data-view]')];
const status=byId('auth-status');
let mode=new URLSearchParams(location.search).get('mode')==='update'?'update':'login';
let busy=false;
function message(text,type='info'){
  status.textContent=text;status.classList.toggle('error',type==='error');status.hidden=!text;
}
function show(view,clear=true){
  mode=view;
  views.forEach(el=>{el.hidden=el.dataset.view!==view});
  if(clear)message('');
  document.title=(view==='profile'?'My Account':view==='register'?'Register':view==='recover'?'Reset Password':view==='update'?'New Password':'Sign In')+' | CozyLoops';
}
function loading(isLoading){
  busy=isLoading;
  document.querySelectorAll('button').forEach(button=>{if(button.closest('[data-view]')&&!button.closest('[data-view]').hidden)button.disabled=isLoading});
}
async function run(action){
  if(busy)return;
  loading(true);message('');
  try{await action()}catch(e){message('Something went wrong. Please try again.','error');console.error('CozyLoops member auth request failed',e)}
  finally{loading(false)}
}
function feedback(error,success){message(error?error.message:success,error?'error':'info')}
document.querySelectorAll('[data-switch]').forEach(button=>button.addEventListener('click',()=>{
  show(button.dataset.switch);
  // Never keep OAuth callback code or recovery tokens in the address bar.
  history.replaceState(null,'',location.pathname);
}));
document.querySelectorAll('[data-google]').forEach(button=>button.addEventListener('click',()=>run(async()=>{
  const {error}=await supabase.auth.signInWithOAuth({provider:'google',options:{redirectTo:location.origin+'/account/'}});
  if(error)feedback(error);
})));
byId('login-form').addEventListener('submit',event=>{
  event.preventDefault();const email=byId('login-email').value.trim(),password=byId('login-password').value;
  run(async()=>{const {error}=await supabase.auth.signInWithPassword({email,password});if(error)feedback(error);else {show('profile');await showProfile()}});
});
byId('register-form').addEventListener('submit',event=>{
  event.preventDefault();
  const email=byId('register-email').value.trim(),password=byId('register-password').value;
  if(password!==byId('register-confirm').value){message('Passwords do not match.','error');return}
  run(async()=>{
    const {data,error}=await supabase.auth.signUp({email,password,options:{emailRedirectTo:location.origin+'/account/'}});
    feedback(error,data?.session?'Your account is ready. You are signed in.':'Check your inbox to confirm your email address before signing in.');
    if(!error&&data?.session){show('profile');await showProfile()}
  });
});
byId('recover-form').addEventListener('submit',event=>{
  event.preventDefault();const email=byId('recover-email').value.trim();
  run(async()=>{
    const {error}=await supabase.auth.resetPasswordForEmail(email,{redirectTo:location.origin+'/account/?mode=update'});
    // Avoid confirming whether a supplied email address belongs to a member.
    feedback(error,'If an account exists for this email, you will receive a password reset link. Check your inbox and spam folder.');
  });
});
byId('update-form').addEventListener('submit',event=>{
  event.preventDefault();
  const password=byId('update-password').value;
  if(password!==byId('update-confirm').value){message('Passwords do not match.','error');return}
  run(async()=>{
    const {error}=await supabase.auth.updateUser({password});
    if(error){feedback(error);return}
    await supabase.auth.signOut();
    show('login');history.replaceState(null,'',location.pathname);
    message('Password changed successfully. Sign in with your new password.');
  });
});
byId('logout').addEventListener('click',()=>run(async()=>{
  const {error}=await supabase.auth.signOut();if(error)feedback(error);else{show('login');history.replaceState(null,'',location.pathname)}
}));
async function showProfile(){
  const {data:{user}}=await supabase.auth.getUser();
  byId('profile-email').textContent=user?.email||'Signed in';
}
supabase.auth.onAuthStateChange((event)=>{
  if(event==='PASSWORD_RECOVERY'){show('update');}
  else if(event==='SIGNED_OUT'&&mode==='profile'){show('login')}
});
try{
  const {data:{session},error}=await supabase.auth.getSession();
  if(error)throw error;
  if(mode==='update'){show('update')}
  else if(session?.user){show('profile');await showProfile()}
  else show('login');
}catch(err){show(mode);message('Unable to connect to member accounts. Please try again later.','error')}

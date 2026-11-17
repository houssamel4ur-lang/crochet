/* This is a bridge to an existing publisher CMP, not a CMP implementation.
 * Never fabricate TCF/GPP strings, gate the original HB tags, or claim consent.
 */
(() => {
  'use strict';
  const button=document.getElementById('ad-consent-settings');
  const status=document.getElementById('ad-consent-status');
  if(!button||!status)return;
  button.addEventListener('click',()=>{
    const fc=window.googlefc;
    if(fc&&typeof fc.showRevocationMessage==='function'){
      try{
        // Official Google Privacy & messaging API; this only reopens an installed CMP.
        fc.showRevocationMessage();
        status.textContent='Requested the advertising privacy settings from the installed provider.';
      }catch{
        status.textContent='Advertising consent settings could not be opened. Please contact the site operator.';
      }
    }else{
      status.textContent='A supported advertising consent manager is not currently available here. This control cannot disable advertising cookies. You can adjust browser privacy settings or contact the operator.';
    }
  });
})();

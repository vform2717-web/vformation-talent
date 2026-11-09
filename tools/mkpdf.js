const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({viewport:{width:816,height:1056}});
  await p.emulateMedia({media:'print', colorScheme:'light'});
  await p.goto('file://' + process.argv[2]); await p.waitForTimeout(300);
  await p.addStyleTag({content:':root{--f-display:"Inter Display","Inter",sans-serif !important;--f-body:"Inter",sans-serif !important}'});
  await p.waitForTimeout(300);
  await p.pdf({path: process.argv[3], format:'Letter', printBackground:true, margin:{top:'0',bottom:'0',left:'0',right:'0'}});
  await b.close();
})();

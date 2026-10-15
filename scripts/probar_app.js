/*
 * Comprobaciones de la página (index.html).
 *
 * Carga Quórum en un DOM de mentira y lo maneja desde fuera, como probar_clm.js
 * con el CLM. Los datos no son de mentira del todo: los cifra el robot de
 * verdad (scripts/probar_robot.py --sitio), en dos grupos de acceso, así que
 * esto prueba también que lo que cifra Python lo abre WebCrypto.
 *
 * Uso (las dependencias no se guardan en el repositorio):
 *     npm install jsdom
 *     pip install openpyxl cryptography msoffcrypto-tool
 *     node scripts/probar_app.js
 *
 * El estado de la página se declara con `let` y no cuelga de window: se llega
 * con w.eval(). Sale con código 1 si algo falla.
 */
const fs=require('fs'), path=require('path'), os=require('os'), {execFileSync}=require('child_process');
let JSDOM;
try{ JSDOM=require('jsdom').JSDOM; }
catch(e){ console.error('Falta la dependencia de la prueba. Instálala con:\n    npm install jsdom\n'); process.exit(2); }

const RAIZ=path.dirname(__dirname);
const HTML=fs.readFileSync(path.join(RAIZ,'index.html'),'utf8');
const SITIO=fs.mkdtempSync(path.join(os.tmpdir(),'quorum-'));
const FRASES=JSON.parse(execFileSync('python3',[path.join(__dirname,'probar_robot.py'),'--sitio',path.join(SITIO,'datos')]).toString().trim().split('\n').pop());
fs.mkdirSync(path.join(SITIO,'demo'));
fs.copyFileSync(path.join(RAIZ,'demo','datos-demo.json'),path.join(SITIO,'demo','datos-demo.json'));

let fallos=0, pruebas=0;
function ok(cond,msg,extra){ pruebas++; if(cond){ console.log('  ✓ '+msg); } else { fallos++; console.log('  ✗ '+msg+(extra!==undefined?('  → '+JSON.stringify(extra)):'')); } }
function seccion(t){ console.log('\n'+t); }
const espera=ms=>new Promise(r=>setTimeout(r,ms));
async function hasta(fn,ms){ const t0=Date.now(); while(Date.now()-t0<(ms||20000)){ try{ if(fn())return true; }catch(e){} await espera(40); } return false; }

function nuevoDom(op){
  op=op||{};
  const dom=new JSDOM(HTML,{url:'http://localhost/quorum/index.html'+(op.hash||''),runScripts:'dangerously',pretendToBeVisual:true,
    beforeParse(w){
      Object.defineProperty(w,'crypto',{value:require('crypto').webcrypto});
      w.TextEncoder=TextEncoder; w.TextDecoder=TextDecoder;
      w.scrollTo=()=>{}; w.confirm=()=>true;
      if(op.ls)for(const [k,v] of Object.entries(op.ls))w.localStorage.setItem(k,v);
      w.fetch=async url=>{
        const rel=String(url).replace(/^.*\/quorum\//,'').replace(/^\.?\//,'');
        const f=path.join(SITIO,rel);
        if(op.sinRed||!fs.existsSync(f))return {ok:false,status:404,json:async()=>{throw new Error('404');}};
        const txt=fs.readFileSync(f,'utf8');
        return {ok:true,status:200,json:async()=>JSON.parse(txt)};
      };
    }});
  return dom.window;
}
async function cargado(w){ return hasta(()=>w.document.querySelector('#lf')||w.document.querySelector('#ldemo')); }
async function entrar(w,frase){
  const err=w.document.querySelector('#lerr');if(err)err.innerHTML='';
  w.document.querySelector('#lp').value=frase;
  w.document.querySelector('#lf').dispatchEvent(new w.Event('submit',{cancelable:true}));
  return hasta(()=>w.document.querySelector('.shell')||w.document.querySelector('#lerr .errbox'));
}
const ev=(w,s)=>w.eval(s);
const texto=w=>w.document.body.textContent;

(async()=>{
  seccion('1. La entrada: nada se descifra sin la frase');
  let w=nuevoDom();
  await cargado(w);
  ok(w.document.querySelector('#lp')&&w.document.querySelector('#lp').type==='password','pide la frase, en un campo de contraseña');
  ok(ev(w,'Object.keys(SOBRES).sort().join()')==='directorio,legal','bajó los dos sobres cifrados');
  ok(!/Manual|Reglamento|Junta Administrativa del FAP ·/.test(texto(w).replace(/la Junta Administrativa del FAP y/,'')),'y no muestra nada de lo que hay dentro');
  await entrar(w,'una-frase-que-no-es');
  ok(w.document.querySelector('#lerr .errbox')&&!w.document.querySelector('.shell'),'una frase equivocada no abre nada y lo dice');

  seccion('2. Cada frase abre su grupo, y solo el suyo');
  await entrar(w,FRASES.legal);
  ok(w.document.querySelector('.shell'),'la frase de legal entra');
  ok(ev(w,'ABIERTOS.join()')==='legal','abre solo legal');
  ok(ev(w,'ACTAS().every(a=>a.cuerpo!=="DIR-FIAS")'),'sin actas del Directorio del FIAS');
  ok(/1 grupo más, cerrado/.test(texto(w)),'y dice que hay otro grupo cerrado');
  const nLegal=ev(w,'RESOL().length');
  ok(await ev(w,`probarFrase(${JSON.stringify(FRASES.legal)})`).then(a=>a.length===0),'la misma frase otra vez no abre nada nuevo');
  const ab=await ev(w,`probarFrase(${JSON.stringify(FRASES.directorio)})`);
  ok(ab.join()==='directorio'&&ev(w,'RESOL().length')>nLegal,'con la segunda frase se suma el directorio',ab);
  ev(w,'render()');
  ok(ev(w,'NORMAS().length')===10&&ev(w,'RESOL().length')===59,'juntos, está todo: 10 normas y 59 resoluciones',[ev(w,'NORMAS().length'),ev(w,'RESOL().length')]);
  ok(ev(w,'CAMBIOS().length')===13,'un cambio que toca dos grupos no se duplica',ev(w,'CAMBIOS().length'));

  seccion('3. La vigencia se deduce de los cambios, a la fecha que se pregunte');
  const est=(id,f,t)=>ev(w,`estado${t||'Norma'}(DB.${t?'res':'normas'}[${JSON.stringify(id)}],${JSON.stringify(f)}).key`);
  ok(est('politica-de-inversiones-del-fias','2026-10-12')==='baja','derogada hoy');
  ok(est('politica-de-inversiones-del-fias','2020-01-01')==='vigente','pero vigente en 2020');
  ok(est('politica-de-inversiones-del-fias','2016-01-01')==='nada','y antes de aprobarse, no existía');
  ok(est('lineamientos-de-teletrabajo','2026-09-01')==='vigente','una derogación futura no se anuncia antes de la sesión que la decidió');
  ok(est('reglamento-de-adquisiciones-del-fias','2026-10-12')==='reformada','con reformas sigue vigente');
  ok(est('lineamientos-de-teletrabajo','2026-10-12')==='vence','derogación que aún no rige: vigente, y avisa la fecha');
  ok(est('lineamientos-de-teletrabajo','2027-01-01')==='baja','el día que rige, derogada');
  ok(est('ja-fap_2024-06-13_p4','2026-10-12','Res')==='baja'&&ev(w,'estadoRes(DB.res["ja-fap_2024-06-13_p4"],"2026-10-12").label')==='Sin efecto','resolución dejada sin efecto por otra acta');
  ok(est('dir-fias_2025-03-20_p3','2026-10-12','Res')==='reformada','resolución reformada');
  const ver=(id,f)=>ev(w,`versionA(DB.normas[${JSON.stringify(id)}],${JSON.stringify(f)}).ultima.tipo`);
  ok(ver('reglamento-de-adquisiciones-del-fias','2018-06-01')==='Texto original','2018: rige el texto original');
  ok(ver('reglamento-de-adquisiciones-del-fias','2020-06-01')==='Reforma parcial · arts. 12 y 15','2020: rige la reforma parcial');
  ok(ver('reglamento-de-adquisiciones-del-fias','2026-10-12')==='Codificación','hoy: la codificación');
  ok(ver('manual-de-operaciones-del-feig','2025-06-30')==='Texto original'&&ver('manual-de-operaciones-del-feig','2025-07-01').startsWith('Reforma parcial'),'una reforma con «Rige desde» cambia el texto ese día, no el de la sesión');
  ev(w,'ST.aFecha="2019-01-01"');
  ok(ev(w,'normasFiltradas().length')===5,'«Vigencia al» 1/1/2019: solo las normas que ya existían',ev(w,'normasFiltradas().map(x=>x.n.nombre)'));
  ev(w,'ST.aFecha=null');

  seccion('4. Pantallas y enlaces');
  ev(w,'go("norma","reglamento-de-adquisiciones-del-fias")');
  ok(w.location.hash==='#/norma/reglamento-de-adquisiciones-del-fias','el enlace lleva el id de la norma, no su posición');
  ok(/Vigente con reformas/.test(texto(w))&&/Codificación/.test(texto(w))&&w.document.querySelectorAll('.tl li').length===3,'la ficha trae estado, versiones y línea de tiempo');
  const qd=w.document.querySelector('#qd');qd.value='2020-06-01';w.document.querySelector('#qdb').click();
  ok(/Reforma parcial/.test(w.document.querySelector('#qdr').textContent),'«¿Qué regía en una fecha?» responde con la versión de ese día');
  ev(w,'go("acta","ja-fap_2026-08-08")');
  ok(w.document.querySelectorAll('.rowitem').length===3&&/Reforma: Manual Operativo/.test(texto(w)),'el acta muestra sus puntos y lo que cambió');
  ev(w,'go("resoluciones")');
  ok(/59 de 59 resoluciones/.test(texto(w)),'el listado de resoluciones');
  const q=w.document.querySelector('#rq');q.value='convocatoria donaciones';q.dispatchEvent(new w.Event('input'));
  ok(/4 de 59/.test(w.document.querySelector('#cnt').textContent),'busca cada palabra en cualquier parte',w.document.querySelector('#cnt').textContent);
  ev(w,'ST.rf.q=""');
  ok(ev(w,'buscarTodo("teletrabajo").some(h=>h.t==="norma")'),'el buscador de arriba encuentra normas');
  ok(ev(w,'buscarTodo("08/08/2026").some(h=>h.t==="acta"&&h.id==="ja-fap_2026-08-08")'),'y sesiones por la fecha como se escribe');
  ok(ev(w,'buscarTodo("junta agosto 2026").length>0')&&ev(w,'buscarTodo("codificacion").length>0'),'sin tildes y en cualquier orden');
  ev(w,'go("panel")');
  ok(w.document.querySelectorAll('.kpi').length===6&&/Próximo: derogación/.test(texto(w)),'el panel: indicadores y lo que viene');
  ev(w,'go("revision")');
  ok(/renglón 58/.test(texto(w)),'«Revisión de la matriz» trae el aviso del robot con su renglón');

  seccion('4b. Fondos: todo junto, o cada uno por separado');
  ev(w,'go("panel")');
  ok(w.document.querySelectorAll('#view .fondobar [data-fd]').length===5,'arriba, «Todos» y un botón por fondo (FIAS, FAP, FEIG y el programa)');
  ok(/Fondos, programas y proyectos/.test(texto(w))&&/Programa de Pequeñas Donaciones/.test(texto(w)),'y una tarjeta por fondo en el panel');
  w.document.querySelector('#view .fondobar [data-fd="FAP"]').click();
  ok(ev(w,'ST.fondo')==='FAP'&&/Áreas Protegidas/.test(w.document.querySelector('.fbname').textContent),'al elegir el FAP, el panel dice cuál es');
  ok(w.document.querySelector('.kpis .kpi:nth-child(4) .kpi-n').textContent==='8','y cuenta solo sus actas: las 8 de la Junta Administrativa');
  ev(w,'go("actas")');
  ok(/8 de 8 actas/.test(texto(w))&&ev(w,'actasFiltradas().every(x=>x.a.cuerpo==="JA-FAP")'),'el listado de actas se queda en el FAP',texto(w).match(/\d+ de \d+ actas?/));
  ok([...w.document.querySelectorAll('select[data-f=cuerpo] option')].map(o=>o.value).join()==='all,JA-FAP','y el filtro de cuerpo solo ofrece los suyos');
  ev(w,'go("resoluciones")');ok(/16 de 16 resoluciones/.test(texto(w)),'sus 16 resoluciones');
  ev(w,'go("normativa")');ok(/2 de 2 normas/.test(texto(w)),'y sus 2 normas');
  w.document.querySelector('#view .fondobar [data-fd="PPD"]').click();
  ok(/2 de 2 normas/.test(texto(w))===false&&ev(w,'normasFiltradas().length')===0,'un programa sin normas no muestra ninguna');
  ev(w,'go("actas")');ok(/2 de 2 actas/.test(texto(w)),'pero sí las actas de su comité');
  w.document.querySelector('#view .fondobar [data-fd="all"]').click();
  ok(/28 de 28 actas/.test(texto(w)),'«Todos» vuelve a juntarlo todo',texto(w).match(/\d+ de \d+ actas?/));
  ok(ev(w,'buscarTodo("pequenas donaciones comite").some(h=>h.t==="acta")'),'el buscador encuentra por el nombre del fondo');

  seccion('4c. El texto vigente, como en Lexis (cifrado aparte, se baja al abrirlo)');
  const MO='manual-operativo-del-ciclo-de-proyectos-del-fap';
  ok(typeof ev(w,`DB.normas["${MO}"].texto`)==='string'&&/^t-[0-9a-f]{24}\.json$/.test(ev(w,`DB.normas["${MO}"].texto`)),'la norma trae el nombre de su archivo de texto, que no dice cuál es');
  ok(ev(w,`DB.normas["${MO}"].textoInfo.articulos`)===6&&ev(w,'Object.keys(CLAVES_TEXTO).join()')==='legal','y la llave para abrirlo vino dentro del archivo del grupo');
  ev(w,`go("norma","${MO}")`);
  ok(w.document.querySelector('#a-leer')&&/6 artículos/.test(texto(w)),'la ficha ofrece «Leer el texto vigente», con cuántos artículos tiene');
  w.document.querySelector('#a-leer').click();
  ok(await hasta(()=>w.document.querySelectorAll('#ltx .lart').length===6),'se baja, se descifra y se muestra: 6 artículos');
  ok(w.document.querySelectorAll('#lidx .lix').length===9&&/CAPÍTULO II · DE LA OPERACIÓN/.test(w.document.querySelector('#lidx').textContent),'índice con capítulos y artículos');
  ok(/Art\. 5\.- COMBUSTIBLE\./.test(w.document.querySelector('#ltx').textContent),'cada artículo con su número y su rubro');
  const lq=w.document.querySelector('#lq');lq.value='combustible';lq.dispatchEvent(new w.Event('input'));
  ok(await hasta(()=>w.document.querySelectorAll('#ltx mark').length>=2)&&/1 coincidencia/.test(w.document.querySelector('#lcnt').textContent),'buscar en la norma resalta y deja en el índice solo lo que coincide');
  ok(ev(w,'buscarTodo("estaciones autorizadas").some(h=>h.t==="texto"&&h.art==="p0-a5")'),'el buscador de arriba encuentra dentro del texto, y lleva al artículo');
  ev(w,`go("texto","${MO}","p0-a4")`);
  ok(w.location.hash===`#/texto/${MO}~p0-a4`,'el enlace lleva la norma y el artículo');
  ev(w,'go("norma","reglamento-de-adquisiciones-del-fias")');
  ok(!w.document.querySelector('#a-leer'),'una norma sin texto no ofrece leerlo (sigue el PDF)');

  seccion('5. Un enlace a algo de otro grupo o que ya no está');
  let w2=nuevoDom({hash:'#/norma/reglamento-de-adquisiciones-del-fias'});
  await cargado(w2);await entrar(w2,FRASES.legal);
  ok(ev(w2,'ST.view')==='normativa'&&/otro grupo de acceso/.test(texto(w2)),'con la frase de legal, la norma del directorio no se abre: lleva al listado y lo dice');
  let w3=nuevoDom({hash:'#/acta/ja-fap_2026-08-08'});
  await cargado(w3);await entrar(w3,FRASES.legal);
  ok(ev(w3,'ST.view')==='acta'&&/8 de agosto de 2026/.test(texto(w3)),'un enlace que llega antes de la frase se abre al entrar');

  seccion('6. Notas: cifradas, y solo en este navegador');
  ev(w,'go("resolucion","ja-fap_2026-08-08_p3")');
  w.document.querySelector('#ntx').value='Nota confidencial de prueba';
  w.document.querySelector('#nok').click();
  ok(await hasta(()=>w.localStorage.getItem('quorum_notas_legal')),'la nota se guarda');
  const todo=JSON.stringify(Object.assign({},w.localStorage))+JSON.stringify(Object.assign({},w.sessionStorage));
  ok(!/confidencial/.test(todo),'cifrada: el texto no está en el almacenamiento');
  ok(!todo.includes(FRASES.legal)&&!todo.includes(FRASES.directorio),'y ninguna frase quedó guardada');
  ok(Object.keys(w.localStorage).every(k=>k.startsWith('quorum_notas_')),'lo único que se guarda son las notas',Object.keys(w.localStorage));
  const ls={};for(const k of Object.keys(w.localStorage))ls[k]=w.localStorage.getItem(k);
  let w4=nuevoDom({ls,hash:'#/resolucion/ja-fap_2026-08-08_p3'});
  await cargado(w4);await entrar(w4,FRASES.legal);
  ok(/Nota confidencial de prueba/.test(texto(w4)),'al volver a entrar con la frase, la nota está');

  seccion('7. Cerrar es olvidar');
  ev(w,'cerrarSesion("x")');
  ok(w.document.querySelector('#lf')&&ev(w,'ABIERTOS.length')===0&&ev(w,'RESOL().length')===0,'cerrar borra lo descifrado y vuelve a pedir la frase');
  ok(ev(w,'Object.keys(LLAVES).length')===0&&!w.location.hash,'también las llaves de las notas y el enlace de la barra');
  ok(ev(w,'Object.keys(TEXTOS).length+Object.keys(CLAVES_TEXTO).length')===0,'y los textos descifrados con su llave');
  await entrar(w,FRASES.legal);
  ev(w,'BLOQUEO_MIN=0.002;tocar()');
  ok(await hasta(()=>w.document.querySelector('#lf'),3000)&&/inactividad/.test(texto(w)),'se cierra sola sin uso');
  ev(w,'BLOQUEO_MIN=20');

  seccion('8. Lo que viene del Excel nunca se interpreta como código');
  ev(w,`DEMO=true;fusionar({grupo:"x",cuerpos:[{sigla:"JA-FAP",nombre:"Junta <b>x</b>"}],actas:[{id:"ja-fap_2030-01-01",cuerpo:"JA-FAP",fecha:"2030-01-01"}],
    resoluciones:[{id:"ja-fap_2030-01-01_p1",acta:"ja-fap_2030-01-01",cuerpo:"JA-FAP",fecha:"2030-01-01",punto:"1",texto:"<img src=x onerror=window.PWNED=1>",enlace:"javascript:window.PWNED=2"}],normas:[],cambios:[],avisos:[]});render();go("resolucion","ja-fap_2030-01-01_p1")`);
  ok(!w.document.querySelector('#view img')&&!w.PWNED,'el texto con etiquetas se muestra como texto');
  ok(![...w.document.querySelectorAll('a')].some(a=>/^javascript:/i.test(a.getAttribute('href')||'')),'y un «javascript:» no llega a un enlace');
  ev(w,'cerrarSesion()');

  seccion('9. La demostración');
  w.document.querySelector('#ldemo').click();
  ok(await hasta(()=>w.document.querySelector('.shell')),'entra sin frase');
  ok(ev(w,'DEMO')&&/datos ficticios/.test(w.document.querySelector('.srcpill').textContent),'y dice siempre que los datos son ficticios');
  ev(w,'go("texto","reglamento-de-adquisiciones-del-fias")');
  ok(await hasta(()=>w.document.querySelectorAll('#ltx .lart').length===13),'la demostración trae un texto de ejemplo para leer');
  ok(w.document.querySelectorAll('#ltx .lref').length===2&&/arts?\. ?12|Art\. 12/.test(w.document.querySelector('#a-p0-a12').textContent)&&w.document.querySelector('#a-p0-a12 .lref'),'los artículos 12 y 15, reformados en la hoja Cambios, lo dicen al pie');
  ok(w.document.querySelectorAll('#lidx .ref').length===2,'y el índice los marca');
  ev(w,'go("norma","codigo-de-etica-y-conducta-del-fias")');
  w.document.querySelector('#ntx').value='nota de demo';w.document.querySelector('#nok').click();await espera(50);
  ok(!w.localStorage.getItem('quorum_notas_demo'),'sus notas no se guardan');

  ev(w,'go("norma","reglamento-interno-de-talento-humano")');
  ok(w.document.querySelectorAll('[data-anx]').length===1&&/Anexos/.test(texto(w)),'una norma muestra sus anexos');
  w.document.querySelector('[data-anx]').click();
  ok(ev(w,'ST.id')==='lineamientos-de-teletrabajo'&&/Anexo de Reglamento Interno de Talento Humano/.test(texto(w)),'y el anexo dice de cuál es, con enlace');

  seccion('10. Sin red, o sin publicar todavía');
  let w5=nuevoDom({sinRed:true});
  await cargado(w5);
  ok(!w5.document.querySelector('#lf')&&/No se pudieron bajar/.test(texto(w5))&&w5.document.querySelector('#ldemo'),'lo dice, y ofrece la demostración');

  seccion('11. Las frases que genera');
  const n=ev(w,'LISTA_PALABRAS.length'),f=ev(w,'fraseNueva()').split('-');
  ok(n>=450,`${n} palabras: seis al azar son más de 52 bits`,n);
  ok(f.length===6&&f.every(p=>ev(w,`LISTA_PALABRAS.includes(${JSON.stringify(p)})`)),'seis palabras de la lista');
  ok(ev(w,'LISTA_PALABRAS.every(p=>/^[a-z]+$/.test(p))'),'sin tildes, eñes ni mayúsculas: se dictan sin dudas');
  ok(ev(w,'new Set(Array.from({length:50},()=>fraseNueva())).size')===50,'y no se repiten');

  console.log(`\n${pruebas-fallos} de ${pruebas} comprobaciones bien`+(fallos?` · ${fallos} FALLAN`:''));
  fs.rmSync(SITIO,{recursive:true,force:true});
  process.exit(fallos?1:0);
})().catch(e=>{console.error(e);process.exit(1);});

// 名片夾 CardVault 官網共用腳本：中英切換、選單、頁首陰影。
// 語言的初始判斷寫在每頁 <head> 的 inline script（避免英文訪客先閃一下中文），這裡負責切換。
var TITLE_ZH = document.title;

function setLang(l){
  var en = (l === 'en');
  document.documentElement.lang = en ? 'en' : 'zh-Hant';
  var t = document.documentElement.getAttribute('data-title-en');
  if (t) document.title = en ? t : TITLE_ZH;
  try { localStorage.setItem('cardvault_lang', en ? 'en' : 'zh'); } catch (e) {}
}
// 依 <head> 判斷好的語言，套用對應的分頁標題
if (document.documentElement.lang === 'en') {
  var t0 = document.documentElement.getAttribute('data-title-en');
  if (t0) document.title = t0;
}

(function(){
  var menuBtn = document.getElementById('menuBtn');
  var panel = document.getElementById('menuPanel');
  var scrim = document.getElementById('menuScrim');
  if (menuBtn && panel && scrim) {
    var openMenu = function(){ panel.classList.add('open'); scrim.classList.add('open'); menuBtn.setAttribute('aria-expanded','true'); };
    var closeMenu = function(){ panel.classList.remove('open'); scrim.classList.remove('open'); menuBtn.setAttribute('aria-expanded','false'); };
    menuBtn.addEventListener('click', function(){ panel.classList.contains('open') ? closeMenu() : openMenu(); });
    document.getElementById('menuClose').addEventListener('click', closeMenu);
    scrim.addEventListener('click', closeMenu);
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeMenu(); });
    Array.prototype.forEach.call(panel.querySelectorAll('nav a'), function(a){ a.addEventListener('click', closeMenu); });
  }

  var header = document.getElementById('siteHeader');
  if (header) {
    var onScroll = function(){ header.classList.toggle('scrolled', window.scrollY > 8); };
    onScroll(); window.addEventListener('scroll', onScroll, {passive:true});
  }
})();

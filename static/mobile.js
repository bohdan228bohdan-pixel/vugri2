// mobile.js — robust mobile nav toggle and safety helpers
(function(){
  function initMobileNav(){
    const toggle = document.getElementById('mobileNavToggle');
    const nav = document.getElementById('siteNav');
    if(!toggle || !nav){
      if (!window.__mobileNavRetries) window.__mobileNavRetries = 0;
      if (window.__mobileNavRetries < 10) {
        window.__mobileNavRetries++;
        setTimeout(initMobileNav, 200);
      }
      return;
    }

    // ensure button on top
    const header = document.querySelector('.site-header');
    if(header) header.style.zIndex = header.style.zIndex || 10000;
    toggle.style.zIndex = 10001;
    toggle.style.cursor = 'pointer';
    toggle.setAttribute('aria-expanded', toggle.getAttribute('aria-expanded') || 'false');

    function openNav(){
      nav.classList.add('open');
      toggle.setAttribute('aria-expanded', 'true');
      document.documentElement.style.overflow = 'hidden';
      document.body.style.overflow = 'hidden';
    }
    function closeNav(){
      nav.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      document.documentElement.style.overflow = '';
      document.body.style.overflow = '';
    }
    function toggleNav(e){
      if(e) e.preventDefault();
      if(nav.classList.contains('open')) closeNav(); else openNav();
    }

    toggle.addEventListener('click', toggleNav, {passive:false});
    toggle.addEventListener('touchstart', function(e){ e.preventDefault(); toggleNav(e); }, {passive:false});

    // close on outside click or Escape
    document.addEventListener('click', function(e){
      if(!nav.classList.contains('open')) return;
      if(!nav.contains(e.target) && !toggle.contains(e.target)) closeNav();
    }, {passive:true});
    document.addEventListener('keydown', function(e){
      if(e.key === 'Escape' && nav.classList.contains('open')) closeNav();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initMobileNav);
  else initMobileNav();
})();
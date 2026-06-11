// ==UserScript==
// @name         Amazon 价格走势查询
// @namespace    https://github.com/jikoryu/git
// @version      2.1
// @description  在 Amazon 商品页面提取真实价格，一键查看历史走势
// @author       jikoryu
// @match        https://www.amazon.com/*
// @match        https://www.amazon.co.jp/*
// @match        https://www.amazon.co.uk/*
// @match        https://www.amazon.de/*
// @match        https://www.amazon.fr/*
// @match        https://www.amazon.ca/*
// @match        https://www.amazon.it/*
// @match        https://www.amazon.es/*
// @match        https://www.amazon.com.au/*
// @match        https://www.amazon.in/*
// @match        https://www.amazon.com.br/*
// @match        https://www.amazon.com.mx/*
// @match        https://www.amazon.nl/*
// @match        https://www.amazon.se/*
// @match        https://www.amazon.sg/*
// @grant        GM_openInTab
// @grant        GM_getValue
// @grant        GM_setValue
// @run-at       document-end
// ==/UserScript==

(function() {
  'use strict';

  const TOOL_URL = 'http://localhost:8888';

  const PLATFORM = 'amazon';
  const COLOR = '#FF9900';

  // ═══════════════════════════════════════
  // 从页面 DOM 提取真实商品信息
  // ═══════════════════════════════════════
  function extractProductInfo() {
    const info = { title: '', price: '', image: '', shop: '', url: location.href.split('?')[0] };

    // ── Amazon DOM 提取 ──
      // 标题
      const titleEl =
        document.querySelector('#productTitle') ||
        document.querySelector('#title') ||
        document.querySelector('[data-automation-id="title"]');
      if (titleEl) info.title = titleEl.textContent.trim();

      // 价格 — 多个备选
      // Amazon 价格通常在 .a-price .a-offscreen 里，格式 "$1,299.99"
      const priceEl =
        document.querySelector('.a-price .a-offscreen') ||
        document.querySelector('.a-price[data-a-size="xl"] .a-offscreen') ||
        document.querySelector('#price_inside_buybox') ||
        document.querySelector('.a-price-whole');
      if (priceEl) {
        let raw = priceEl.textContent.trim();
        // 如果取到 .a-price-whole（只有整数部分），尝试找 fraction
        if (priceEl.classList.contains('a-price-whole')) {
          const fracEl = priceEl.parentElement?.querySelector('.a-price-fraction');
          if (fracEl) raw += '.' + fracEl.textContent.trim();
        }
        // 清理货币符号
        raw = raw.replace(/[^0-9.,]/g, '').replace(',', '');
        const m = raw.match(/(\d+\.?\d*)/);
        if (m) info.price = m[1];
      }

      // 如果没有 offscreen，试试 corePriceDisplay
      if (!info.price) {
        const corePrice = document.querySelector('#corePriceDisplay_desktop_feature_div .a-price-whole');
        if (corePrice) {
          let raw = corePrice.textContent.trim();
          const frac = document.querySelector('#corePriceDisplay_desktop_feature_div .a-price-fraction');
          if (frac) raw += '.' + frac.textContent.trim();
          raw = raw.replace(/[^0-9.]/g, '');
          const m = raw.match(/(\d+\.?\d*)/);
          if (m) info.price = m[1];
        }
      }

      // 图片
      const imgEl =
        document.querySelector('#landingImage') ||
        document.querySelector('#imgTagWrapper img') ||
        document.querySelector('.imgTagWrapper img') ||
        document.querySelector('#main-image') ||
        document.querySelector('[data-old-hires]');
      if (imgEl) {
        info.image = imgEl.src || imgEl.getAttribute('data-old-hires') || '';
      }

      // 店铺
      const shopEl =
        document.querySelector('#bylineInfo') ||
        document.querySelector('#brand') ||
        document.querySelector('[data-feature-name="bylineInfo"]');
      if (shopEl) {
        info.shop = shopEl.textContent.replace(/Visit the |Brand: |Store: /gi, '').trim();
      }

    }

    // 兜底：始终从 document.title 提取
    if (!info.title) {
      info.title = document.title.split(/[-–—:|]/)[0].trim() || document.title;
    }

    return info;
  }

  // ═══════════════════════════════════════
  // 注入浮动按钮
  // ═══════════════════════════════════════
  function injectButton() {
    if (document.getElementById('__pt_btn__')) return;

    const color = COLOR;
    const btn = document.createElement('div');
    btn.id = '__pt_btn__';
    btn.textContent = '📉 View Price History';
    btn.title = '从当前页面提取真实价格，查看历史走势';

    Object.assign(btn.style, {
      position:'fixed', bottom:'24px', right:'24px', zIndex:'9999999',
      padding:'14px 22px', background:`linear-gradient(135deg, ${color}, #6366f1)`,
      color:'#fff', fontSize:'15px', fontWeight:'700', borderRadius:'14px',
      cursor:'pointer', boxShadow:'0 4px 24px rgba(79,70,229,0.4)',
      transition:'all 0.2s ease', letterSpacing:'0.3px', userSelect:'none',
      fontFamily:'-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif',
    });

    btn.addEventListener('mouseenter', () => {
      btn.style.transform = 'translateY(-2px)';
      btn.style.boxShadow = '0 8px 32px rgba(79,70,229,0.5)';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'translateY(0)';
      btn.style.boxShadow = '0 4px 24px rgba(79,70,229,0.4)';
    });

    btn.addEventListener('click', (e) => {
      e.preventDefault(); e.stopPropagation();
      showLoading();
      const info = extractProductInfo();

      const params = new URLSearchParams();
      params.set('url', location.href);
      params.set('source', 'client');
      if (info.title) params.set('title', info.title);
      if (info.price) params.set('price', info.price);
      if (info.image) params.set('image', info.image);
      if (info.shop) params.set('shop', info.shop);
      params.set('platform', PLATFORM);

      const targetUrl = `${TOOL_URL}/?${params.toString()}`;

      if (typeof GM_openInTab === 'function') {
        GM_openInTab(targetUrl, { active: true });
      } else {
        window.open(targetUrl, '_blank');
      }
      hideLoading();

      const count = (parseInt(GM_getValue('usage_count', '0'), 10) || 0) + 1;
      GM_setValue('usage_count', String(count));
    });

    document.body.appendChild(btn);
  }

  // 提取时短暂显示进度
  function showLoading() {
    const btn = document.getElementById('__pt_btn__');
    if (btn) btn.textContent = '提取中...';
  }
  function hideLoading() {
    const btn = document.getElementById('__pt_btn__');
    if (btn) btn.textContent = '📉 View Price History';
  }

  // ═══════════════════════════════════════
  // 确保在商品详情页才注入
  // ═══════════════════════════════════════
  function isProductPage() {
    // Amazon 商品页特征: 有 #productTitle 且 URL 包含 /dp/ 或 /gp/product/
    return (!!document.querySelector('#productTitle') || !!document.querySelector('#title')) &&
           (/\/dp\//.test(location.href) || /\/gp\/product\//.test(location.href) || /\/product\//.test(location.href));
  }

  function tryInject() {
    if (!isProductPage()) return;
    if (document.body) { injectButton(); }
    else { setTimeout(tryInject, 500); }
  }

  tryInject();
  // Amazon 有时 SPA 切换，延迟重试
  setTimeout(tryInject, 2000);
  setTimeout(tryInject, 4000);

  // URL 变化监听
  let lastUrl = location.href;
  new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      const old = document.getElementById('__pt_btn__');
      if (old) old.remove();
      setTimeout(tryInject, 2000);
    }
  }).observe(document, { subtree: true, childList: true });

})();

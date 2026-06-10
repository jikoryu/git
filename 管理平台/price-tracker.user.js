// ==UserScript==
// @name         商品价格走势查询
// @namespace    https://github.com/jikoryu/git
// @version      1.0
// @description  在京东/淘宝/拼多多商品页面注入按钮，一键查看30天价格走势
// @author       jikoryu
// @match        https://item.jd.com/*
// @match        https://item.taobao.com/*
// @match        https://detail.tmall.com/*
// @match        https://mobile.yangkeduo.com/goods*.html*
// @match        https://www.pinduoduo.com/goods*.html*
// @grant        GM_openInTab
// @grant        GM_getValue
// @grant        GM_setValue
// @run-at       document-end
// ==/UserScript==

(function() {
  'use strict';

  // ═══════════════════════════════════════
  // 配置：价格走势工具地址
  // ═══════════════════════════════════════
  const TOOL_URL = 'http://localhost:8888';

  // ═══════════════════════════════════════
  // 检测是否为商品详情页
  // ═══════════════════════════════════════
  function isProductPage() {
    const url = location.href;
    // 京东商品页
    if (/item\.jd\.com\/\d+\.html/.test(url)) return true;
    // 淘宝商品页
    if (/item\.taobao\.com\/item\.htm/.test(url) && /[?&]id=\d+/.test(url)) return true;
    // 天猫商品页
    if (/detail\.tmall\.com\/item\.htm/.test(url)) return true;
    // 拼多多商品页
    if (/goods\.html/.test(url) && /goods_id=\d+/.test(url)) return true;
    return false;
  }

  // ═══════════════════════════════════════
  // 获取平台名称
  // ═══════════════════════════════════════
  function getPlatform() {
    const host = location.hostname;
    if (/jd\.com/.test(host)) return '京东';
    if (/taobao\.com/.test(host)) return '淘宝';
    if (/tmall\.com/.test(host)) return '天猫';
    if (/pinduoduo\.com|yangkeduo\.com/.test(host)) return '拼多多';
    return '电商';
  }

  // ═══════════════════════════════════════
  // 注入浮动按钮
  // ═══════════════════════════════════════
  function injectButton() {
    // 避免重复注入
    if (document.getElementById('__price_tracker_btn__')) return;

    const platform = getPlatform();
    const colors = { '京东':'#E2231A', '淘宝':'#FF5000', '天猫':'#FF5000', '拼多多':'#E02E24' };
    const color = colors[platform] || '#4f46e5';

    const btn = document.createElement('div');
    btn.id = '__price_tracker_btn__';
    btn.innerHTML = '📉 查看价格走势';
    btn.title = '点击查看该商品近30天价格走势';

    // 样式：右下角悬浮按钮
    Object.assign(btn.style, {
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: '999999',
      padding: '14px 22px',
      background: `linear-gradient(135deg, ${color}, #6366f1)`,
      color: '#fff',
      fontSize: '15px',
      fontWeight: '700',
      borderRadius: '14px',
      cursor: 'pointer',
      boxShadow: '0 4px 20px rgba(79,70,229,0.35)',
      transition: 'all 0.2s ease',
      letterSpacing: '0.5px',
      userSelect: 'none',
      fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif',
    });

    // Hover 效果
    btn.addEventListener('mouseenter', () => {
      btn.style.transform = 'translateY(-2px)';
      btn.style.boxShadow = '0 6px 28px rgba(79,70,229,0.45)';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'translateY(0)';
      btn.style.boxShadow = '0 4px 20px rgba(79,70,229,0.35)';
    });

    // 点击事件
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();

      const productUrl = location.href;
      const targetUrl = `${TOOL_URL}/?url=${encodeURIComponent(productUrl)}`;

      // 使用 GM_openInTab（Tampermonkey API）打开新标签页
      if (typeof GM_openInTab === 'function') {
        GM_openInTab(targetUrl, { active: true });
      } else {
        window.open(targetUrl, '_blank');
      }
    });

    document.body.appendChild(btn);

    // 记录使用次数
    const count = (parseInt(GM_getValue('usage_count', '0'), 10) || 0) + 1;
    GM_setValue('usage_count', String(count));
  }

  // ═══════════════════════════════════════
  // 主入口
  // ═══════════════════════════════════════
  if (isProductPage()) {
    // 等待页面加载完成后再注入（有些电商页面是 SPA）
    const tryInject = () => {
      if (document.body) {
        injectButton();
      } else {
        setTimeout(tryInject, 500);
      }
    };

    // 立即尝试 + 延迟重试（处理 SPA 路由切换）
    tryInject();
    setTimeout(tryInject, 2000);

    // 监听 URL 变化（SPA 切换商品时重新注入）
    let lastUrl = location.href;
    new MutationObserver(() => {
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        const old = document.getElementById('__price_tracker_btn__');
        if (old) old.remove();
        setTimeout(tryInject, 1500);
      }
    }).observe(document, { subtree: true, childList: true });
  }

})();

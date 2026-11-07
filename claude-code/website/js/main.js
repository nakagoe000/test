'use strict';

document.documentElement.classList.add('js');

document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initMobileNav();
  initReveal();
  initFaq();
  initPlanLinks();
  initContactForm();
  document.getElementById('year').textContent = new Date().getFullYear();
});

/* ヘッダーの影 & トップへ戻るボタン */
function initHeader() {
  const header = document.getElementById('header');
  const toTop = document.getElementById('toTop');

  const onScroll = () => {
    const y = window.scrollY;
    header.classList.toggle('is-scrolled', y > 10);
    toTop.classList.toggle('is-visible', y > 600);
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

/* スマホ用ハンバーガーメニュー */
function initMobileNav() {
  const button = document.getElementById('hamburger');
  const nav = document.getElementById('nav');

  const setOpen = (open) => {
    button.classList.toggle('is-open', open);
    nav.classList.toggle('is-open', open);
    button.setAttribute('aria-expanded', String(open));
    button.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
  };

  button.addEventListener('click', () => {
    setOpen(!nav.classList.contains('is-open'));
  });

  // リンクをタップしたら閉じる
  nav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setOpen(false));
  });

  // Escキーで閉じる
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') setOpen(false);
  });
}

/* スクロールで要素をふわっと表示 */
function initReveal() {
  const targets = document.querySelectorAll('.reveal');

  if (!('IntersectionObserver' in window)) {
    targets.forEach((el) => el.classList.add('is-visible'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
  );

  targets.forEach((el) => {
    // 同じグループ内の要素が、順番に少しずつ遅れて表示されるように
    const group = Array.from(el.parentElement.children).filter((c) => c.classList.contains('reveal'));
    const delay = el.dataset.delay ?? group.indexOf(el) * 0.12;
    el.style.transitionDelay = `${delay}s`;

    // 表示が終わったら遅延を解除（ほかの動きに影響しないように）
    el.addEventListener('transitionend', () => {
      el.style.transitionDelay = '';
    }, { once: true });

    observer.observe(el);
  });
}

/* FAQアコーディオン */
function initFaq() {
  document.querySelectorAll('.faq__q').forEach((button) => {
    button.addEventListener('click', () => {
      const item = button.closest('.faq__item');
      const open = !item.classList.contains('is-open');
      item.classList.toggle('is-open', open);
      button.setAttribute('aria-expanded', String(open));
    });
  });
}

/* 料金プランのボタン → フォームのプランを自動選択 */
function initPlanLinks() {
  const select = document.getElementById('plan');
  document.querySelectorAll('[data-plan]').forEach((link) => {
    link.addEventListener('click', () => {
      select.value = link.dataset.plan;
    });
  });
}

/* お問い合わせフォームの入力チェック */
function initContactForm() {
  const form = document.getElementById('contactForm');
  const success = document.getElementById('formSuccess');

  const rules = {
    name: (v) => (v.trim() ? '' : 'お名前を入力してください。'),
    email: (v) => {
      if (!v.trim()) return 'メールアドレスを入力してください。';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'メールアドレスの形式が正しくありません。';
      return '';
    },
    message: (v) => (v.trim() ? '' : 'ご相談内容を入力してください。'),
  };

  const validateField = (field) => {
    const rule = rules[field.name];
    if (!rule) return true;
    const message = rule(field.value);
    const error = field.parentElement.querySelector('.form__error');
    error.textContent = message;
    field.classList.toggle('is-invalid', Boolean(message));
    field.setAttribute('aria-invalid', String(Boolean(message)));
    return !message;
  };

  // 一度触った項目は入力中にチェック
  Object.keys(rules).forEach((name) => {
    const field = form.elements[name];
    field.addEventListener('blur', () => validateField(field));
    field.addEventListener('input', () => {
      if (field.classList.contains('is-invalid')) validateField(field);
    });
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    success.hidden = true;

    const fields = Object.keys(rules).map((name) => form.elements[name]);
    const results = fields.map(validateField);
    const firstInvalid = fields[results.indexOf(false)];

    if (firstInvalid) {
      firstInvalid.focus();
      return;
    }

    // TODO: 本番では Formspree などの送信サービスやサーバーに送る
    form.reset();
    success.hidden = false;
  });
}

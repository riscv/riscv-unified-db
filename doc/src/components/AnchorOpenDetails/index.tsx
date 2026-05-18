// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

import { useEffect } from 'react';
import BrowserOnly from '@docusaurus/BrowserOnly';

function getNavbarHeight(): number {
  // --ifm-navbar-height is in rem (e.g. "3.75rem") — convert to px
  const cssVar = getComputedStyle(document.documentElement)
    .getPropertyValue('--ifm-navbar-height').trim();
  if (cssVar.endsWith('rem')) {
    const rem = parseFloat(cssVar);
    const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
    return rem * rootFontSize;
  }
  if (cssVar.endsWith('px')) return parseFloat(cssVar);
  // Fallback: measure the navbar element directly
  const navbar = document.querySelector('.navbar--fixed-top') as HTMLElement | null;
  return navbar ? navbar.offsetHeight : 0;
}

function openDetailsForId(id: string): void {
  const target = document.getElementById(id);
  if (!target) return;

  // Walk up the DOM looking for Docusaurus's <Details> component wrapper
  // or native HTML <details> elements.
  // Docusaurus renders <details> as a div with data-collapsed="true" when closed.
  let el: HTMLElement | null = target.parentElement;
  while (el) {
    if (el.dataset.collapsed === 'true') {
      const summary = el.querySelector(':scope > summary') as HTMLElement | null;
      if (summary) summary.click();
    }
    // Also handle native HTML <details> elements
    if (el instanceof HTMLDetailsElement && !el.open) {
      el.open = true;
    }
    el = el.parentElement;
  }

  // Scroll after the Docusaurus expand animation completes.
  // --ifm-transition-fast is 200ms; wait a little longer to be safe.
  setTimeout(() => {
    const navbarHeight = getNavbarHeight();
    const top = target.getBoundingClientRect().top + window.scrollY - navbarHeight - 8;
    window.scrollTo({ top, behavior: 'smooth' });
  }, 250);
}

function AnchorOpenDetailsInner(): null {
  useEffect(() => {
    // Handle hash present on initial page load
    if (window.location.hash) {
      openDetailsForId(window.location.hash.slice(1));
    }

    // Intercept anchor clicks directly — Docusaurus's router may not fire hashchange
    // for same-page anchor navigation. preventDefault stops the browser's own
    // instant scroll so our post-animation scroll takes over.
    function onClick(e: MouseEvent): void {
      const anchor = (e.target as HTMLElement).closest('a');
      if (!anchor) return;
      const href = anchor.getAttribute('href');
      if (!href?.startsWith('#')) return;
      e.preventDefault();
      openDetailsForId(href.slice(1));
      history.pushState(null, '', href);
    }

    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  }, []);

  return null;
}

export default function AnchorOpenDetails(): JSX.Element {
  return <BrowserOnly>{() => <AnchorOpenDetailsInner />}</BrowserOnly>;
}

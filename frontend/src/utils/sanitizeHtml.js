const ALLOWED_TAGS = new Set([
  'a',
  'p',
  'br',
  'strong',
  'em',
  'ul',
  'ol',
  'li',
  'code',
  'pre',
  'blockquote',
  'table',
  'thead',
  'tbody',
  'tr',
  'th',
  'td',
  'hr',
  'span',
  'div',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
]);

const ALLOWED_ATTRS = {
  a: new Set(['href', 'title', 'target', 'rel']),
};

const ALLOWED_GLOBAL_ATTRS = new Set([]);

const ALLOWED_PROTOCOLS = new Set(['http:', 'https:', 'mailto:']);

function isRelativeUrl(url) {
  return url.startsWith('/') || url.startsWith('./') || url.startsWith('../') || url.startsWith('#');
}

function isAllowedUrl(url, anchor) {
  if (!url) return false;
  const trimmed = url.trim();
  if (!trimmed) return false;
  if (isRelativeUrl(trimmed)) return true;
  try {
    const parsed = anchor || document.createElement('a');
    parsed.href = trimmed;
    return ALLOWED_PROTOCOLS.has(parsed.protocol);
  } catch (error) {
    return false;
  }
}

function sanitizeNode(node, anchor) {
  if (node.nodeType === Node.ELEMENT_NODE) {
    const tagName = node.tagName.toLowerCase();

    if (!ALLOWED_TAGS.has(tagName)) {
      const parent = node.parentNode;
      if (parent) {
        while (node.firstChild) {
          parent.insertBefore(node.firstChild, node);
        }
        parent.removeChild(node);
      }
      return;
    }

    const allowedAttrs = new Set([...(ALLOWED_ATTRS[tagName] || []), ...ALLOWED_GLOBAL_ATTRS]);

    Array.from(node.attributes).forEach((attr) => {
      const attrName = attr.name.toLowerCase();
      if (attrName.startsWith('on')) {
        node.removeAttribute(attr.name);
        return;
      }
      if (!allowedAttrs.has(attrName)) {
        node.removeAttribute(attr.name);
        return;
      }
      if (attrName === 'href') {
        if (!isAllowedUrl(attr.value, anchor)) {
          node.removeAttribute(attr.name);
          node.removeAttribute('target');
          node.removeAttribute('rel');
        } else {
          node.setAttribute('target', '_blank');
          node.setAttribute('rel', 'noopener noreferrer nofollow');
        }
      }
    });
  }

  Array.from(node.childNodes).forEach((child) => sanitizeNode(child, anchor));
}

export function sanitizeHtml(html) {
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') {
    return '';
  }

  if (!html) {
    return '';
  }

  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  const anchor = document.createElement('a');
  Array.from(doc.body.childNodes).forEach((child) => sanitizeNode(child, anchor));
  return doc.body.innerHTML;
}


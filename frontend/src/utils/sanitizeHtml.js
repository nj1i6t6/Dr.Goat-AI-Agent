import DOMPurify from 'dompurify';

const ALLOWED_TAGS = [
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
];

const ALLOWED_ATTR = ['href', 'title', 'rel', 'target'];
const LINK_REL = 'noopener noreferrer nofollow';

function applySafeLinkAttributes(root) {
  root.querySelectorAll('a[href]').forEach((anchor) => {
    anchor.setAttribute('target', '_blank');
    anchor.setAttribute('rel', LINK_REL);
  });
}

export function sanitizeHtml(html) {
  if (!html || typeof window === 'undefined' || typeof document === 'undefined') {
    return '';
  }

  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    RETURN_TRUSTED_TYPE: false,
  });

  const template = document.createElement('template');
  template.innerHTML = clean;
  applySafeLinkAttributes(template.content);
  return template.innerHTML;
}

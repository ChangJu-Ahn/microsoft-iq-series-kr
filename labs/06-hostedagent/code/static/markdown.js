import MarkdownIt from "./markdown-it.js";

const parser = new MarkdownIt({html: false, linkify: false, typographer: false});
parser.disable("image");
parser.core.ruler.after("inline", "evidence_references", state => {
  for (const block of state.tokens) {
    if (block.type !== "inline" || !block.children) continue;
    const children = [];
    let linkDepth = 0;
    for (const token of block.children) {
      if (token.type === "link_open") linkDepth++;
      if (token.type === "link_close") linkDepth--;
      if (token.type !== "text" || linkDepth > 0) {
        children.push(token);
        continue;
      }
      let start = 0;
      for (const match of token.content.matchAll(/\[ref_id:([^\]\n]+)\]/g)) {
        if (match.index > start) {
          const text = new state.Token("text", "", 0);
          text.content = token.content.slice(start, match.index);
          children.push(text);
        }
        const citation = new state.Token("evidence_reference", "", 0);
        citation.meta = {id: match[1]};
        children.push(citation);
        start = match.index + match[0].length;
      }
      if (start < token.content.length) {
        const text = new state.Token("text", "", 0);
        text.content = token.content.slice(start);
        children.push(text);
      }
    }
    block.children = children;
  }
});
parser.renderer.rules.evidence_reference = (tokens, index, options, env) => {
  const id = tokens[index].meta.id;
  const escape = parser.utils.escapeHtml;
  const reference = env.references.get(id);
  if (!reference) {
    return `<span class="citation citation-missing" data-ref-id="${escape(id)}" title="${escape(`[ref_id:${id}] · 반환 근거와 연결되지 않음`)}">근거 미확인 · ${escape(id)}</span>`;
  }
  const label = `${reference.label} · ${id}`;
  return `<a class="citation source-${reference.kind}" data-ref-id="${escape(id)}" href="#${reference.anchor}" title="${escape(reference.title || label)}" aria-label="${escape(`${label} 근거 보기`)}">${escape(label)}</a>`;
};
const validateLink = parser.validateLink.bind(parser);
parser.validateLink = url => /^https?:\/\//i.test(url) && validateLink(url);
parser.renderer.rules.link_open = (tokens, index, options, env, renderer) => {
  tokens[index].attrSet("target", "_blank");
  tokens[index].attrSet("rel", "noopener noreferrer");
  return renderer.renderToken(tokens, index, options);
};
for (const type of ["th_open", "td_open"]) {
  parser.renderer.rules[type] = (tokens, index, options, env, renderer) => {
    const token = tokens[index];
    const alignment = token.attrGet("style")?.match(/^text-align:(left|center|right)$/)?.[1];
    if (token.attrs) token.attrs = token.attrs.filter(([name]) => name !== "style");
    if (alignment) token.attrSet("class", `align-${alignment}`);
    return renderer.renderToken(tokens, index, options);
  };
}

export function renderMarkdown(text, references = new Map()) {
  return parser.render(text, {references});
}

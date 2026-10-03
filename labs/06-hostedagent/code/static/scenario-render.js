import MarkdownIt from "./markdown-it.js";

const repository = "https://github.com/ChangJu-Ahn/microsoft-iq-series-kr/blob/main/";
const sourceDirectory = repository + "labs/00-getting-started/";
const diagrams = new Set(["assets/customer-problem.svg", "assets/problem-solving-workshop.svg"]);
const parser = new MarkdownIt({html: false, linkify: false, typographer: false});

export function scenarioLink(value) {
  if (typeof value !== "string" || !value || value.startsWith("//")) return null;
  if (value.startsWith("#")) return value;
  try {
    const url = new URL(value, sourceDirectory);
    if (!["https:", "http:"].includes(url.protocol) || url.username || url.password) return null;
    if (!/^https?:\/\//i.test(value) && !url.href.startsWith(repository)) return null;
    return url.href;
  } catch {
    return null;
  }
}

const validateLink = parser.validateLink.bind(parser);
parser.validateLink = value => validateLink(value) && scenarioLink(value) !== null;
parser.renderer.rules.link_open = (tokens, index, options, env, renderer) => {
  const token = tokens[index];
  const href = scenarioLink(token.attrGet("href"));
  if (href) {
    token.attrSet("href", href);
    if (!href.startsWith("#")) {
      token.attrSet("target", "_blank");
      token.attrSet("rel", "noopener noreferrer");
    }
  }
  return renderer.renderToken(tokens, index, options);
};
const renderImage = parser.renderer.rules.image;
parser.renderer.rules.image = (tokens, index, options, env, renderer) => {
  const token = tokens[index];
  const src = token.attrGet("src");
  if (!diagrams.has(src)) {
    return `<span class="scenario-image-unavailable">지원하지 않는 이미지: ${parser.utils.escapeHtml(token.content)}</span>`;
  }
  const local = "/scenario/" + src;
  token.attrSet("src", local);
  token.attrSet("loading", "lazy");
  token.attrSet("decoding", "async");
  return `<a class="scenario-image-link" href="${local}" target="_blank" rel="noopener noreferrer">${renderImage(tokens, index, options, env, renderer)}</a>`;
};
parser.renderer.rules.table_open = () => '<div class="table-scroll scenario-table"><table>\n';
parser.renderer.rules.table_close = () => "</table></div>\n";
for (const type of ["th_open", "td_open"]) {
  parser.renderer.rules[type] = (tokens, index, options, env, renderer) => {
    const token = tokens[index];
    const alignment = token.attrGet("style")?.match(/^text-align:(left|center|right)$/)?.[1];
    if (token.attrs) token.attrs = token.attrs.filter(([name]) => name !== "style");
    if (alignment) token.attrSet("class", `align-${alignment}`);
    return renderer.renderToken(tokens, index, options);
  };
}

export function renderScenario(markdown) {
  const tokens = parser.parse(markdown, {});
  const sections = [];
  for (const [index, token] of tokens.entries()) {
    if (token.type === "heading_open" && token.tag === "h2") {
      const id = `scenario-section-${sections.length + 1}`;
      token.attrSet("id", id);
      sections.push({id, title: tokens[index + 1].content});
    }
    if (["heading_open", "heading_close"].includes(token.type) && token.tag === "h1") {
      token.tag = "h2";
      if (token.type === "heading_open") token.attrSet("class", "scenario-document-title");
    }
  }
  return {html: parser.renderer.render(tokens, parser.options, {}), sections};
}

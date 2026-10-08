import {node} from "./dom.js";

const $ = id => document.getElementById(id);
let messages = [];
let selected = "";

function showMessage(id, focus = false) {
  const mail = messages.find(item => item.id === id);
  if (!mail) {
    $("mail-error").textContent = "선택한 메일의 기록을 찾을 수 없습니다. 목록에서 다시 선택하세요.";
    $("mail-content").hidden = true;
    $("mail-subject").textContent = "메일을 찾을 수 없습니다";
    return;
  }
  selected = id;
  $("mail-error").textContent = "";
  $("mail-subject").textContent = mail.subject;
  $("mail-sender").textContent = mail.sender;
  $("mail-recipient").textContent = mail.recipient;
  $("mail-date").textContent = mail.date;
  $("mail-body").textContent = mail.body;
  $("mail-content").hidden = false;
  for (const button of $("mail-list").querySelectorAll("button")) {
    button.setAttribute("aria-pressed", String(button.dataset.mailId === id));
  }
  history.replaceState(null, "", `#${id}`);
  if (focus) $("mail-subject").focus();
}

function renderList() {
  const query = $("mail-search").value.trim().toLocaleLowerCase();
  const visible = messages.filter(mail => `${mail.subject}\n${mail.body}`.toLocaleLowerCase().includes(query));
  $("mail-list").replaceChildren();
  $("mail-count").textContent = `${visible.length}개 메일 · 2026년 9월`;
  for (const mail of visible) {
    const item = node("li");
    const button = node("button", undefined, "mail-item");
    button.type = "button";
    button.dataset.mailId = mail.id;
    button.setAttribute("aria-pressed", String(mail.id === selected));
    button.setAttribute("aria-label", `${mail.subject} 본문 보기`);
    const top = node("span", undefined, "mail-item-top");
    top.append(node("strong", mail.sender), node("span", "9/22"));
    button.append(top, node("span", mail.subject, "mail-item-subject"),
      node("span", mail.body.split("\n")[0], "mail-item-preview"));
    button.onclick = () => showMessage(mail.id, true);
    item.append(button);
    $("mail-list").append(item);
  }
  if (!visible.length) $("mail-list").append(node("li", "일치하는 메일이 없습니다.", "mail-empty"));
}

$("mail-search").oninput = renderList;
window.addEventListener("hashchange", () => showMessage(location.hash.slice(1)));

try {
  const response = await fetch("/static/demo/mail.json");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data.messages) || data.messages.length !== 10 ||
      new Set(data.messages.map(mail => mail.id)).size !== data.messages.length ||
      data.messages.some(mail => !/^mail-\d+$/.test(mail.id) ||
        ["subject", "sender", "recipient", "date", "body"].some(key => typeof mail[key] !== "string" || !mail[key].trim()))) {
    throw new Error("메일 목록 또는 본문 기록이 올바르지 않습니다.");
  }
  messages = data.messages;
  $("mail-total").textContent = messages.length;
  $("mail-search").disabled = false;
  renderList();
  showMessage(location.hash.slice(1) || messages[0].id);
} catch (error) {
  $("mail-error").textContent = `메일 기록을 불러오지 못했습니다: ${error.message}`;
  $("mail-count").textContent = "메일 기록 조회 실패";
}

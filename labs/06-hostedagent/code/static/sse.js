export async function* readEvents(body) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;
  try {
    while (true) {
      const {value, done} = await reader.read();
      buffer += decoder.decode(value, {stream: !done}).replace(/\r\n/g, "\n");
      let boundary;
      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const lines = frame.split("\n");
        const name = lines.find(line => line.startsWith("event:"))?.slice(6).trim();
        const data = lines.filter(line => line.startsWith("data:")).map(line => line.slice(5).trimStart()).join("\n");
        if (name && data) yield {name, data: JSON.parse(data)};
      }
      if (done) {
        completed = true;
        break;
      }
    }
    if (buffer.trim()) throw new Error("스트림이 이벤트 도중 종료됐습니다.");
  } finally {
    if (!completed) await reader.cancel();
    reader.releaseLock();
  }
}

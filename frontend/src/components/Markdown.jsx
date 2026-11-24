function renderInline(text) {
  return String(text)
    .split(/(\*\*[^*]+\*\*)/g)
    .filter(Boolean)
    .map((part, index) =>
      part.startsWith("**") && part.endsWith("**") ? (
        <strong key={index}>{part.slice(2, -2)}</strong>
      ) : (
        <span key={index}>{part}</span>
      ),
    );
}

export default function Markdown({ text }) {
  const lines = String(text || "").split(/\r?\n/);
  const blocks = [];
  let list = [];
  let ordered = false;

  const flush = () => {
    if (!list.length) return;
    const ListTag = ordered ? "ol" : "ul";
    blocks.push(
      <ListTag key={`list-${blocks.length}`}>
        {list.map((item, index) => (
          <li key={index}>{renderInline(item)}</li>
        ))}
      </ListTag>,
    );
    list = [];
  };

  lines.forEach((line, index) => {
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+\.\s+(.*)$/);

    if (bullet || numbered) {
      const isOrdered = Boolean(numbered);
      if (list.length && isOrdered !== ordered) flush();
      ordered = isOrdered;
      list.push((bullet || numbered)[1]);
      return;
    }

    flush();
    if (/^###\s+/.test(line)) {
      blocks.push(<h4 key={index}>{renderInline(line.replace(/^###\s+/, ""))}</h4>);
    } else if (/^##\s+/.test(line)) {
      blocks.push(<h3 key={index}>{renderInline(line.replace(/^##\s+/, ""))}</h3>);
    } else if (/^#\s+/.test(line)) {
      blocks.push(<h2 key={index}>{renderInline(line.replace(/^#\s+/, ""))}</h2>);
    } else if (line.trim()) {
      blocks.push(<p key={index}>{renderInline(line)}</p>);
    }
  });
  flush();

  return <div className="markdown">{blocks.length ? blocks : <p>No report yet.</p>}</div>;
}

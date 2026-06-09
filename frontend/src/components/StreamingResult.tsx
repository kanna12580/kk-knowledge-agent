interface StreamingResultProps {
  lines: string[];
}

export function StreamingResult({ lines }: StreamingResultProps) {
  return (
    <div className="stream-box" aria-label="流式结果">
      {lines.length === 0 ? (
        <span className="stream-placeholder">等待流式结果</span>
      ) : (
        lines.map((line, index) => <p key={`${index}-${line}`}>{line}</p>)
      )}
    </div>
  );
}


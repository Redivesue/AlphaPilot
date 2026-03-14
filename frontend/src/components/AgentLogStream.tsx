import { useEffect, useRef, useState } from "react";
import { Card } from "antd";

interface LogEntry {
  timestamp: string;
  agent: string;
  action: string;
  result: unknown;
}

interface AgentLogStreamProps {
  wsUrl: string;
  connected: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export default function AgentLogStream({ wsUrl, connected, onConnect, onDisconnect }: AgentLogStreamProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!connected) return;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => onConnect?.();
    ws.onclose = () => onDisconnect?.();
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setLogs((prev) => [...prev, data]);
      } catch {}
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [wsUrl, connected]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <Card title="Agent Logs" size="small">
      <div
        ref={containerRef}
        style={{
          height: 320,
          overflow: "auto",
          background: "#1e1e1e",
          color: "#d4d4d4",
          fontFamily: "monospace",
          fontSize: 12,
          padding: 12,
          borderRadius: 4,
        }}
      >
        {logs.length === 0 && !connected && <div style={{ color: "#888" }}>Connect and run agent to see logs...</div>}
        {logs.length === 0 && connected && <div style={{ color: "#888" }}>Waiting for logs...</div>}
        {logs.map((l, i) => (
          <div key={i} style={{ marginBottom: 4 }}>
            <span style={{ color: "#6a9955" }}>[{l.timestamp}]</span>{" "}
            <span style={{ color: "#569cd6" }}>{l.agent}</span> → {l.action}:{" "}
            <span style={{ color: "#ce9178" }}>{String(l.result)}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

import { useEffect, useState } from "react";
import { Card } from "antd";
import { logsApi } from "../api/client";

interface LogEntry {
  timestamp: string;
  agent?: string;
  action: string;
  result?: unknown;
}

export default function SystemLogs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const load = () => {
    logsApi
      .getLogs(200)
      .then((res) => setLogs(res.data))
      .catch(() => {});
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div>
      <h2>System Logs</h2>
      <Card>
        <div
          style={{
            maxHeight: 500,
            overflow: "auto",
            fontFamily: "monospace",
            fontSize: 12,
          }}
        >
          {logs.length === 0 && <div style={{ color: "#888" }}>No logs yet.</div>}
          {logs.map((l, i) => (
            <div key={i} style={{ marginBottom: 4 }}>
              <span style={{ color: "#666" }}>[{l.timestamp}]</span>{" "}
              {l.agent && <span style={{ color: "#1890ff" }}>{l.agent}</span>}{" "}
              {l.action}: {String(l.result ?? "")}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button, Card } from "antd";
import ReactMarkdown from "react-markdown";
import { reportsApi } from "../api/client";

export default function ReportDetail() {
  const { filename } = useParams<{ filename: string }>();
  const navigate = useNavigate();
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!filename) return;
    reportsApi
      .getContent(filename)
      .then((res) => setContent(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filename]);

  const downloadUrl = filename ? reportsApi.downloadUrl(filename) : "";

  return (
    <div>
      <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
        <Button onClick={() => navigate("/reports")}>Back to Reports</Button>
        <a href={downloadUrl} download>
          <Button type="primary">Download Markdown</Button>
        </a>
      </div>
      <h2>{filename}</h2>
      <Card loading={loading}>
        <div style={{ padding: 16 }} className="markdown-body">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </Card>
    </div>
  );
}

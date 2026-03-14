import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Button, Spin, message } from "antd";
import Plot from "react-plotly.js";
import { factorsApi } from "../api/client";

export default function FactorDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<{
    id: string;
    expression: string;
    mean_ic: number | null;
    icir: number | null;
    sharpe: number | null;
    max_drawdown: number | null;
    is_active?: boolean;
    ic_decay: Record<number, number> | null;
    similar_factors: { expression: string; mean_ic: number; sharpe: number }[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    factorsApi
      .getDetail(id)
      .then((res) => setDetail(res.data))
      .catch(() => message.error("Failed to load factor"))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDeactivate = () => {
    if (!id) return;
    factorsApi
      .deactivate(id)
      .then(() => {
        message.success("Factor deactivated");
        setDetail((d) => (d ? { ...d, is_active: false } : null));
      })
      .catch(() => message.error("Failed to deactivate"));
  };

  if (loading || !detail) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  const decayData = detail.ic_decay
    ? Object.entries(detail.ic_decay).map(([h, v]) => ({ horizon: parseInt(h), ic: v }))
    : [];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button onClick={() => navigate("/factors")}>Back to Library</Button>
      </div>
      <h2>Factor Detail</h2>

      <Card title="Expression" size="small" style={{ marginBottom: 16 }}>
        <code style={{ fontSize: 14 }}>{detail.expression}</code>
      </Card>

      <Card title="IC Statistics" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="IC">{detail.mean_ic?.toFixed(4) ?? "-"}</Descriptions.Item>
          <Descriptions.Item label="ICIR">{detail.icir?.toFixed(2) ?? "-"}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Backtest" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Sharpe">{detail.sharpe?.toFixed(2) ?? "-"}</Descriptions.Item>
          <Descriptions.Item label="Max Drawdown">
            {detail.max_drawdown != null ? `${(detail.max_drawdown * 100).toFixed(1)}%` : "-"}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {decayData.length > 0 && (
        <Card title="IC Decay" size="small" style={{ marginBottom: 16 }}>
          <Plot
            data={[
              {
                x: decayData.map((d) => d.horizon),
                y: decayData.map((d) => d.ic),
                type: "bar",
                marker: { color: "#1890ff" },
              },
            ]}
            layout={{
              height: 240,
              margin: { t: 20, r: 20, b: 40, l: 50 },
              xaxis: { title: "Horizon (days)" },
              yaxis: { title: "IC" },
            }}
            config={{ responsive: true }}
            style={{ width: "100%" }}
          />
        </Card>
      )}

      {detail.similar_factors && detail.similar_factors.length > 0 && (
        <Card title="Similar Factors (RAG)" size="small" style={{ marginBottom: 16 }}>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {detail.similar_factors.map((s, i) => (
              <li key={i}>
                <code>{s.expression}</code> — IC: {s.mean_ic?.toFixed(4)}, Sharpe: {s.sharpe?.toFixed(2)}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <Button type="primary" onClick={() => navigate(`/backtest?factor=${encodeURIComponent(detail.expression)}`)}>
          Run Backtest
        </Button>
        {detail.is_active !== false && (
          <Button danger onClick={handleDeactivate}>
            Deactivate Factor
          </Button>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Row, Col, Spin, Card } from "antd";
import Plot from "react-plotly.js";
import StatCard from "../components/StatCard";
import { dashboardApi } from "../api/client";

export default function Dashboard() {
  const [stats, setStats] = useState<{
    active_factors: number;
    average_ic: number;
    best_sharpe: number;
    last_data_update: string | null;
  } | null>(null);
  const [charts, setCharts] = useState<{
    ic_distribution: { x: number[]; y: number[] };
    factor_performance: { factors: string[]; sharpe: number[] };
    equity_curve: { dates: string[]; values: number[] };
    sharpe_ranking: { factors: string[]; sharpe: number[] };
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([dashboardApi.getStats(), dashboardApi.getCharts()])
      .then(([statsRes, chartsRes]) => {
        setStats(statsRes.data);
        setCharts(chartsRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>Quant Research Dashboard</h2>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <StatCard title="Active Factors" value={stats?.active_factors ?? 0} />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard title="Average IC" value={stats?.average_ic?.toFixed(4) ?? "-"} />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard title="Best Sharpe" value={stats?.best_sharpe?.toFixed(2) ?? "-"} />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard title="Last Data Update" value={stats?.last_data_update ?? "-"} />
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="IC Distribution" size="small" style={{ marginBottom: 16 }}>
            <Plot
              data={[
                {
                  x: charts?.ic_distribution?.x ?? [],
                  y: charts?.ic_distribution?.y ?? [],
                  type: "bar",
                  marker: { color: "#1890ff" },
                },
              ]}
              layout={{
                height: 280,
                margin: { t: 20, r: 20, b: 40, l: 50 },
                xaxis: { title: "IC" },
                yaxis: { title: "Count" },
              }}
              config={{ responsive: true }}
              style={{ width: "100%" }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Factor Performance (Sharpe)" size="small" style={{ marginBottom: 16 }}>
            <Plot
              data={[
                {
                  y: charts?.factor_performance?.factors ?? [],
                  x: charts?.factor_performance?.sharpe ?? [],
                  type: "bar",
                  orientation: "h",
                  marker: { color: "#52c41a" },
                },
              ]}
              layout={{
                height: 280,
                margin: { t: 20, r: 20, b: 60, l: 120 },
                xaxis: { title: "Sharpe" },
                yaxis: { title: "" },
              }}
              config={{ responsive: true }}
              style={{ width: "100%" }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Strategy Equity Curve" size="small" style={{ marginBottom: 16 }}>
            <Plot
              data={[
                {
                  x: charts?.equity_curve?.dates ?? [],
                  y: charts?.equity_curve?.values ?? [],
                  type: "scatter",
                  mode: "lines",
                  line: { color: "#1890ff", width: 2 },
                },
              ]}
              layout={{
                height: 280,
                margin: { t: 20, r: 20, b: 40, l: 50 },
                xaxis: { title: "Date" },
                yaxis: { title: "Cumulative Return" },
              }}
              config={{ responsive: true }}
              style={{ width: "100%" }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Sharpe Ranking" size="small" style={{ marginBottom: 16 }}>
            <Plot
              data={[
                {
                  x: charts?.sharpe_ranking?.factors ?? [],
                  y: charts?.sharpe_ranking?.sharpe ?? [],
                  type: "bar",
                  marker: { color: "#722ed1" },
                },
              ]}
              layout={{
                height: 280,
                margin: { t: 20, r: 20, b: 80, l: 50 },
                xaxis: { title: "", tickangle: -45 },
                yaxis: { title: "Sharpe" },
              }}
              config={{ responsive: true }}
              style={{ width: "100%" }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

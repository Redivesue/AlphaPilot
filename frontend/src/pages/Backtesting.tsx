import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Card, Form, Input, InputNumber, Select, Button, Row, Col, message } from "antd";
import Plot from "react-plotly.js";
import { factorsApi, backtestApi } from "../api/client";

export default function Backtesting() {
  const [searchParams] = useSearchParams();
  const presetFactor = searchParams.get("factor") || "";

  const [factors, setFactors] = useState<{ id: string; expression: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{
    sharpe: number;
    max_drawdown: number;
    annual_return: number;
    daily_returns: { date: string; value: number }[];
    drawdown_series: { date: string; value: number }[];
  } | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    factorsApi
      .list({ limit: 50 })
      .then((res) => setFactors(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (presetFactor) {
      const match = factors.find((f) => f.expression === presetFactor);
      if (match) form.setFieldValue("factor_id", match.id);
      else form.setFieldValue("expression", presetFactor);
    }
  }, [presetFactor, factors]);

  const runBacktest = () => {
    const values = form.getFieldsValue();
    const expression = values.expression || factors.find((f) => f.id === values.factor_id)?.expression;
    if (!expression) {
      message.error("Please select a factor or enter an expression");
      return;
    }

    setRunning(true);
    setResult(null);
    backtestApi
      .run({
        factor_expression: expression,
        top_pct: values.top_pct ?? 0.1,
        bottom_pct: values.bottom_pct ?? 0.1,
        transaction_cost: values.transaction_cost ?? 0.0005,
      })
      .then((res) => setResult(res.data))
      .catch(() => {})
      .finally(() => setRunning(false));
  };

  const factorOptions = factors.map((f) => ({
    value: f.id,
    label: f.expression.length > 50 ? f.expression.slice(0, 50) + "..." : f.expression,
  }));

  return (
    <div>
      <h2>Strategy Backtesting</h2>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical" initialValues={{ top_pct: 0.1, bottom_pct: 0.1, transaction_cost: 0.0005 }}>
          <Form.Item name="factor_id" label="Select Factor">
            <Select
              loading={loading}
              placeholder="Choose from library"
              options={factorOptions}
              allowClear
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
          <Form.Item name="expression" label="Or enter expression">
            <Input.TextArea rows={2} placeholder="rank(ts_mean(returns, 10))" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="top_pct" label="Top % Long">
                <InputNumber min={0.01} max={0.5} step={0.01} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="bottom_pct" label="Bottom % Short">
                <InputNumber min={0.01} max={0.5} step={0.01} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="transaction_cost" label="Transaction Cost">
                <InputNumber min={0} max={0.01} step={0.0001} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item>
            <Button type="primary" loading={running} onClick={runBacktest}>
              Run Backtest
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {result && (
        <>
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col><strong>Sharpe:</strong> {result.sharpe?.toFixed(2)}</Col>
              <Col><strong>Max Drawdown:</strong> {(result.max_drawdown * 100)?.toFixed(1)}%</Col>
              <Col><strong>Annual Return:</strong> {result.annual_return != null ? (result.annual_return * 100).toFixed(1) + "%" : "-"}</Col>
            </Row>
          </Card>
          <Row gutter={16}>
            <Col span={12}>
              <Card title="Equity Curve" size="small">
                <Plot
                  data={[
                    {
                      x: result.daily_returns?.map((d) => d.date) ?? [],
                      y: (result.daily_returns ?? []).reduce<number[]>((acc, d, i) => {
                        const prev = acc[i - 1] ?? 1;
                        acc.push(prev * (1 + d.value));
                        return acc;
                      }, []),
                      type: "scatter",
                      mode: "lines",
                      line: { color: "#1890ff" },
                    },
                  ]}
                  layout={{ height: 280, margin: { t: 20, r: 20, b: 40, l: 50 } }}
                  config={{ responsive: true }}
                  style={{ width: "100%" }}
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Drawdown" size="small">
                <Plot
                  data={[
                    {
                      x: result.drawdown_series?.map((d) => d.date) ?? [],
                      y: result.drawdown_series?.map((d) => d.value * 100) ?? [],
                      type: "scatter",
                      mode: "lines",
                      fill: "tozeroy",
                      line: { color: "#ff4d4f" },
                    },
                  ]}
                  layout={{ height: 280, margin: { t: 20, r: 20, b: 40, l: 50 }, yaxis: { title: "Drawdown %" } }}
                  config={{ responsive: true }}
                  style={{ width: "100%" }}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
}

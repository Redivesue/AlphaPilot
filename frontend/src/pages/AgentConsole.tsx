import { useState } from "react";
import { Card, Form, Input, DatePicker, Button, message, Space } from "antd";
import dayjs from "dayjs";
import AgentLogStream from "../components/AgentLogStream";
import { agentApi } from "../api/client";

const { TextArea } = Input;

export default function AgentConsole() {
  const [form] = Form.useForm();
  const [running, setRunning] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  const runAgent = () => {
    agentApi
      .getStatus()
      .then((res) => {
        if (res.data.running) {
          message.warning("Agent already running");
          return;
        }
        const values = form.getFieldsValue();
        const goal = values.goal || "Discover alpha factors with high IC, ICIR, and Sharpe.";
        const tickers = values.tickers ? values.tickers.split(/[\s,]+/).filter(Boolean) : undefined;
        const start = values.range?.[0]?.format("YYYY-MM-DD");
        const end = values.range?.[1]?.format("YYYY-MM-DD");

        setRunning(true);
        agentApi
          .run({ research_goal: goal, tickers, start_date: start, end_date: end })
          .then(() => {
            message.success("Research pipeline started");
            setWsConnected(true);
          })
          .catch((e) => {
            message.error(e.response?.data?.detail || "Failed to start");
            setRunning(false);
          });
      })
      .catch(() => message.error("Failed to check status"));
  };

  return (
    <div>
      <h2>AI Research Agent Console</h2>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical" initialValues={{ goal: "Discover new alpha factors" }}>
          <Form.Item name="goal" label="Research Goal">
            <TextArea rows={3} placeholder="e.g. Discover momentum factors with high IC" />
          </Form.Item>
          <Form.Item name="tickers" label="Stock Universe">
            <Input placeholder="AAPL, MSFT, NVDA..." />
          </Form.Item>
          <Form.Item name="range" label="Time Range">
            <DatePicker.RangePicker
              style={{ width: "100%" }}
              defaultValue={[dayjs("2015-01-01"), dayjs("2025-02-01")]}
            />
          </Form.Item>
        </Form>
        <Space wrap>
          <Button type="primary" loading={running} onClick={() => runAgent()}>
            Run Factor Discovery
          </Button>
          <Button onClick={() => runAgent()}>Evaluate Existing Factors</Button>
          <Button onClick={() => runAgent()}>Run Backtesting</Button>
          <Button onClick={() => runAgent()}>Generate Research Report</Button>
        </Space>
      </Card>

      <AgentLogStream
        wsUrl={agentApi.wsUrl()}
        connected={wsConnected || running}
        onConnect={() => setWsConnected(true)}
        onDisconnect={() => {
          setWsConnected(false);
          setRunning(false);
        }}
      />
    </div>
  );
}

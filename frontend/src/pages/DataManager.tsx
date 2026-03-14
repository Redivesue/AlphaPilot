import { useEffect, useState } from "react";
import { Card, Descriptions, Form, Input, Button, Checkbox, message } from "antd";
import { dataApi } from "../api/client";

export default function DataManager() {
  const [status, setStatus] = useState<{
    start_date: string;
    end_date: string;
    tickers: string[];
    n_days: number;
    n_tickers: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [form] = Form.useForm();

  const loadStatus = () => {
    dataApi
      .getStatus()
      .then((res) => setStatus(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => loadStatus(), []);

  const onUpdate = () => {
    const values = form.getFieldsValue();
    const tickersToAdd = values.tickers_to_add ? values.tickers_to_add.split(/[\s,]+/).filter(Boolean) : undefined;
    const start = values.start_date;
    const end = values.end_date;

    setUpdating(true);
    dataApi
      .update({
        tickers_to_add: tickersToAdd,
        start_date: start || undefined,
        end_date: end || undefined,
        re_evaluate: values.re_evaluate,
      })
      .then((res) => {
        message.success(res.data.message || "Data updated");
        loadStatus();
      })
      .catch((e) => message.error(e.response?.data?.detail || "Update failed"))
      .finally(() => setUpdating(false));
  };

  return (
    <div>
      <h2>Market Data Manager</h2>

      <Card title="Current Data Range" size="small" loading={loading} style={{ marginBottom: 16 }}>
        {status && (
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Range">
              {status.start_date} → {status.end_date}
            </Descriptions.Item>
            <Descriptions.Item label="Tickers">{status.tickers?.join(", ") || "-"}</Descriptions.Item>
            <Descriptions.Item label="Days">{status.n_days}</Descriptions.Item>
            <Descriptions.Item label="Ticker Count">{status.n_tickers}</Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      <Card title="Update Data" size="small">
        <Form form={form} layout="vertical">
          <Form.Item name="tickers_to_add" label="Add Ticker(s)">
            <Input placeholder="TSLA, GOOGL..." />
          </Form.Item>
          <Form.Item name="start_date" label="Start Date">
            <Input placeholder="2015-01-01" />
          </Form.Item>
          <Form.Item name="end_date" label="End Date">
            <Input placeholder="2025-03-01" />
          </Form.Item>
          <Form.Item name="re_evaluate" valuePropName="checked" initialValue={false}>
            <Checkbox>Re-evaluate factors after update</Checkbox>
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={updating} onClick={onUpdate}>
              Update Data
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

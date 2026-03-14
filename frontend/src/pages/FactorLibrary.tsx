import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Table, Button, Select } from "antd";
import { EyeOutlined } from "@ant-design/icons";
import { factorsApi } from "../api/client";

interface Factor {
  id: string;
  expression: string;
  mean_ic: number | null;
  icir: number | null;
  sharpe: number | null;
  is_active: boolean;
}

export default function FactorLibrary() {
  const navigate = useNavigate();
  const [factors, setFactors] = useState<Factor[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState("created_at");

  useEffect(() => {
    factorsApi
      .list({ sort_by: sortBy, limit: 100 })
      .then((res) => setFactors(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [sortBy]);

  const columns = [
    {
      title: "Expression",
      dataIndex: "expression",
      key: "expression",
      ellipsis: true,
      render: (t: string) => <code style={{ fontSize: 12 }}>{t}</code>,
    },
    {
      title: "IC",
      dataIndex: "mean_ic",
      key: "mean_ic",
      width: 80,
      render: (v: number | null) => (v != null ? v.toFixed(4) : "-"),
    },
    {
      title: "ICIR",
      dataIndex: "icir",
      key: "icir",
      width: 80,
      render: (v: number | null) => (v != null ? v.toFixed(2) : "-"),
    },
    {
      title: "Sharpe",
      dataIndex: "sharpe",
      key: "sharpe",
      width: 80,
      render: (v: number | null) => (v != null ? v.toFixed(2) : "-"),
    },
    {
      title: "Status",
      dataIndex: "is_active",
      key: "is_active",
      width: 80,
      render: (v: boolean) => (v ? "Active" : "Inactive"),
    },
    {
      title: "Action",
      key: "action",
      width: 100,
      render: (_: unknown, r: Factor) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => navigate(`/factors/${r.id}`)}>
          View
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2>Factor Library</h2>
        <Select
          value={sortBy}
          onChange={setSortBy}
          style={{ width: 140 }}
          options={[
            { value: "created_at", label: "Newest" },
            { value: "sharpe", label: "Sharpe" },
            { value: "mean_ic", label: "IC" },
            { value: "icir", label: "ICIR" },
          ]}
        />
      </div>
      <Table
        loading={loading}
        dataSource={factors}
        columns={columns}
        rowKey="id"
        pagination={{ pageSize: 20 }}
        size="small"
      />
    </div>
  );
}

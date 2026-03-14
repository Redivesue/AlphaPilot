import { Card } from "antd";

interface StatCardProps {
  title: string;
  value: string | number;
  loading?: boolean;
}

export default function StatCard({ title, value, loading }: StatCardProps) {
  return (
    <Card loading={loading} size="small">
      <div style={{ fontSize: 12, color: "#666", marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 24, fontWeight: 600 }}>{value}</div>
    </Card>
  );
}

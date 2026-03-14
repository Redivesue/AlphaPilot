import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { List, Card } from "antd";
import { FileTextOutlined } from "@ant-design/icons";
import { reportsApi } from "../api/client";

interface Report {
  filename: string;
  created_at: string;
  title?: string;
}

export default function Reports() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    reportsApi
      .list()
      .then((res) => setReports(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2>Research Reports</h2>
      <Card loading={loading}>
        <List
          dataSource={reports}
          renderItem={(r) => (
            <List.Item
              style={{ cursor: "pointer" }}
              onClick={() => navigate(`/reports/${r.filename}`)}
            >
              <List.Item.Meta
                avatar={<FileTextOutlined style={{ fontSize: 24 }} />}
                title={r.title || r.filename}
                description={r.created_at}
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
}

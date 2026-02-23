import { useMemo, useState } from "react";

interface Finding {
  id: string;
  severity: string;
  category: string;
  title: string;
  description: string;
  tool: string;
  file_path: string;
  line_number: number | null;
  remediation: string;
  cwe_id: string;
}

interface FindingsTableProps {
  findings: Finding[];
}

type SortKey = "severity" | "category" | "title" | "tool" | "file_path";

const SEVERITY_ORDER: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
  info: 0,
};

function severityClass(severity: string): string {
  return `severity-${severity}`;
}

export function FindingsTable({ findings }: FindingsTableProps): JSX.Element {
  const [sortKey, setSortKey] = useState<SortKey>("severity");
  const [sortAsc, setSortAsc] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const categories = useMemo(() => {
    const cats = new Set(findings.map((f) => f.category));
    return Array.from(cats).sort();
  }, [findings]);

  const filtered = useMemo(() => {
    let result = findings;
    if (filterSeverity) {
      result = result.filter((f) => f.severity === filterSeverity);
    }
    if (filterCategory) {
      result = result.filter((f) => f.category === filterCategory);
    }
    return result;
  }, [findings, filterSeverity, filterCategory]);

  const sorted = useMemo(() => {
    const copy = [...filtered];
    copy.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "severity") {
        cmp =
          (SEVERITY_ORDER[b.severity] ?? 0) -
          (SEVERITY_ORDER[a.severity] ?? 0);
      } else {
        const aVal = a[sortKey] || "";
        const bVal = b[sortKey] || "";
        cmp = aVal.localeCompare(bVal);
      }
      return sortAsc ? -cmp : cmp;
    });
    return copy;
  }, [filtered, sortKey, sortAsc]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  return (
    <div className="findings-table-container">
      <div className="findings-filters">
        <label>
          Severity:
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
          >
            <option value="">All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>
        </label>
        <label>
          Category:
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
          >
            <option value="">All</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </label>
        <span className="findings-count">
          {sorted.length} of {findings.length} findings
        </span>
      </div>

      <table className="findings-table">
        <thead>
          <tr>
            <th onClick={() => toggleSort("severity")} className="sortable">
              Severity {sortKey === "severity" ? (sortAsc ? "^" : "v") : ""}
            </th>
            <th onClick={() => toggleSort("category")} className="sortable">
              Category {sortKey === "category" ? (sortAsc ? "^" : "v") : ""}
            </th>
            <th onClick={() => toggleSort("title")} className="sortable">
              Title {sortKey === "title" ? (sortAsc ? "^" : "v") : ""}
            </th>
            <th onClick={() => toggleSort("file_path")} className="sortable">
              File {sortKey === "file_path" ? (sortAsc ? "^" : "v") : ""}
            </th>
            <th>Line</th>
            <th onClick={() => toggleSort("tool")} className="sortable">
              Tool {sortKey === "tool" ? (sortAsc ? "^" : "v") : ""}
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((f) => (
            <tr
              key={f.id}
              className={`finding-row ${expandedId === f.id ? "expanded" : ""}`}
              onClick={() =>
                setExpandedId(expandedId === f.id ? null : f.id)
              }
            >
              <td>
                <span className={severityClass(f.severity)}>
                  {f.severity.toUpperCase()}
                </span>
              </td>
              <td>{f.category}</td>
              <td>
                {f.title}
                {expandedId === f.id && (
                  <div className="finding-detail">
                    <p>
                      <strong>Description:</strong> {f.description}
                    </p>
                    {f.remediation && (
                      <p>
                        <strong>Remediation:</strong> {f.remediation}
                      </p>
                    )}
                    {f.cwe_id && (
                      <p>
                        <strong>CWE:</strong> {f.cwe_id}
                      </p>
                    )}
                  </div>
                )}
              </td>
              <td>{f.file_path}</td>
              <td>{f.line_number ?? "-"}</td>
              <td>{f.tool}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {sorted.length === 0 && (
        <p className="no-findings">No findings match current filters.</p>
      )}
    </div>
  );
}

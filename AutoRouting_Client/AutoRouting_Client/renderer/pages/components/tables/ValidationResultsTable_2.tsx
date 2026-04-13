import React from 'react';

const VALIDATION_STATUS = {
  SUCCESS: '정상',
  ERROR: '에러',
  WARNING: '경고',
  PENDING: '진행중'
} as const;


export interface ValidationResult {
  id: string;
  status: keyof typeof VALIDATION_STATUS;
  deviceName: string;
  content: string;
  details?: string;
}

interface ValidationResultsTableProps {
  results: ValidationResult[];
  isLoading?: boolean;
  maxHeight?: string;
}

const StatusCell: React.FC<{ status: keyof typeof VALIDATION_STATUS }> = ({ status }) => {
  const statusText = VALIDATION_STATUS[status];

  return (
    <td>
      <span style={{ width: "100px", color: status === 'ERROR' ? 'red' : status === 'WARNING' ? 'orange' : 'green' }}>
        ● {statusText}
      </span>
    </td>
  );
};

const ValidationResultsTable: React.FC<ValidationResultsTableProps> = ({
  results,
  isLoading = false,
  maxHeight = "400px"
}) => {
  if (!Array.isArray(results)) {
    return (
      <div className="table-container">
        <div className="empty-state">
          <p>올바른 형태의 검증 결과가 아닙니다.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="table-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>검증 결과를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="table-container">
        <div className="empty-state">
          <p>검증 결과가 없습니다.</p>
        </div>
      </div>
    );
  }

  const groupedResults = results.reduce((groups, item) => {
    ; (groups[item.deviceName] = groups[item.deviceName] || []).push(item)
    return groups
  }, {} as Record<string, ValidationResult[]>)

  return (
    <div className="table-container" style={{ maxHeight, overflowY: 'auto' }}>
      <table className="full-width-table">
        <thead>
          <tr>
            <th style={{ width: "120px" }}>장비 명</th>
            <th style={{ width: "80px" }}>상태</th>
            <th>내용</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(groupedResults).map(([deviceName, items]) =>
            items.map((result, idx) => (
              <tr key={result.id}>
                { }
                {idx === 0 && (
                  <td rowSpan={items.length} title={deviceName}>
                    {deviceName}
                  </td>
                )}
                { }
                <StatusCell status={result.status} />
                { }
                <td>
                  <div className="content-cell">
                    <div className="content-text">{result.content}</div>
                    {result.details && (
                      <div className="content-details">{result.details}</div>
                    )}
                  </div>
                </td>
              </tr>
            )))
          }

        </tbody>
      </table>
    </div>
  );
};

export default ValidationResultsTable;
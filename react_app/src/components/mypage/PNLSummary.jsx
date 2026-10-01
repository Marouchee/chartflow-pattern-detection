import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/apiClient'; // 1112 추가 apiClient 임포트

// 마이페이지 상단에 띄울 요약 지표 (승률, 총매매횟수, 누적손익, 누적PnL 등)
export default function PNLSummary() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        // fetch 대신 apiClient.get()을 사용
        const data = await apiClient.get('/mypage/summary/'); // 1112수정
        setSummary(data);

      } catch (err) {
        setError(err.message);
        //더미데이터 삭제
      } finally {
        setLoading(false);
      }
    };
    fetchSummary(); // async 함수 호출
  }, []);

  if (loading) return <div className="text-center p-4">로딩 중...</div>;
  
  // API 요청 실패 시 summary=null 에러
  if (!summary) {
    return <div className="text-red-500 text-center p-4">{error || '데이터를 불러오는데 실패했습니다.'}</div>;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
      <div className="bg-newBox p-4 rounded-lg">
        <p className="text-sm text-gray-400">총 실현 손익</p>
        <p className={`text-xl font-bold ${summary.total_realized_pnl >= 0 ? 'text-green-400' : 'text-red-500'}`}>
          ${parseFloat(summary.total_realized_pnl).toLocaleString()}
        </p>
      </div>
      <div className="bg-newBox p-4 rounded-lg">
        <p className="text-sm text-gray-400">누적 수익률</p>
        <p className={`text-xl font-bold ${summary.cumulative_roi >= 0 ? 'text-green-400' : 'text-red-500'}`}>
          {summary.cumulative_roi}%
        </p>
      </div>
      <div className="bg-newBox p-4 rounded-lg">
        <p className="text-sm text-gray-400">승률</p>
        <p className="text-xl font-bold text-yellow-400">{summary.win_rate}%</p>
      </div>
      <div className="bg-newBox p-4 rounded-lg">
        <p className="text-sm text-gray-400">총 거래 횟수</p>
        <p className="text-xl font-bold">{summary.total_trades}회</p>
      </div>
    </div>
  );
}
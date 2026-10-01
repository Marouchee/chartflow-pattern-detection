import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/apiClient'; // 1112 추가 apiClient 임포트

export default function TradeHistoryTable() {
  const [history, setHistory] = useState({ count: 0, results: [] });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null); // 1112 에러 state 추가

  const SIZE_PER_PAGE = 10; // 한 페이지에 보여줄 항목 수

  useEffect(() => {
    setLoading(true);
    setError(null); // API 호출 시 에러 초기화

    // fetch 대신 apiClient.get()을 사용
    apiClient.get(`/mypage/trade-history/?page=${page}&size=${SIZE_PER_PAGE}`)
      .then(data => {
        setHistory(data);
      })
      .catch(err => {
        console.error(err);
        setError(err.message || '데이터를 불러올 수 없습니다.'); // 더미 데이터 삭제
      })
      .finally(() => {
        setLoading(false); // 성공, 실패 여부와 관계없이 로딩 종료
      });
  }, [page]);

  const totalPages = Math.ceil(history.count / SIZE_PER_PAGE);

  return (
    <div className="bg-newBox p-4 rounded-lg">
      <h3 className="font-bold text-lg mb-4">거래 내역</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr>
              <th className="p-2">시간</th>
              <th className="p-2">심볼</th>
              <th className="p-2">포지션</th>
              <th className="p-2">수량</th>
              <th className="p-2">가격</th>
              <th className="p-2">상태</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="text-center p-4">로딩 중...</td></tr>
            ) : error ? (
              <tr><td colSpan="6" className="text-center p-4 text-red-500">{error}</td></tr>
            ) : history.results.length === 0 ? (
              <tr><td colSpan="6" className="text-center p-4 text-gray-500">거래 내역이 없습니다.</td></tr>
            ) : (
              history.results.map(order => (
                <tr key={order.id} className="border-t border-gray-700">
                  <td className="p-2">{new Date(order.created_at).toLocaleString()}</td>
                  <td className="p-2">{order.symbol}</td>
                  <td className={`p-2 font-bold ${order.side.toLowerCase() === 'buy' || order.side.toLowerCase() === 'long' ? 'text-green-400' : 'text-red-400'}`}>
                    {order.side.toLowerCase() === 'buy' || order.side.toLowerCase() === 'long' ? 'Long' : 'Short'}
                    </td>
                  <td className="p-2">{order.quantity}</td>
                  <td className="p-2">${parseFloat(order.price).toLocaleString()}</td>
                  <td className="p-2">{order.status}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="flex justify-center items-center mt-4 space-x-2">
        <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 rounded bg-gray-600 disabled:opacity-50">이전</button>
        <span>{page} / {totalPages || 1}</span>
        <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages || totalPages === 0} className="px-3 py-1 rounded bg-gray-600 disabled:opacity-50">다음</button>
      </div>
    </div>
  );
}
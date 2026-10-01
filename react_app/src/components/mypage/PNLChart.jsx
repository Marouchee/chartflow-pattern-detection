import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiClient } from '../../services/apiClient';

export default function PNLChart() {
  const [data, setData] = useState([]);
  const [period, setPeriod] = useState('monthly'); // 'weekly', 'monthly', 'all'
  const [error, setError] = useState(null); // 1112 에러 state 추가
  const [error, setError] = useState(null); // 1112 에러 state 추가

useEffect(() => {
    setError(null); // API 호출 시 에러 상태 초기화

    // fetch 대신 apiClient.get() 사용
    apiClient.get(`/mypage/pnl-history/?period=${period}`) //
      .then(apiData => {
        setData(apiData.pnl_entries);
      })
      .catch(err => {
        console.error(err);
        // 더미데이터 삭제, 에러시 빈 차트 띄움
        setError(err.message || '데이터를 불러올 수 없습니다.');
        setData([]); // 차트 데이터 비우기
      });
  }, [period]); // 기간 변경시 >> api재호출

  return (
    <div className="bg-newBox p-4 rounded-lg h-80">
      <div className="flex justify-end gap-2 mb-4">
        <button onClick={() => setPeriod('weekly')} className={`px-2 py-1 text-xs rounded ${period === 'weekly' ? 'bg-yellow-500' : 'bg-gray-600'}`}>주간</button>
        <button onClick={() => setPeriod('monthly')} className={`px-2 py-1 text-xs rounded ${period === 'monthly' ? 'bg-yellow-500' : 'bg-gray-600'}`}>월간</button>
        <button onClick={() => setPeriod('all')} className={`px-2 py-1 text-xs rounded ${period === 'all' ? 'bg-yellow-500' : 'bg-gray-600'}`}>전체</button>
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="date" stroke="#888" fontSize={10} />
          <YAxis stroke="#888" fontSize={10} />
          <Tooltip contentStyle={{ backgroundColor: '#222', border: 'none' }} labelStyle={{ color: '#fff' }} />
          <Legend />
          <Line type="monotone" dataKey="realized_pnl" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/apiClient'; // 1112 추가 apiClient 임포트

export default function PNLCalendar() {
  const [date, setDate] = useState(new Date());
  const [pnlData, setPnlData] = useState({});
  const [error, setError] = useState(null); // 1112 에러 state 추가

  useEffect(() => {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;

    apiClient.get(`/mypage/pnl-calendar/?year=${year}&month=${month}`)
      .then(data => {
        const mappedData = {};
        data.pnl_entries.forEach(entry => {
          mappedData[new Date(entry.date).getDate()] = parseFloat(entry.realized_pnl);
        });
        setPnlData(mappedData);
      })
      .catch(err => {
        console.error(err);
        setError(err.message || '데이터를 불러올 수 없습니다.'); // 더미 데이터 삭제
      });
  }, [date]);

  const monthStart = new Date(date.getFullYear(), date.getMonth(), 1);
  const monthEnd = new Date(date.getFullYear(), date.getMonth() + 1, 0);
  const startDay = monthStart.getDay(); // 0이 일요일임 (1=월, 2=화 ...)
  const daysInMonth = monthEnd.getDate();
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const blanks = Array.from({ length: startDay }, (_, i) => null);
  const cells = [...blanks, ...days];

  const changeMonth = (offset) => { //
    setDate(new Date(date.getFullYear(), date.getMonth() + offset, 1));
  };


  return (
    <div className="bg-newBox p-4 rounded-lg">
      <div className="flex justify-between items-center mb-4">
        <button onClick={() => changeMonth(-1)} className="px-2 py-1 rounded hover:bg-gray-600">‹</button>
        <h3 className="font-bold text-lg">{`${date.getFullYear()}년 ${date.getMonth() + 1}월`}</h3>
        <button onClick={() => changeMonth(1)} className="px-2 py-1 rounded hover:bg-gray-600">›</button>
      </div>

      {/* 에러 표시 추가 */}
      {error ? (
        <div className="text-red-500 text-center p-4">{error}</div>
      ) : (
        <div className="grid grid-cols-7 gap-1 text-center text-xs">
          {['일', '월', '화', '수', '목', '금', '토'].map(day => <div key={day} className="font-semibold text-gray-400">{day}</div>)}
          {cells.map((cell, index) => {
            const pnl = cell ? pnlData[cell] : undefined;

            let bgClass = 'bg-transparent';
            if (cell) {
              bgClass = 'bg-gray-700';
              
              if (pnl !== undefined) {
                // pnl에 따른 배경색 변경
                if (pnl > 0) {
                  bgClass = 'bg-green-700';
                } else if (pnl < 0) {
                  bgClass = 'bg-red-700';
                }
              }
            }

            return (
              <div key={index} className={`p-1 h-16 rounded ${bgClass}`}>
                {cell && (
                  <div className="flex flex-col items-center">
                    <span className="text-sm">{cell}</span>
                    {pnlData[cell] !== undefined && (
                      <span className="text-xs text-white">
                        {pnlData[cell].toFixed(1)}
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
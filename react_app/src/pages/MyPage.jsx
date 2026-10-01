import React, { useState, useEffect } from 'react';
import Modal from '../components/Modal';
import PNLSummary from '../components/mypage/PNLSummary';
import PNLChart from '../components/mypage/PNLChart';
import PNLCalendar from '../components/mypage/PNLCalendar';
import TradeHistoryTable from '../components/mypage/TradeHistoryTable';
import { apiClient } from "../services/apiClient";
import { useLocation } from 'react-router-dom';

export default function MyPage() {
  const [balance, setBalance] = useState(null);
  const [showResetModal, setShowResetModal] = useState(false);
  const [loadingBalance, setLoadingBalance] = useState(true);
  const location = useLocation(); // location 객체 생성

  useEffect(() => { // 실제 잔액을 불러오는 함수
    const fetchBalance = async () => {
      setLoadingBalance(true);
      try {
        const data = await apiClient.get('/mypage/balance/');
        setBalance(data.balance);
      } catch (error) {
        console.error("잔액 조회 실패:", error);
        setBalance(0); // 에러 시 0으로 표시
      } finally {
        setLoadingBalance(false);
      }
    };

    fetchBalance();
  }, [location]); // 페이지 이동 시 재호출

  const handleConfirmReset = async () => {
    try { // 잔액 초기화 API 호출
      const data = await apiClient.post('/mypage/reset-balance/');
      setBalance(data.new_balance); // API 응답으로 온 새 잔액으로 state 업데이트
      alert(data.message); // 성공 알림
    } catch (error) {
      console.error("잔액 초기화 실패:", error);
      alert("잔액 초기화에 실패했습니다.");
    }
    setShowResetModal(false);
  };

  return (
    <div className="space-y-8 text-white">

      {/* 지갑 잔액 표시 및 초기화 버튼 */}
      <section className="bg-newBox p-4 rounded-lg flex justify-between items-center">
        <div>
          <h3 className="text-gray-400 text-sm">현재 지갑 잔액</h3>
          <p className="text-2xl font-bold">
            {parseFloat(balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT
          </p>
        </div>
        <button 
          onClick={() => setShowResetModal(true)}
          className="bg-yellow-400 text-black font-semibold py-2 px-4 rounded hover:bg-yellow-500 transition"
        >
          잔액 초기화
        </button>
      </section>

      {/* 통계 요약 파트, 승률, 라이프타임pnl, 총 거래 횟수, 누적 손익 등  */}
      <section>
        <h2 className="text-2xl font-bold mb-4">요약</h2>
        <PNLSummary />
      </section>

      {/* PnL 그래프 (주간, 월간, 전체) + PnL캘린더 파트 */}
      <section className="grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-2xl font-bold mb-4">PnL Chart</h2>
          <PNLChart />
        </div>
        <div>
          <h2 className="text-2xl font-bold mb-4">PnL Calendar</h2>
          <PNLCalendar />
        </div>
      </section>

      {/* 전체 거래 내역 파트 */}
      <section>
        <h2 className="text-2xl font-bold mb-4">전체 거래 내역</h2>
        <TradeHistoryTable />
      </section>

      {/* 잔액 초기화 확인 모달 */}
      {showResetModal && (
        <Modal onClose={() => setShowResetModal(false)}>
          <div className="p-4">
            <h2 className="text-lg mb-4 font-bold">잔액 초기화 확인</h2>
            <p className="mb-4">
              지갑 잔액을 100,000 USDT로 초기화하시겠습니까? (거래 내역은 유지됩니다)
            </p>
            <div className="flex justify-end gap-2">
              <button 
                onClick={() => setShowResetModal(false)}
                className="px-4 py-2 rounded bg-gray-600 text-white"
              >
                취소
              </button>
              <button 
                onClick={handleConfirmReset}
                className="px-4 py-2 rounded bg-yellow-400 text-black font-semibold"
              >
                확인
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
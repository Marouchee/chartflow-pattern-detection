import React, { useState, useEffect, useCallback } from "react";
import { apiClient } from "../services/apiClient"; 
import TradePanel from "../components/TradePanel";
import TradeTables from "../components/TradeTables";
import TradingViewWidget from "../components/TradingViewWidget";

export default function MockInvestPage() {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true); 
  const [isInitialLoad, setIsInitialLoad] = useState(true); 

  // 종목 상태
  const [currentSymbol, setCurrentSymbol] = useState("BTCUSDT");
  const [searchInput, setSearchInput] = useState("BTCUSDT");

  // 실시간 가격을 API에서 가져오므로 초기값은 null로 설정
  const [currentPrice, setCurrentPrice] = useState(null); 
  const [walletBalance, setWalletBalance] = useState(null); 
  
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    setCurrentSymbol(searchInput.toUpperCase().trim());
  };
  
  const fetchPositions = useCallback(async () => {
    // 주기적 갱신 시 로딩 스피너 방지
    if (isInitialLoad) {
        setLoading(true);
    }
    
    try {
      const data = await apiClient.get(
        `/papertrade/positions/?symbol=${currentSymbol}`
      );
      setPositions(data);
    } catch (err) {
      console.error("포지션 로딩 실패:", err);
      setPositions([]); 
    } finally {
      // 최초 로딩이 끝나면 loading 상태를 false로 바꾸고 isInitialLoad를 false로 설정한다
      if (isInitialLoad) {
        setLoading(false);
        setIsInitialLoad(false); 
      }
    }
  }, [currentSymbol, isInitialLoad]); 

  const fetchWalletBalance = useCallback(async () => {
    try {
      const data = await apiClient.get('/mypage/balance/');
      setWalletBalance(data.balance);
    } catch (error) {
      console.error("잔액 조회 실패:", error);
      setWalletBalance("0");
    }
  }, []);

  const fetchCurrentPrice = useCallback(async () => {
    try {
        const data = await apiClient.get(`/papertrade/price/?symbol=${currentSymbol}`);
        setCurrentPrice(parseFloat(data.price));
        // 가격 업데이트 성공 후 포지션 갱신
        fetchPositions(); 
    } catch (err) {
        console.error("실시간 가격 로딩 실패:", err);
        setCurrentPrice(null); 
    }
  }, [currentSymbol, fetchPositions]); 

  const refreshAllData = useCallback(() => {
    // 주문/청산 시에는 가격, 포지션, 잔액 모두 즉시 갱신
    fetchCurrentPrice(); 
    fetchWalletBalance();
  }, [fetchCurrentPrice, fetchWalletBalance]);

  // 실시간 가격 업데이트 로직 (3초 간격)
  useEffect(() => {
    fetchCurrentPrice(); // 최초 실행 
    const interval = setInterval(() => {
        fetchCurrentPrice(); // 주기적 실행
    }, 3000); 

    return () => clearInterval(interval);
  }, [fetchCurrentPrice]); 

  // 심볼 변경 시 잔액만 갱신한다 (fetchCurrentPrice가 이미 fetchPositions를 호출했으므로)
  useEffect(() => {
    fetchWalletBalance(); 
  }, [currentSymbol, fetchWalletBalance]); 

  // 주문 성공 시 콜백
  const handleOrderSuccess = () => {
    refreshAllData();
  };

  return (
    <div className="max-w-screen-xl mx-auto p-4">
      {/* 상단 종목 검색바 */}
      <div className="mb-4 flex items-center gap-4 bg-layer p-3 rounded border border-gray-600">
        <span className="text-white font-bold text-lg">종목 검색:</span>
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input 
                type="text" 
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="bg-newBox text-white px-3 py-1 rounded border border-gray-500 focus:outline-none focus:border-yellow-400"
                placeholder="예: ETHUSDT"
            />
            <button 
                type="submit" 
                className="bg-yellow-400 text-black px-4 py-1 rounded font-bold hover:bg-yellow-500 transition"
            >
                이동
            </button>
        </form>
        <span className="text-gray-400 text-sm ml-2">
            * 현재 선택된 종목: <span className="text-yellow-400 font-bold">{currentSymbol}</span>
        </span>
      </div>

      <div className="grid grid-cols-[3fr_1fr] gap-4">
        <div className="h-[500px] border rounded-none overflow-hidden">
          <TradingViewWidget
            key={currentSymbol} 
            symbol={currentSymbol} 
            onSymbolChange={setCurrentSymbol}
          />
        </div>
        
        <TradePanel
          symbol={currentSymbol} 
          marketPrice={currentPrice || 0} 
          onOrderSuccess={handleOrderSuccess} 
          walletBalance={walletBalance}
        />
      </div>
      
      <div className="mt-2 border rounded-none">
        {/* TradeTables에 isInitialLoad prop 전달 */}
        <TradeTables
          positions={positions} 
          loading={loading} 
          isInitialLoad={isInitialLoad} 
          currentPrice={currentPrice || 0} 
          onRefreshAll={refreshAllData} 
        /> 
      </div>
    </div>
  );
}
import React, { useState, useEffect } from "react";
import { apiClient } from "../services/apiClient"; 
import Modal from "./Modal"; 

export default function TradeTables({ positions, loading, isInitialLoad, currentPrice, onRefreshAll }) {
  const [activeTab, setActiveTab] = useState("position");
  const [openOrders, setOpenOrders] = useState([]);      
  const [loadingOpenOrders, setLoadingOpenOrders] = useState(false);

  const [showCloseModal, setShowCloseModal] = useState(false); 
  // selectedPosition 객체에 해당 포지션의 실시간 가격(current_price)이 포함되도록 변경
  const [selectedPosition, setSelectedPosition] = useState(null); 

  const [showTpSlModal, setShowTpSlModal] = useState(false); 
  const [tpPrice, setTpPrice] = useState(""); 
  const [slPrice, setSlPrice] = useState(""); 

  // 미체결 탭 데이터 로딩
  useEffect(() => {
    if (activeTab === 'open') {
      const fetchOpenOrders = async () => {
        setLoadingOpenOrders(true);
        try {
          const data = await apiClient.get("/papertrade/pending/");
          setOpenOrders(data);
        } catch (error) {
          console.error("미체결 주문 조회 실패:", error);
          setOpenOrders([]); 
        } finally {
          setLoadingOpenOrders(false);
        }
      };
      fetchOpenOrders();
    }
  }, [activeTab, onRefreshAll]); 

  // 주문 취소 핸들러 API 호출
  const handleCancelOrder = async (orderId) => {
    if (!window.confirm("이 지정가 주문을 취소하시겠습니까?")) {
      return;
    }
    try {
      const payload = { order_id: orderId };
      const data = await apiClient.post("/papertrade/cancel/", payload);
      alert(data.message); 
      if (onRefreshAll) {
        onRefreshAll(); 
      }
    } catch (error) {
      console.error("주문 취소 실패:", error);
      alert("주문 취소에 실패했습니다: " + (error.response?.data?.error || error.message));
    }
  };

  // 모달 열기 시 해당 포지션 심볼의 가격 정보 사용
  const handleOpenCloseModal = (position) => {
    setSelectedPosition(position); 
    setShowCloseModal(true);     
  };

  // '종료' 모달 확인 시 API 호출
  const handleConfirmClose = async () => {
    if (!selectedPosition) return;

    try {
      const payload = {
        position_id: selectedPosition.id,
      };
      const data = await apiClient.post("/papertrade/close/", payload);

      alert(data.message); 
      
      if (onRefreshAll) {
        onRefreshAll();
      }

    } catch (error) {
      console.error("포지션 종료 실패:", error);
      alert("포지션 종료에 실패했습니다: " + (error.response?.data?.error || error.message));
    } finally {
      setShowCloseModal(false);     
      setSelectedPosition(null);  
    }
  };
  
  // 모달 열기 시 해당 포지션 심볼의 가격 정보 사용
  const handleOpenTpSlModal = (position) => {
    setSelectedPosition(position); 
    setTpPrice(position.tp_price || ""); 
    setSlPrice(position.sl_price || ""); 
    setShowTpSlModal(true);      
  };

  // TP/SL '확인' 모달 클릭 시 API 호출
  const handleConfirmTpSl = async () => {
    if (!selectedPosition) return;

    try {
      const payload = {
        position_id: selectedPosition.id,
        tp: tpPrice, 
        sl: slPrice  
      };
      await apiClient.post("/papertrade/tpsl/", payload);
      
      alert("TP/SL이 설정되었습니다.");
      
      if (onRefreshAll) {
        onRefreshAll();
      }

    } catch (error) {
      console.error("TP/SL 설정 실패:", error);
      alert("TP/SL 설정에 실패했습니다: " + (error.response?.data?.error || error.message));
    } finally {
      setShowTpSlModal(false);      
      setSelectedPosition(null);    
      setTpPrice("");               
      setSlPrice("");               
    }
  };

  // PNL 데이터 계산 로직
  const calculatedPositions = (positions || []).map((p) => {
    const entry = parseFloat(p.entry_price); 
    const qty = parseFloat(p.quantity);     
    let pnl = 0;                            
    
    // 포지션 객체에 포함된 해당 심볼의 실시간 가격을 PNL 계산에 사용한다
    const markPrice = p.current_price ? parseFloat(p.current_price) : 0; 
    
    if (markPrice > 0) { 
        if (p.side === "buy") { 
            pnl = (markPrice - entry) * qty; 
        } else { 
            pnl = (entry - markPrice) * qty; 
        }
    }

    // 소수점 자리수 통일을 위한 toFixed 적용
    const fixedEntry = entry.toFixed(4);
    const fixedMark = markPrice > 0 ? markPrice.toFixed(4) : '--';
    const fixedLiq = p.liq_price ? parseFloat(p.liq_price).toFixed(4) : '--';
    const fixedTP = p.tp_price ? parseFloat(p.tp_price).toFixed(4) : null;
    const fixedSL = p.sl_price ? parseFloat(p.sl_price).toFixed(4) : null;
    
    // 종목 셀 표시용 포지션 상세 정보
    const isLong = p.side === 'buy';
    const sideLabel = isLong ? 'Long' : 'Short';
    const sideColor = isLong ? 'bg-long' : 'bg-short';
    const marginMode = 'Isolated'; // 마진 모드는 상호작용에 반응하도록 수정할것

    return {
      symbol: p.symbol,
      quantity: qty.toFixed(8),
      entry: fixedEntry,
      mark: fixedMark, 
      pnl: pnl, 
      liq: fixedLiq, 
      id: p.id,         
      tp: fixedTP, 
      sl: fixedSL, 
      originalPosition: p,
      
      // 종목 셀 표기용 상세 정보
      sideLabel,
      sideColor,
      marginMode,
      leverage: p.leverage,
      // 모달에서 사용할 포지션별 현재 가격을 미리 포맷팅하여 저장한다.
      priceForModal: markPrice > 0 ? markPrice.toFixed(4) : '0.0000',
    };
  });

  return (
    <div className="p-4 border rounded-none bg-layer text-white">
      {/* 탭 네비게이션 */}
      <div className="flex justify-start gap-4 text-sm border-b border-gray-600 mb-2">
        <button onClick={() => setActiveTab("position")} className={`pb-2 font-semibold ${activeTab === "position" ? "border-b-2 border-yellow-400 text-white" : "text-gray-400"}`}>포지션</button>
        <button onClick={() => setActiveTab("open")} className={`pb-2 font-semibold ${activeTab === "open" ? "border-b-2 border-yellow-400 text-white" : "text-gray-400"}`}>미체결</button>
      </div>

      {/* 포지션 탭 */}
      {/* isInitialLoad가 true일 때만 로딩 메시지 표시 (최초로딩) */}
      {activeTab === "position" && isInitialLoad && loading && (
        <div className="text-center text-gray-400 py-4">
          포지션 정보를 불러오는 중입니다...
        </div>
      )}

      {activeTab === "position" && (!isInitialLoad || !loading) && (
        <table className="w-full text-sm text-left table-fixed">
          <thead className="text-gray-400 border-b border-gray-600">
            <tr>
              {/* 고정 너비 적용 */}
              <th className="w-[15%]">종목</th>
              <th className="w-[12%]">수량</th>
              <th className="w-[12%]">진입가</th>
              <th className="w-[12%]">현재가</th>
              <th className="w-[16%]">미실현손익</th>
              <th className="w-[16%]">강제청산가</th>
              <th className="w-[12%] pr-2">TP/SL</th> 
              <th className="w-[5%] text-right pr-2">동작</th> 
            </tr>
          </thead>
          <tbody>
            {calculatedPositions.length === 0 ? (
              <tr><td colSpan="8" className="text-center text-gray-500 py-4">오픈된 포지션이 없습니다.</td></tr>
            ) : (
              calculatedPositions.map((p, i) => (
                <tr key={i} className="text-white h-14">{/* 포지션별 높이설정임 */}
                  {/* 종목: 상세 정보 표시 */}
                  <td className="align-middle">
                    <div className="font-bold mb-1">{p.symbol}</div>
                    <div className="flex space-x-1.5 text-xs">
                        <span className={`px-1 rounded-sm text-black ${p.sideColor}`}>
                            {p.sideLabel}
                        </span>
                        <span className="px-1 rounded-sm bg-gray-700 text-gray-300">
                            {p.marginMode}
                        </span>
                        <span className="px-1 rounded-sm bg-gray-700 text-gray-300">
                            {p.leverage}x
                        </span>
                    </div>
                  </td>
                  {/* 수량: 8자리 고정 */}
                  <td className="align-middle">{p.quantity}</td>
                  {/* 가격: 4자리 고정 */}
                  <td className="align-middle">{p.entry}</td>
                  <td className="align-middle">{p.mark}</td>
                  {/* 미실현손익: 소수점 2자리 고정 */}
                  <td className={`align-middle font-semibold ${p.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {p.mark !== '--' ? `${p.pnl.toFixed(2)} USDT` : '--'}
                  </td>
                  <td className="align-middle">{p.liq}</td>
                  <td className="pr-2 text-xs align-middle relative">
                    <div className="flex flex-col space-y-0.5 items-start">
                      {/* 익절가 */}
                      <div className={`font-semibold ${p.tp ? 'text-green-400' : 'text-gray-400'}`}>
                        TP: {p.tp || "--"}
                      </div>
                      {/* 손절가 */}
                      <div className={`font-semibold ${p.sl ? 'text-red-400' : 'text-gray-400'}`}>
                        SL: {p.sl || "--"}
                      </div>
                    </div>
                    <button 
                        onClick={() => handleOpenTpSlModal(p.originalPosition)}
                        className="text-yellow-400 underline absolute right-3 top-1/2 transform -translate-y-1/2 mr-1"
                    >
                        edit
                    </button>
                  </td>
                  
                  {/* 종료 버튼 */}
                  <td className="text-right pr-2 align-middle">
                    <button 
                      onClick={() => handleOpenCloseModal(p.originalPosition)} 
                      className="text-yellow-400 underline text-xs"
                    >
                      종료
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}

      {/* 미체결 탭 */}
      {activeTab === "open" && loadingOpenOrders && (
        <div className="text-center text-gray-400 py-4">
          미체결 주문을 불러오는 중입니다...
        </div>
      )}

      {activeTab === "open" && !loadingOpenOrders && (
        <table className="w-full text-sm text-left table-fixed">
          <thead className="text-gray-400 border-b border-gray-600">
            <tr>
              <th className="w-[20%]">시간</th>
              <th className="w-[15%]">종목</th>
              <th className="w-[10%]">포지션</th>
              <th className="w-[15%]">지정가</th>
              <th className="w-[10%]">수량</th>
              <th className="w-[15%]">증거금(USDT)</th>
              <th className="w-[15%] text-right pr-2">동작</th>
            </tr>
          </thead>
          <tbody>
            {openOrders.length === 0 ? (
              <tr><td colSpan="7" className="text-center text-gray-500 py-4">미체결 주문이 없습니다.</td></tr>
            ) : (
              openOrders.map((o) => (
                <tr key={o.id} className="text-white">
                  <td>{new Date(o.created_at).toLocaleString()}</td>
                  <td>{o.symbol}</td>
                  <td className={`font-bold ${o.side === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                    {o.side === 'buy' ? 'Long' : 'Short'}
                  </td>
                  {/* 지정가: 소수점 4자리 고정 */}
                  <td>{parseFloat(o.trigger_price).toFixed(4)}</td>
                  {/* 수량: 소수점 8자리 고정 */}
                  <td>{parseFloat(o.quantity).toFixed(8)}</td>
                  {/* 증거금: 소수점 2자리 고정 */}
                  <td>{parseFloat(o.margin).toFixed(2)}</td>
                  <td className="text-right pr-2">
                    <button 
                      onClick={() => handleCancelOrder(o.id)} 
                      className="text-red-500 underline text-xs"
                    >
                      취소
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}

      {/* 포지션 종료 확인 모달 */}
      {showCloseModal && selectedPosition && (
        <Modal onClose={() => setShowCloseModal(false)}>
          <div className="p-4">
            <h2 className="text-lg mb-4 font-bold">포지션 종료 확인</h2>
            <p className="mb-4">
              {selectedPosition.symbol} 포지션을 실시간 시장가로 종료하시겠습니까? (가격은 서버에서 결정됨)
            </p>
            <div className="flex justify-end gap-2">
              <button 
                onClick={() => setShowCloseModal(false)}
                className="px-4 py-2 rounded bg-gray-600 text-white"
              >
                취소
              </button>
              <button 
                onClick={handleConfirmClose}
                className="px-4 py-2 rounded bg-yellow-400 text-black font-semibold"
              >
                확인
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* TP/SL 설정 모달 */}
      {showTpSlModal && selectedPosition && (
        <Modal onClose={() => setShowTpSlModal(false)}>
          <div className="p-4">
            <h2 className="text-lg mb-4 font-bold">{selectedPosition.symbol} TP/SL 설정</h2>
            <div className="mb-4">
              <label htmlFor="tpInput" className="block text-sm text-gray-300 mb-1">익절가 (TP)</label>
              <input 
                id="tpInput" 
                type="number"
                className="w-full p-1 bg-newBox text-white border border-gray-500 rounded" 
                // selectedPosition.current_price 참조
                placeholder={`현재가: ${selectedPosition.current_price ? parseFloat(selectedPosition.current_price).toFixed(4) : '0.0000'}`}
                value={tpPrice}
                onChange={(e) => setTpPrice(e.target.value)}
              />
            </div>
            <div className="mb-4">
              <label htmlFor="slInput" className="block text-sm text-gray-300 mb-1">손절가 (SL)</label>
              <input 
                id="slInput" 
                type="number"
                className="w-full p-1 bg-newBox text-white border border-gray-500 rounded" 
                // selectedPosition.current_price 참조
                placeholder={`현재가: ${selectedPosition.current_price ? parseFloat(selectedPosition.current_price).toFixed(4) : '0.0000'}`}
                value={slPrice}
                onChange={(e) => setSlPrice(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button 
                onClick={() => setShowTpSlModal(false)}
                className="px-4 py-2 rounded bg-gray-600 text-white"
              >
                취소
              </button>
              <button 
                onClick={handleConfirmTpSl}
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
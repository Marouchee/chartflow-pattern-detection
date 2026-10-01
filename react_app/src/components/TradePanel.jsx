import React, { useState, useEffect } from "react";
import Modal from "./Modal";
import TradeTables from "./TradeTables";
import { apiClient } from "../services/apiClient";

export default function TradePanel({ 
  symbol, 
  marketPrice, 
  onOrderSuccess, 
  showOnlyTables = false,
  walletBalance
}) {
  const [orderType, setOrderType] = useState("limit");
  const [marginMode, setMarginMode] = useState("isolated");
  const [leverage, setLeverage] = useState(10); 
  
  const [orderAmount, setOrderAmount] = useState(""); 
  const [quantity, setQuantity] = useState(0); 
  
  const [price, setPrice] = useState("");
  const [orderSide, setOrderSide] = useState("buy"); // 이 상태는 UI 표시용으로만 남겨둔다
  const [showLeverageModal, setShowLeverageModal] = useState(false);

  // 수량 자동 계산 로직
  useEffect(() => {
    const amount = parseFloat(orderAmount);
    const lev = parseFloat(leverage);
    const priceToUse = orderType === 'limit' ? parseFloat(price) : marketPrice;

    if (amount > 0 && priceToUse > 0 && lev > 0) {
      setQuantity((amount * lev) / priceToUse);
    } else {
      setQuantity(0);
    }
  }, [orderAmount, price, orderType, marketPrice, leverage]);
  
  const handleOrder = async (side) => {
    
    const payload = {
      symbol,
      side: side,
      order_type: orderType, 
      price: orderType === "market" ? marketPrice : parseFloat(price), 
      quantity: parseFloat(quantity),
      margin: parseFloat(orderAmount), 
      margin_mode: marginMode,
      leverage: leverage
    };

    if (!payload.quantity || payload.quantity <= 0 || !payload.margin || payload.margin <= 0) {
        alert("주문 수량 또는 금액이 유효하지 않습니다.");
        return;
    }

    console.log("보내는 주문 payload:", payload);

    try {
      const data = await apiClient.post("/papertrade/order/", payload);
      
      alert(data.message); 
      onOrderSuccess(); 
      setOrderAmount(""); 
      
    } catch (error) {
      console.error("서버 오류:", error);
      alert("주문 실패: " + (error.response?.data?.error || error.message));
    }
  };

  if (showOnlyTables) return <TradeTables />;

  const formatBalance = (balance) => {
    if (balance === null || balance === undefined) {
      return <span className="text-gray-400">로딩 중...</span>;
    }
    const number = parseFloat(balance);
    return (
      <span>
        {number.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT
      </span>
    );
  };

  return (
    <div className="p-4 border border-gray-600 rounded-none bg-layer text-white w-[300px] h-[499px] box-border">
      
      {/* 상단: 마진 모드 및 레버리지 설정 */}
      <div className="flex justify-between mb-4">
        <select
          value={marginMode}
          onChange={(e) => setMarginMode(e.target.value)}
          className="bg-transparent text-white underline outline-none cursor-pointer"
        >
          <option value="isolated" className="bg-layer">isolated</option>
          <option value="cross" className="bg-layer">cross</option>
        </select>
        
        <button onClick={() => setShowLeverageModal(true)} className="underline">
            {leverage}x
        </button>
      </div>

      {/* 주문 유형 탭 */}
      <div className="flex justify-start gap-6 text-sm border-b border-gray-600 mb-4">
        <button onClick={() => setOrderType("limit")} className={`pb-2 font-semibold ${orderType === "limit" ? "border-b-2 border-yellow-400 text-white" : "text-gray-400"}`}>지정가</button>
        <button onClick={() => setOrderType("market")} className={`pb-2 font-semibold ${orderType === "market" ? "border-b-2 border-yellow-400 text-white" : "text-gray-400"}`}>시장가</button>
      </div>

      {/* 가격 입력 */}
      <div className="mb-4">
        <label htmlFor="priceInput" className="block text-sm text-gray-300 mb-1">주문 가격 (USDT)</label>
        {orderType === "limit" ? (
          <input id="priceInput" type="number" className="w-full p-1 bg-newBox text-white border border-gray-500 rounded" placeholder="주문가격" value={price} onChange={(e) => setPrice(e.target.value)} />
        ) : (
          <input id="priceInput" className="w-full p-1 bg-newBox text-gray-400 border border-gray-500 rounded" value="시장가" readOnly />
        )}
      </div>

      {/* 주문 금액 입력 */}
      <div className="mb-4">
        <label htmlFor="amountInput" className="block text-sm text-gray-300 mb-1">주문 금액 (USDT)</label>
        <input 
          id="amountInput" 
          type="number"
          className="w-full p-1 bg-newBox text-white border border-gray-600 rounded" 
          placeholder="주문 금액" 
          value={orderAmount} 
          onChange={(e) => setOrderAmount(e.target.value)} 
        />
        <div className="text-sm text-gray-400 mt-1">
          수량: {quantity.toFixed(8)} {symbol.replace('USDT', '')}
        </div>
      </div>

      {/* 매수/매도 버튼 */}
      <div className="grid grid-cols-2 gap-2 mb-12">
        {/* handleOrder에 'buy' 직접 전달 */}
        <button onClick={() => handleOrder("buy")} className="bg-long text-white py-1 rounded">Open Long</button>
        {/* handleOrder에 'sell' 직접 전달 */}
        <button onClick={() => handleOrder("sell")} className="bg-short text-white py-1 rounded">Open Short</button>
      </div>

      {/* 하단: 자산 정보 */}
      <div className="text-sm text-gray-300 space-y-2">
        <div className="flex justify-between">
          <span>지갑 잔액:</span>
          {formatBalance(walletBalance)}
        </div>
        <div className="flex justify-between">
          <span>총 평가:</span>
          {formatBalance(walletBalance)}
        </div>
        <div className="flex justify-between">
          <span>주문 가능:</span>
          {formatBalance(walletBalance)}
        </div>
      </div>

      {/* 레버리지 설정 모달 */}
      {showLeverageModal && (
        <Modal onClose={() => setShowLeverageModal(false)}>
          {/* 모달 너비 지정 */}
          <div className="w-[450px]"> 
            
            {/* 모달 헤더 */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Adjust Leverage</h2>
            </div>

            {/* 정보 표시 */}
            <div className="mb-6 text-lg font-semibold text-gray-300">
              <span>{symbol}</span>
              <span className="mx-2 text-gray-500">•</span>
              <span>{marginMode.charAt(0).toUpperCase() + marginMode.slice(1)}</span>
              <span className="mx-2 text-gray-500">•</span>
              <span className="text-yellow-400">{leverage}x</span>
            </div>

            {/* 레버리지 입력 필드 */}
            <div className="mb-8">
              <label htmlFor="leverageInput" className="block text-sm text-gray-400 mb-2">Leverage</label>
              <div className="relative flex items-center">
                <input 
                  id="leverageInput"
                  type="number" 
                  value={leverage} 
                  min={1} 
                  max={100} 
                  onChange={(e) => {
                    const val = parseInt(e.target.value, 10);
                    if (isNaN(val)) {
                      setLeverage(0);
                    } else {
                      setLeverage(val < 1 ? 1 : (val > 100 ? 100 : val));
                    }
                  }} 
                  className="w-full p-3 bg-gray-700 text-white border border-gray-600 rounded pr-10 focus:outline-none focus:border-yellow-400 text-lg" 
                />
                <span className="absolute right-4 text-gray-400 text-lg">x</span>
              </div>
            </div>

            {/* 슬라이더 */}
            <div className="mb-8 px-1">
              <input 
                type="range" 
                min="1" 
                max="125" 
                step="1" 
                value={leverage} 
                onChange={(e) => setLeverage(parseInt(e.target.value, 10))} 
                className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-2 px-1">
                <span>1x</span>
                <span>25x</span>
                <span>50x</span>
                <span>75x</span>
                <span>100x</span>
                <span>125x</span>
              </div>
            </div>

            {/* 주문 가능 금액 정보 */}
            <div className="mb-4 p-3 bg-gray-800 rounded text-sm leading-relaxed">
              <div>해당 레버리지를 통해 아래 크기의 포지션을 개설할 수 있습니다.</div>
              <div className="font-bold">
                {(parseFloat(walletBalance || 0) * leverage).toLocaleString('en-US', { maximumFractionDigits: 0 })} USDT
                </div>
            </div>

            {/* 경고 메시지 */}
            <div className="mb-8 p-3 bg-gray-800 rounded border border-gray-700 text-sm flex items-start">
              <div className="text-yellow-400 mr-2 mt-0.5">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </div>
              <div>
                <p className="font-semibold text-gray-300 mb-1">레버리지 조정은 보유 포지션과 주문에 동시 적용됩니다.</p>
                <p className="text-gray-400 leading-snug">10배 이상의 레버리지를 사용할 경우 작은 가격 변동에도 포지션이 강제 청산에 노출될 수 있습니다. 주의하여 거래하시기 바랍니다.</p>
              </div>
            </div>

            {/* 하단 버튼 */}
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setShowLeverageModal(false)} 
                className="px-6 py-3 bg-gray-700 text-white rounded hover:bg-gray-600 transition font-medium"
              >
                Cancel
              </button>
              <button 
                onClick={() => setShowLeverageModal(false)} 
                className="px-6 py-3 bg-yellow-400 text-black font-bold rounded hover:bg-yellow-500 transition"
              >
                Confirm
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
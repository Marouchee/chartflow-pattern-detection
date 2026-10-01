import React, { useEffect, useRef, memo } from 'react';

function TradingViewWidget({ symbol, onSymbolChange }) {
  const containerRef = useRef(null);
  
  const widgetRef = useRef(null); // 'ready'콜백에서 받은 위젯 인스턴스를 저장

  useEffect(() => { // 마운트 시 위젯 생성
    if (!containerRef.current || !window.TradingView || !window.TradingView.widget) {
      console.error("TradingViewWidget: 컨테이너 또는 라이브러리가 준비되지 않았습니다.");
      return;
    }

    const widgetOptions = {
      symbol: symbol || "NASDAQ:AAPL",
      autosize: true,
      interval: "5",
      timezone: "Etc/UTC",
      theme: "dark",
      style: "1",
      locale: "kr",
      container_id: containerRef.current.id,
      allow_symbol_change: true,
      
      // 10/29 오류수정
      // 'onChartReady'가 아니라 'ready' 콜백을 옵션 안에 전달한다.
      ready: (widget) => { // 'widget' 파라미터: 실제 위젯 인스턴스, ref에 저장하여 클린업이나 다른 useEffect에서 사용
        console.log("TradingView Widget이 준비되었습니다.");
        widgetRef.current = widget;
        // 2. 'ready' 콜백 안에서 이벤트를 구독함. .chart() 메서드를 호출해야 .subscribe()를 사용가능함
        widget.chart().subscribe('symbol_change', (symbolInfo) => {
          console.log("TradingView 심볼 변경:", symbolInfo.ticker);
          if (onSymbolChange) {
            onSymbolChange(symbolInfo.ticker);
          }
        });
      },
    };

    new window.TradingView.widget(widgetOptions); // 'new' 생성자는 위젯을 초기화함. 인스턴스 반환은 하지 않음. 인스턴스는 'ready' 콜백으로 전달됨

    return () => { // 4. 클린업 함수
      // 'ready' 콜백에서 ref에 저장했던 인스턴스를 사용하여 remove() 호출
      if (widgetRef.current && typeof widgetRef.current.remove === 'function') {
        console.log("TradingView Widget을 제거합니다.");
        widgetRef.current.remove();
        widgetRef.current = null;
      }
    };
  }, []); // 마운트 시 한 번만 실행

  // 부모로부터 'symbol' prop이 변경되었을 때
  useEffect(() => {
    // 'ready' 콜백이 실행되어 ref에 위젯이 저장되었는지 확인
    if (widgetRef.current && symbol && typeof widgetRef.current.chart === 'function') {
      // 위젯의 chart() 객체에서 setSymbol() 호출
      widgetRef.current.chart().setSymbol(symbol);
    }
  }, [symbol]); // 'symbol' prop이 변경될 때마다 실행

  return (
    <div 
      id="tradingview_widget_container" 
      ref={containerRef} 
      className="h-full w-full" 
    />
  );
}

export default memo(TradingViewWidget);
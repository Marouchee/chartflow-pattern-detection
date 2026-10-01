import React, { useState, useEffect } from "react";
import { getCSRFToken } from "../utils/csrf";
import { strategyGuide, defaultStrategy } from "../data/strategyGuide";

// ChartAnalysisPage: 사용자가 차트 이미지를 업로드하고 분석 결과를 확인할 수 있는 페이지
export default function ChartAnalysisPage() {
  // 업로드 탭
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewURL, setPreviewURL] = useState("");

  const [resultImageURL, setResultImageURL] = useState(""); // 업로드 분석 결과 이미지
  const [patterns, setPatterns] = useState([]); // [{label, conf}, ...]
  const [patternLabel, setPatternLabel] = useState(""); // 하위호환: 단일 레이블

  // 종목/기간 탭
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [interval, setInterval] = useState("1d"); // 1d / 1h / 15m ...
  const [resultURL, setResultURL] = useState(""); // by-symbol 결과 이미지

  const [strategyDetails, setStrategyDetails] = useState([]);

  // 공통
  const [loading, setLoading] = useState(false);

  const backendURL =
    process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:8000";

  /** 주어진 URL을 절대 URL로 보정하고 캐시버스터를 붙여 리로드를 강제 */
  const absolutizeAndBust = (raw) => {
    if (!raw) return "";
    const normalized = String(raw).replace(/\\/g, "/");
    const isAbs = /^https?:\/\//i.test(normalized);
    const abs = isAbs
      ? normalized
      : `${backendURL}${normalized.startsWith("/") ? "" : "/"}${normalized}`;
    const sep = abs.includes("?") ? "&" : "?";
    return `${abs}${sep}cb=${Date.now()}`;
  };

  /** 서버 응답의 패턴 데이터를 state에 반영 (배열/단일 라벨 모두 대응) */
  const applyPatterns = (data) => {
    let patternsArray = []; // 최종적으로 state에 저장될 배열

    // 1. data.patterns (객체 배열)가 있는지 확인
    if (Array.isArray(data?.patterns) && data.patterns.length > 0) {
      patternsArray = data.patterns;
    }
    // 2. 1번이 아닐 경우, data.pattern_labels (문자열 배열)가 있는지 확인
    else if (Array.isArray(data?.pattern_labels) && data.pattern_labels.length > 0) {
      // state 형식(객체 배열)에 맞게 변환
      patternsArray = data.pattern_labels.map(label => ({ 
        label: label, 
        conf: null // conf 정보가 없으므로 null로 설정
      }));
    } 
    // 3. 위 두 형식 모두 없고, data.pattern_label (단일 문자열)만 있는지 확인
    else if (!Array.isArray(data?.patterns) && data?.pattern_label) {
      // 단일 문자열도 객체 배열로 변환
      patternsArray = [{ label: data.pattern_label, conf: null }];
    }

    // 최종 변환된 배열로 state 설정
    setPatterns(patternsArray);

    // state 배열을 기준으로 단일 문자열 state도 업데이트
    setPatternLabel(patternsArray.length ? patternsArray.map((p) => p.label).join(", ") : "");
  };

  useEffect(() => {
    if (patterns.length > 0) {
      const details = patterns.map((p) => {
        const label = p.label;
        return strategyGuide[label] || { ...defaultStrategy, displayName: label };
      });
      setStrategyDetails(details);
    } else {
      setStrategyDetails([]);
    }
  }, [patterns]);

  // ================= 업로드 분석 =================
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedImage(file);
    setPreviewURL(URL.createObjectURL(file));
    // 이전 결과/메시지 초기화
    setResultImageURL("");
    setPatterns([]);
    setPatternLabel("");
    setStrategyDetails([]);
  };

  const handleUploadAnalysis = async () => {
    if (!selectedImage) return alert("이미지를 선택해주세요.");
    setLoading(true);
    setResultImageURL("");
    setPatterns([]);
    setPatternLabel("");
    setStrategyDetails([]);

    try {
      const csrfToken = getCSRFToken();
      const formData = new FormData();
      formData.append("image", selectedImage);

      const res = await fetch(`${backendURL}/chart/analysis/image/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        credentials: "include",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "서버 오류");

      const url = absolutizeAndBust(data.result_url || data.result);
      setResultImageURL("");
      setTimeout(() => setResultImageURL(url), 0);

      applyPatterns(data);
    } catch (err) {
      console.error(err);
      alert(err.message || "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // ================= 종목/기간 분석 =================
  const handleSymbolAnalysis = async () => {
    if (!symbol || !startDate || !endDate) {
      alert("종목, 시작일, 종료일을 모두 입력하세요.");
      return;
    }
    setLoading(true);
    setResultURL("");
    setPatterns([]);
    setPatternLabel("");
    setStrategyDetails([]);

    try {
      const csrfToken = getCSRFToken();
      const payload = {
        symbol,
        start_date: startDate,
        end_date: endDate,
        interval,
      };

      const res = await fetch(`${backendURL}/chart/by-symbol/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "서버 오류");

      const url = absolutizeAndBust(data.result_url);
      setResultURL("");
      setTimeout(() => setResultURL(url), 0);

      applyPatterns(data);
    } catch (err) {
      console.error(err);
      alert(err.message || "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // ================= UI =================
  return (
    <div className="p-6 space-y-8 text-white">
      {/* 이미지 업로드 분석 */}
      <section>
        <h2 className="text-xl font-semibold mb-2">이미지를 업로드하여 분석</h2>
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          className="text-white mb-2"
        />
        {previewURL && (
          <img
            src={previewURL}
            alt="미리보기"
            className="max-w-full h-auto border"
          />
        )}
      </section>

      <section>
        <button
          onClick={handleUploadAnalysis}
          className="px-4 py-2 bg-long text-newWhiteText rounded disabled:opacity-50"
          disabled={loading}
        >
          이미지 분석 요청
        </button>
        {loading && <p className="text-yellow-400 mt-2">분석 중입니다...</p>}
      </section>

      <section>
        {resultImageURL && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">분석 결과</h3>
            <img
              key={resultImageURL}
              src={resultImageURL}
              alt="분석 결과 이미지"
              className="max-w-full h-auto border"
            />
            <div className="mt-2">
              <p className="text-base text-green-400 mb-1">감지된 패턴:</p>
              {patterns.length > 0 ? (
                <ul className="list-disc pl-5">
                  {patterns.map((p, i) => (
                    <li key={`${p.label}-${i}`}>
                      {p.label}
                      {typeof p.conf === "number" && (
                        <> ({(p.conf * 100).toFixed(1)}%)</>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>
                  <span className="font-semibold">
                    {patternLabel || "없음"}
                  </span>
                </p>
              )}
            </div>

            {strategyDetails.length > 0 && (
              <div className="mt-6 p-4 bg-newBox rounded-lg space-y-4">
                <h4 className="text-lg font-semibold text-yellow-400">
                  📈 추천 매매 전략
                </h4>
                {strategyDetails.map((strategy, index) => (
                  <div
                    key={index}
                    className="pb-4 border-b border-gray-700 last:border-b-0"
                  >
                    <h5 className="text-md font-bold flex items-center">
                      {strategy.displayName}
                      {strategy.type !== "unknown" && (
                        <span
                          className={`ml-3 px-2 py-0.5 text-xs font-medium rounded-full ${
                            strategy.type === "bearish"
                              ? "bg-red-600 text-white"
                              : strategy.type === "bullish"
                              ? "bg-green-600 text-white"
                              : strategy.type === "complex"
                              ? "bg-yellow-400 text-black"
                              : ""
                          }`}
                        >
                          {strategy.type === "bearish"
                            ? "하락형"
                            : strategy.type === "bullish"
                            ? "상승형"
                            : strategy.type === "complex"
                            ? "복합형"
                            : ""}
                        </span>
                      )}
                    </h5>
                    <p className="text-sm text-gray-300 mt-2 whitespace-pre-line">
                      {strategy.description}
                    </p>
                    <p className="text-sm text-white mt-2 whitespace-pre-line">
                      <strong className="text-yellow-500">전략:</strong>{" "}
                      {strategy.strategy}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {/* 종목/기간 입력 UI */}
      <h2 className="text-xl font-semibold mb-2">기간을 지정하여 분석</h2>
      <div className="space-x-2">
        <input
          className="bg-newBox px-2 py-1 rounded"
          placeholder="종목 (예: AAPL, BTCUSDT)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />
        <input
          type="date"
          className="bg-newBox px-2 py-1 rounded"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
        />
        <input
          type="date"
          className="bg-newBox px-2 py-1 rounded"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
        />
        <select
          className="bg-newBox px-2 py-1 rounded"
          value={interval}
          onChange={(e) => setInterval(e.target.value)}
        >
          <option value="1d">1일봉</option>
          <option value="1h">1시간봉</option>
          <option value="15m">15분봉</option>
        </select>
        <button
          onClick={handleSymbolAnalysis}
          className="px-4 py-2 bg-long text-newWhiteText rounded"
          disabled={loading}
        >
          {loading ? "분석 중..." : "차트 생성 및 분석"}
        </button>
      </div>

      {/* 결과 표시(기간 분석) */}
      {resultURL && (
        <div className="mt-4">
          <p className="mb-2 text-green-400">감지된 패턴:</p>
          {patterns.length > 0 ? (
            <ul className="list-disc pl-5">
              {patterns.map((p, i) => (
                <li key={`bySymbol-${p.label}-${i}`}>
                  {p.label}
                  {typeof p.conf === "number" && (
                    <> ({(p.conf * 100).toFixed(1)}%)</>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p>
              <strong>{patternLabel || "없음"}</strong>
            </p>
          )}

          <img
            key={resultURL}
            src={resultURL}
            alt="분석 결과"
            className="w-full max-w-3xl border mt-2"
          />

          {strategyDetails.length > 0 && (
            <div className="mt-6 p-4 bg-newBox rounded-lg space-y-4">
              <h4 className="text-lg font-semibold text-yellow-400">
                📈 추천 매매 전략
              </h4>
              {strategyDetails.map((strategy, index) => (
                <div
                  key={`bySymbol-strategy-${index}`}
                  className="pb-4 border-b border-gray-700 last:border-b-0"
                >
                  <h5 className="text-md font-bold flex items-center">
                    {strategy.displayName}
                    {strategy.type !== "unknown" && (
                      <span
                        className={`ml-3 px-2 py-0.5 text-xs font-medium rounded-full ${
                          strategy.type === "bearish"
                            ? "bg-red-600 text-white"
                            : strategy.type === "bullish"
                            ? "bg-green-600 text-white"
                            : strategy.type === "complex"
                            ? "bg-yellow-400 text-black"
                            : ""
                        }`}
                      >
                        {strategy.type === "bearish"
                          ? "하락형"
                          : strategy.type === "bullish"
                          ? "상승형"
                          : strategy.type === "complex"
                          ? "복합형"
                          : ""}
                      </span>
                    )}
                  </h5>
                  <p className="text-sm text-gray-300 mt-2 whitespace-pre-line">
                    {strategy.description}
                  </p>
                  <p className="text-sm text-white mt-2 whitespace-pre-line">
                    <strong className="text-yellow-500">전략:</strong>{" "}
                    {strategy.strategy}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
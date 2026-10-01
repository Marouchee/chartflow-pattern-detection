import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar"; //

// 페이지 컴포넌트
import ChartAnalysisPage from "./pages/ChartAnalysisPage"; //
import MockInvestPage from "./pages/MockInvestPage"; //
import MyPage from "./pages/MyPage"; //
import LoginPage from "./pages/LoginPage"; //1105 추가
import RegisterPage from "./pages/RegisterPage"; //1105 추가

// 인증 관련
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext"; // AuthContext에서 훅 가져오기

export default function App() {
  // AuthContext에서 실제 로그인 상태를 가져옴. isLoggedIn state 삭제
  const { accessToken } = useAuth();

  return (
    <Router>
      <div className="dark min-h-screen bg-bottomBg text-white overflow-x-hidden">
        <Navbar
          // 실제 로그인 상태(accessToken) Navbar에 전달
          isLoggedIn={!!accessToken} // accessToken이 있으면 true 없으면 false
        />

        <div className="max-w-screen-xl mx-auto p-4">
          <Routes>
            {/* Route의 element에 페이지 컴포넌트를 직접 전달 */}

            {/* 기본/차트분석 페이지 (누구나 접근 가능) */}
            <Route path="/" element={<ChartAnalysisPage />} />
            <Route path="/chart/analysis" element={<ChartAnalysisPage />} />

            {/* 로그인 페이지 (누구나 접근 가능) */}
            <Route path="/login" element={<LoginPage />} />
            {/* <Route path="/register" element={<RegisterPage />} /> */}

            {/* --- 회원가입 라우트 추가 --- */}
            <Route path="/register" element={<RegisterPage />} />
            {/* ------------------------- */}

            {/* 모의투자 페이지 (로그인 필요) */}
            <Route
              path="/mockinvest/futures"
              element={
                <ProtectedRoute>
                  <MockInvestPage />
                </ProtectedRoute>
              }
            />

            {/* 통계(마이페이지) (로그인 필요) */}
            <Route
              path="/mypage"
              element={
                <ProtectedRoute>
                  <MyPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}
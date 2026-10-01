import React from "react";
import { useAuth } from "../context/AuthContext";
import { Navigate, useLocation } from "react-router-dom";

// 로그인이 필요한 페이지를 감싸는 컴포넌트
function ProtectedRoute({ children }) {
  const { accessToken } = useAuth();
  const location = useLocation();

  if (!accessToken) {
    // 로그인되지 않았다면 로그인 페이지로 리디렉션
    // (state: location)은 로그인 후 원래 가려던 페이지로 돌려보내기 위함
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children; // 로그인되었다면 자식 컴포넌트(페이지) 렌더링
}
export default ProtectedRoute;
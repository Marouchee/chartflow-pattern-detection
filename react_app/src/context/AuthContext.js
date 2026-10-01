// react_app/src/context/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from "react";
import { apiClient } from "../services/apiClient"; //

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // 유저 정보(선택)
  const [accessToken, setAccessToken] = useState(
    localStorage.getItem("access_token")
  );
  const [refreshToken, setRefreshToken] = useState(
    localStorage.getItem("refresh_token")
  );

  // 로그인 함수
  const login = async (username, password) => {
    try {
      // 백엔드의 사용자 계정 api '/api/accounts/token/' 호출
      const data = await apiClient.post("/api/accounts/token/", {
        username,
        password,
      });

      setAccessToken(data.access);
      setRefreshToken(data.refresh);
      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);

      return true;
    } catch (error) {
      console.error("Login failed:", error);
      logout(); // 실패 시 토큰 정리
      return false;
    }
  };

  // 로그아웃 함수
  const logout = () => {
    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  };

  const authContextValue = {
    user,
    accessToken,
    login,
    logout,
    // refreshToken 재발급 로직은 나중에 추가
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// 훅 생성
export const useAuth = () => {
  return useContext(AuthContext);
};
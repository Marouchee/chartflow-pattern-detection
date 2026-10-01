import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from '../context/AuthContext';

// 'isLoggedIn' prop을 App.js에서 전달받음
export default function Navbar({ isLoggedIn }) {
  // AuthContext에서 logout 함수 가져옴
  const { logout } = useAuth();
  const navigate = useNavigate();

  // 로그아웃 함수
  const handleLogout = () => {
    logout(); // Context, localStorage 토큰 제거
    navigate('/login'); // 로그아웃 후 로그인 페이지로 이동
  };

  return (
    <nav className="bg-newBgDark text-white px-6 py-3 flex justify-between items-center">
      {/* 왼쪽메뉴 시작 */}
      <div className="flex space-x-6">
        {/* 차트분석 탭 */}
        <div className="relative group">
          <button className="hover:text-yellow-400">차트분석</button>
          <div className="absolute hidden group-hover:block bg-newBox p-2 rounded shadow-lg z-10">
            <Link to="/chart/analysis" className="block px-4 py-2 hover:bg-gray-700 whitespace-nowrap">차트 분석</Link>
            <Link to="/chart/patterninform" className="block px-4 py-2 hover:bg-gray-700 whitespace-nowrap">패턴 정보</Link>
          </div>
        </div>

        {/* 모의투자 탭 */}
        <div className="relative group">
          <button className="hover:text-yellow-400">모의투자</button>
          <div className="absolute hidden group-hover:block bg-newBox p-2 rounded shadow-lg z-10">
            <Link to="/mockinvest/spot" className="block px-4 py-2 hover:bg-gray-700 whitespace-nowrap">현물</Link>
            <Link to="/mockinvest/futures" className="block px-4 py-2 hover:bg-gray-700 whitespace-nowrap">선물</Link>
            <Link to="/mockinvest/options" className="block px-4 py-2 hover:bg-gray-700 whitespace-nowrap">옵션</Link>
          </div>
        </div>
      </div>

      <Link to="/">Home</Link>

      {/* 오른쪽메뉴 시작 로그인/마이페이지 */}
      <div className="flex items-center space-x-4">
        {/* 별도의 마이페이지 버튼 (항상 보임) */}
        <Link to="/mypage" className="hover:text-yellow-400">마이페이지</Link>

        {/* 로그인 상태에 따라 '로그아웃' 또는 '로그인' 버튼 표시 */}
        {isLoggedIn ? (
          // 로그인 상태
          <button
            onClick={handleLogout}
            className="bg-red-500 hover:bg-red-600 text-white py-2 px-4 rounded"
          >
            로그아웃
          </button>
        ) : (
          // 로그인 안된상태
          <Link
            to="/login"
            className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded"
          >
            로그인
          </Link>
        )}
      </div>
    </nav>
  );
}
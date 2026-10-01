import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, useLocation, Link } from "react-router-dom"; // react-router-dom v6

function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation(); // useLocation 훅 사용

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const success = await login(username, password);
if (success) {
      // 로그인 후 리디렉션 로직 수정. ProtectedRoute에서 보낸 'from' state가 있으면 해당 위치로 없으면 /mypage
      const from = location.state?.from?.pathname || "/mypage";
      navigate(from, { replace: true });
    } else {
      setError("아이디 또는 비밀번호가 일치하지 않습니다.");
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-md">
      <h2 className="text-2xl font-bold mb-4 text-center">로그인</h2>
      {error && <p className="text-red-500 mb-4 text-center">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1 font-medium">아이디</label>
          <input
            type="text"
            className="w-full p-2 border rounded"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="block mb-1 font-medium">비밀번호</label>
          <input
            type="password"
            className="w-full p-2 border rounded"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        >
          로그인
        </button>
      </form>

      {/* 회원 가입!!! */}
      <div className="mt-4 text-center">
        <p>
          계정이 없으신가요?{" "}
          <Link to="/register" className="text-blue-400 hover:underline">
            회원가입하기
          </Link>
        </p>
      </div>
    </div>
  );
}
export default LoginPage;
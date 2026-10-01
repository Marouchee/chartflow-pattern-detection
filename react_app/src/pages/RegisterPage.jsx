import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/apiClient'; // apiClient 사용 (fetch 대신)

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  // 비밀번호 확인 state
  const [passwordConfirm, setPasswordConfirm] = useState('');

  const [error, setError] = useState(null);
  const { login } = useAuth(); // 회원가입 성공 시 자동 로그인
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (password !== passwordConfirm) {
        setError("비밀번호가 일치하지 않습니다.");
        return;
    }

    try {
      const data = await apiClient.post('/api/accounts/register/', {
        username,
        password,
        password_confirm: passwordConfirm 
      });
      // 회원가입 성공 시 자동 로그인 시도
      await login(username, password);
      navigate('/mypage'); // 마이페이지로 이동

    } catch (err) {
      console.error("회원가입 실패:", err);
      let errorMsg = '회원가입에 실패했습니다. (서버 오류)';
      if (err.response && err.response.data) {
          const data = err.response.data;
          if (data.username) {
            errorMsg = `아이디 오류: ${data.username[0]}`;
          } else if (data.password) {
            errorMsg = `비밀번호 오류: ${data.password[0]}`;
          } else if (data.password_confirm) {
            errorMsg = `비밀번호 확인 오류: ${data.password_confirm[0]}`;
          } else if (JSON.stringify(data).length < 100) {
            errorMsg = JSON.stringify(data);
          }
      }
      setError(errorMsg);
      // ---
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-layer">
      <div className="p-8 bg-newBox rounded-lg shadow-lg w-full max-w-sm">
        <h2 className="text-2xl font-bold text-center text-white mb-6">회원가입</h2>
        <form onSubmit={handleSubmit}>
          {/* 에러 메시지 표시 방식 변경 */}
          {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
          
          <div className="mb-4">
            <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="username">
              아이디
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="username" type="text" placeholder="Username"
              value={username} onChange={(e) => setUsername(e.target.value)} required
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="password">
              비밀번호
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              id="password" type="password" placeholder="******************"
              value={password} onChange={(e) => setPassword(e.target.value)} required
            />
          </div>

          {/* 비밀번호 확인 입력란  */}
          <div className="mb-6">
            <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="passwordConfirm">
              비밀번호 확인
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              id="passwordConfirm" type="password" placeholder="******************"
              value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)} required
            />
          </div>

          <div className="flex items-center justify-between">
            <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline" type="submit">
              회원가입
            </button>
            <Link to="/login" className="inline-block align-baseline font-bold text-sm text-blue-500 hover:text-blue-800">
              로그인
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
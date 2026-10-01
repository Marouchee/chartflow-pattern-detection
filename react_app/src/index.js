import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import MyPage from "./pages/MyPage";
import { AuthProvider } from "./context/AuthContext.js"; // 1105 추가

<BrowserRouter>
  <Routes>
    {/* ... */}
    <Route path="/my" element={<MyPage />} />
  </Routes>
</BrowserRouter>

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <AuthProvider> {/* 1105 추가 */}
      <App />
    </AuthProvider> {/* 1105 추가 */}
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();

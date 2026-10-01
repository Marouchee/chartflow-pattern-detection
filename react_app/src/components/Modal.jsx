import React from "react";

export default function Modal({ onClose, children }) {
  return (
    // 배경 오버레이
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
      <div className="bg-newBox text-white rounded-lg shadow-xl relative p-5">
        <button 
            onClick={onClose} 
            className="absolute top-3 right-4 text-gray-400 hover:text-white text-2xl font-bold z-10"
        >
            ×
        </button>
        {/* 자식 컴포넌트가 들어갈 위치 */}
        {children}
      </div>
    </div>
  );
}
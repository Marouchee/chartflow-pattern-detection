/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',                  // 다크모드 활성화
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        newBgDark: "#151515",         // 전체 배경색 - 트레이딩뷰 dark모드 배경색색
        newWhite: "#ffffff",          // 전체 배경색 - 트레이딩뷰 light모드 배경색
        bottomBg: "#000000",          // 최하단 배경색 - 트레이딩뷰 기준 최하단 배경색과 통일
        newBox: "#1a1a1a",            // 박스 배경색 - 수량,주문가격 박스
        newLine: "#404040",           // 밑줄색
        newWhiteText: "#fbfbfb",      // 흰 글자색
        newGrayText: "#a0a0a0",       // 회색 글자색
        layer: "#0f0f0f",             // 트레이드패널 / 트레이드테이블 배경색
        long: "#089981",              // 매수 버튼, 수익 색
        short: "#f23645",             // 매도 버튼, 손실 색
      },
    },
  },
  plugins: [],
};
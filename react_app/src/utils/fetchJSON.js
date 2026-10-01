export async function fetchJSON(url, options = {}) {
  // 헤더 객체 준비 단계
  // options에 headers가 없을 수도 있으니 기본값 {}을 부여
  // 기존 options.headers의 내용 보존
  const headers = {
    "Content-Type": "application/json", // JSON 요청을 기본으로 가정
    ...options.headers,
  };

  // JWT 토큰 가져오기
  const accessToken = localStorage.getItem("access_token");

  // 토큰이 있으면 헤더에 추가한다
  if (accessToken) {
    // 'Bearer' 스키마를 포함하여 헤더 추가 (API 명세)
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  // 수정된 헤더와 함께 fetch 호출
  // 기존 options를 복사, headers 덮어쓰기, credentials 유지.
  const res = await fetch(url, {
    credentials: "include", // 기존 로직 유지
    ...options, // 기존 options (method, body 등) 유지
    headers: headers, // 새 헤더 객체
  });

  const ct = res.headers.get("content-type") || "";

  if (!res.ok) {
    // 에러 응답은 텍스트로 받아서 메시지에 일부 포함
    const text = await res.text().catch(() => "");
    throw new Error(
      `HTTP ${res.status} ${res.statusText} (${url})\n` +
        `${ct ? `CT=${ct}\n` : ""}` +
        `${text.slice(0, 200)}`
    );
  }

  // 빈 응답 204 No Content 처리
  if (res.status === 204 || ct.length === 0) {
    return null; 
  }

  if (ct.includes("application/json")) {
    return res.json();
  }

  // JSON이 아닌 응답 그대로 텍스트 반환
  const text = await res.text();
  // 상황에 따라 throw 또는 텍스트 처리
  throw new Error(
    `Expected JSON but got '${ct}' from ${url}\n` + text.slice(0, 200)
  );
}
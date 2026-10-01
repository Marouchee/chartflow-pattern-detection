/**
 * 브라우저 쿠키에서 'csrftoken'의 값을 파싱해서 반환
 */
export function getCSRFToken() {
  const name = "csrftoken";
  const decodedCookie = decodeURIComponent(document.cookie);
  const cookieArr = decodedCookie.split(";");
  for (let i = 0; i < cookieArr.length; i++) {
    let c = cookieArr[i].trim();
    if (c.startsWith(name + "=")) {
      return c.substring(name.length + 1);
    }
  }
  return null;
}
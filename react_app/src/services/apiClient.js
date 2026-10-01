import { fetchJSON } from "../utils/fetchJSON";

// apiClient 객체 정의
const apiClient = {
  get: (url) => fetchJSON(url),
  
  post: (url, data) => fetchJSON(url, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};

export { apiClient };
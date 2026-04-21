import axios from "axios";
import toast from "react-hot-toast";

const client = axios.create({
  baseURL: import.meta.env.VITE_ADMIN_API_BASE_URL,
  timeout: 10000,
});

function extractApiErrorMessage(err) {
  const data = err?.response?.data;
  const directMessage = data?.error?.message;
  if (directMessage && directMessage !== "Upstream service returned an error.") {
    return directMessage;
  }
  const upstreamDetail = data?.error?.details?.upstream_response?.detail;
  if (typeof upstreamDetail === "string" && upstreamDetail.trim()) {
    return upstreamDetail;
  }
  const upstreamMessage = data?.error?.details?.upstream_response?.error?.message;
  if (typeof upstreamMessage === "string" && upstreamMessage.trim()) {
    return upstreamMessage;
  }
  return null;
}

function isAuthFailure(status, message) {
  if (status === 401) return true;
  if (status !== 403 || !message) return false;
  const lower = message.toLowerCase();
  return (
    lower.includes("access token") ||
    lower.includes("authentication credentials") ||
    lower.includes("token has expired") ||
    lower.includes("token is invalid")
  );
}

client.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const adminId = localStorage.getItem("admin_user_id");
  const method = (config.method || "get").toLowerCase();
  const url = (config.url || "").toLowerCase();
  const isAuthEndpoint =
    url.includes("/auth/login") || url.includes("/auth/register") || url.includes("/auth/refresh");
  if (adminId && method !== "get" && !isAuthEndpoint) {
    config.headers["X-Admin-ID"] = adminId;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    const message = extractApiErrorMessage(err);

    if (isAuthFailure(status, message)) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("admin_role");
      localStorage.removeItem("admin_user_id");
      window.location.href = "/admin/login";
      return Promise.reject(err);
    }

    if (message) {
      toast.error(message);
    } else {
      const requestId = err.response?.data?.request_id;
      if (requestId) {
        toast.error(`Error ID: ${requestId} - Contact engineering`);
      }
    }
    return Promise.reject(err);
  }
);

export default client;

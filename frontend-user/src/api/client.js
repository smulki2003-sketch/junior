import axios from "axios";
import toast from "react-hot-toast";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
});

export function extractApiErrorMessage(err) {
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
  if (upstreamMessage) {
    return upstreamMessage;
  }

  const fallbackMessage = data?.error?.details?.upstream_response?.message;
  if (fallbackMessage) {
    return fallbackMessage;
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
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.code === "ECONNABORTED") {
      toast.error("The request is taking longer than expected. Please wait and check your bookings before retrying.");
      return Promise.reject(err);
    }

    const status = err.response?.status;
    const message = extractApiErrorMessage(err);

    if (isAuthFailure(status, message)) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
      return Promise.reject(err);
    }

    if (message) {
      toast.error(message);
    } else {
      const requestId = err.response?.data?.request_id;
      if (requestId) {
        toast.error(`Request failed. Error ID: ${requestId}`);
      }
    }
    return Promise.reject(err);
  }
);

export default client;

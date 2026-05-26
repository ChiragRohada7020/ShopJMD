export const formatCurrency = (value = 0) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));

export const formatDate = (value) => {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
};

export const today = () => new Date().toISOString().slice(0, 10);

export const getErrorMessage = (error) => {
  if (error?.message === "Network Error") {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";
    return `Backend not reachable at ${apiUrl}. Check backend deploy, CORS, and VITE_API_URL.`;
  }
  if (error?.code === "ECONNABORTED") {
    return "Request timed out. Check that Flask and MongoDB are running.";
  }
  const data = error?.response?.data;
  if (data?.error) return data.error;
  if (data?.errors) return Object.values(data.errors).join(", ");
  return error?.message || "Request failed";
};

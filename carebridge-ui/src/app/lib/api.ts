import axios from "axios";
import { PrePurchaseReport } from "../types/prepurchase";
import { AuditReport } from "../types/audit";

// ✅ env-driven — set NEXT_PUBLIC_API_URL in .env.local for dev,
//    and in Vercel/deployment env vars for production/Kaggle ngrok URL
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 360_000,   // 6 min — covers MedGemma generation time on T4
});

// --------------------------------------------------
// Post-Rejection Audit
// --------------------------------------------------
export const analyzeRejection = async (payload: {
  policy_text:             string;
  rejection_text:          string;
  medical_documents_text?: string;
  user_explanation?:       string;
}): Promise<AuditReport> => {
  const response = await API.post("/audit", payload);
  return response.data;
};

// --------------------------------------------------
// Pre-Purchase Analysis — text input
// --------------------------------------------------
export const analyzePolicy = async (
  policyText: string,
  providerId?: string
): Promise<PrePurchaseReport> => {
  const payload: any = { policy_text: policyText };
  if (providerId) {
      payload.provider_id = providerId;
  }
  const response = await API.post("/prepurchase", payload);
  return response.data;
};

// --------------------------------------------------
// Pre-Purchase Analysis — file upload
// Sends actual file as multipart/form-data to /prepurchase/upload
// --------------------------------------------------
export const analyzePolicyFromFile = async (
  file: File
): Promise<PrePurchaseReport> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await API.post("/prepurchase/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};


// --------------------------------------------------
// Policy Comparison
// --------------------------------------------------
export const comparePolicies = async (
  policyA: string,
  policyB: string
) => {
  const response = await API.post("/compare", {
    policy_a_text: policyA,
    policy_b_text: policyB,
  });
  return response.data;
};
console.log("API:", BASE_URL);

export default API;
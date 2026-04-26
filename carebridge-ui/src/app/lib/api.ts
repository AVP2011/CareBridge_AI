import axios from "axios";
import { PrePurchaseReport } from "../types/prepurchase";
import { AuditReport } from "../types/audit";

// ✅ env-driven — set NEXT_PUBLIC_API_URL in .env.local for dev,
//    and in Vercel/deployment env vars for production/Kaggle ngrok URL
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://uninvidious-lyla-capitally.ngrok-free.dev";

const API = axios.create({
  baseURL: BASE_URL,
  headers: { 
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
  },
  timeout: 360_000,   // 6 min — covers MedGemma generation time on T4
});

// --------------------------------------------------
// Post-Rejection Audit
// --------------------------------------------------
export const analyzeRejection = async (payload: {
  policy_text: string;
  rejection_text: string;
  medical_documents_text?: string;
  user_explanation?: string;
}): Promise<AuditReport> => {
  const response = await API.post("/audit", payload);
  return response.data;
};

// --------------------------------------------------
// Pre-Purchase Analysis — text input
// --------------------------------------------------
export const analyzePolicy = async (
  policyText: string,
  providerId?: string,
  agentSummary?: string,
): Promise<PrePurchaseReport> => {
  const payload: any = { policy_text: policyText };
  if (providerId) payload.provider_id = providerId;
  if (agentSummary) payload.agent_summary = agentSummary;

  const response = await API.post("/prepurchase", payload);
  return response.data;
};

// --------------------------------------------------
// Pre-Purchase Analysis — file upload
// --------------------------------------------------
export const analyzePolicyFromFile = async (
  file: File,
  agentSummary?: string,
): Promise<PrePurchaseReport> => {
  const formData = new FormData();
  formData.append("file", file);
  if (agentSummary) formData.append("agent_summary", agentSummary);

  const response = await axios.post(`${BASE_URL}/prepurchase/upload`, formData, {
    headers: {
      "ngrok-skip-browser-warning": "true"
    },
    timeout: 360_000,
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
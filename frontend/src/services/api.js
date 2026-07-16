import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  // HCP Endpoints
  getHcps: async () => {
    const res = await apiClient.get("/api/hcps");
    return res.data;
  },
  
  createHcp: async (hcpData) => {
    const res = await apiClient.post("/api/hcps", hcpData);
    return res.data;
  },

  // Interaction Endpoints
  getInteractions: async () => {
    const res = await apiClient.get("/api/interactions");
    return res.data;
  },

  getInteraction: async (id) => {
    const res = await apiClient.get(`/api/interactions/${id}`);
    return res.data;
  },

  createInteraction: async (data) => {
    const res = await apiClient.post("/api/interactions", data);
    return res.data;
  },

  updateInteraction: async (id, data) => {
    const res = await apiClient.patch(`/api/interactions/${id}`, data);
    return res.data;
  },

  getHcpHistory: async (hcpId) => {
    const res = await apiClient.get(`/api/hcps/${hcpId}/interaction-history`);
    return res.data;
  },

  // Agent Endpoints
  sendAgentChat: async (message, history = [], currentState = {}) => {
    const res = await apiClient.post("/api/agent/chat", {
      message,
      history,
      current_state: currentState,
    });
    return res.data;
  },

  extractInteractionText: async (text) => {
    const res = await apiClient.post("/api/agent/extract", { text });
    return res.data;
  },

  getFollowUpSuggestions: async (interactionId = null, payload = null) => {
    const body = interactionId ? { interaction_id: interactionId } : payload;
    const res = await apiClient.post("/api/agent/follow-up-suggestions", body);
    return res.data;
  },
};

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../services/api";

export const sendChatMessage = createAsyncThunk(
  "agent/sendChatMessage",
  async ({ message, history, currentState }, { rejectWithValue }) => {
    try {
      // Map history to the basic format the backend expects
      const formattedHistory = history.map((msg) => ({
        role: msg.sender === "user" ? "user" : "assistant",
        content: msg.text,
      }));
      return await api.sendAgentChat(message, formattedHistory, currentState);
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to send message to agent");
    }
  }
);

const agentSlice = createSlice({
  name: "agent",
  initialState: {
    messages: [
      {
        id: "welcome",
        sender: "agent",
        text: "Hello! I am your AI CRM Assistant. You can describe your doctor interaction here, e.g.:\n\n'Met Dr. Priya Sharma today at Cardiology clinic. We discussed Product X Efficacy. She showed positive sentiment and requested slides.'\n\nI will extract the fields and sync them to your structured form.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ],
    extractedData: {},
    confidence: {},
    missingFields: [],
    requiresConfirmation: false,
    currentState: {
      tool_name: null,
      tool_inputs: null,
      requires_confirmation: false,
      confirmation_status: null,
      extracted_data: {},
    },
    loading: false,
    error: null,
  },
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    confirmExtractedData: (state) => {
      // Rep approves DB write
      state.currentState.confirmation_status = "approved";
      state.requiresConfirmation = false;
    },
    rejectExtractedData: (state) => {
      // Rep rejects DB write
      state.currentState.confirmation_status = "rejected";
      state.requiresConfirmation = false;
      state.extractedData = {};
    },
    resetAgent: (state) => {
      state.messages = [
        {
          id: "welcome",
          sender: "agent",
          text: "Hello! I am your AI CRM Assistant. Describe your meeting and I will help you log it.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ];
      state.extractedData = {};
      state.confidence = {};
      state.missingFields = [];
      state.requiresConfirmation = false;
      state.currentState = {
        tool_name: null,
        tool_inputs: null,
        requires_confirmation: false,
        confirmation_status: null,
        extracted_data: {},
      };
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.loading = false;
        const res = action.payload;
        
        // Add agent reply message
        state.messages.push({
          id: `msg-${Date.now()}`,
          sender: "agent",
          text: res.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        });

        // Sync agent's internal state tracking
        state.extractedData = res.extracted_data || {};
        state.confidence = res.confidence || {};
        state.missingFields = res.missing_fields || [];
        
        // Check if backend requires confirmation
        const reqConfirm = res.status === "requires_confirmation";
        state.requiresConfirmation = reqConfirm;

        // Keep current state copy updated
        state.currentState = {
          extracted_data: res.extracted_data || {},
          tool_name: reqConfirm ? "log_interaction_tool" : null,
          tool_inputs: res.extracted_data || {},
          requires_confirmation: reqConfirm,
          confirmation_status: null, // resets confirmation status for next message
        };
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.messages.push({
          id: `msg-err-${Date.now()}`,
          sender: "agent",
          text: `Error: ${action.payload}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          isError: true,
        });
      });
  },
});

export const { addMessage, confirmExtractedData, rejectExtractedData, resetAgent } = agentSlice.actions;
export default agentSlice.reducer;

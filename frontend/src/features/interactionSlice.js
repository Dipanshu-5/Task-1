import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../services/api";

const initialFormData = {
  hcp_id: "",
  interaction_type: "In-Person",
  interaction_date: new Date().toISOString().split("T")[0],
  interaction_time: "",
  attendees: [],
  topics_discussed: [],
  materials_shared: [],
  samples_distributed: [],
  sentiment: "Neutral",
  outcomes: "",
  follow_up_actions: "",
  follow_up_date: "",
  original_notes: "",
  ai_summary: "",
  consent_voice: false,
};

export const saveInteraction = createAsyncThunk(
  "interaction/saveInteraction",
  async (formData, { rejectWithValue }) => {
    try {
      const payload = { ...formData };
      delete payload.consent_voice; // strip UI-only indicator if not modeled directly
      return await api.createInteraction(payload);
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to save interaction");
    }
  }
);

export const updateInteractionThunk = createAsyncThunk(
  "interaction/updateInteraction",
  async ({ id, updates }, { rejectWithValue }) => {
    try {
      return await api.updateInteraction(id, updates);
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to update interaction");
    }
  }
);

export const fetchHcpHistory = createAsyncThunk(
  "interaction/fetchHcpHistory",
  async (hcpId, { rejectWithValue }) => {
    try {
      return await api.getHcpHistory(hcpId);
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to fetch HCP history");
    }
  }
);

export const fetchAllInteractions = createAsyncThunk(
  "interaction/fetchAllInteractions",
  async (_, { rejectWithValue }) => {
    try {
      return await api.getInteractions();
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to load interactions");
    }
  }
);

const interactionSlice = createSlice({
  name: "interaction",
  initialState: {
    formData: { ...initialFormData },
    history: [], // selected HCP's timeline
    allInteractions: [], // all logged items for quick overview
    activeInteractionId: null, // if editing an existing interaction
    loading: false,
    saveLoading: false,
    historyLoading: false,
    error: null,
    saveSuccess: false,
  },
  reducers: {
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      state.formData[field] = value;
    },
    resetForm: (state) => {
      state.formData = { ...initialFormData };
      state.activeInteractionId = null;
      state.saveSuccess = false;
      state.error = null;
    },
    setEditMode: (state, action) => {
      const interaction = action.payload;
      state.activeInteractionId = interaction.id;
      
      // Parse JSON columns if they come as string arrays/dicts from API
      const parseField = (val) => {
        if (!val) return [];
        if (typeof val === "string") {
          try { return JSON.parse(val); } catch { return [val]; }
        }
        return val;
      };

      state.formData = {
        hcp_id: interaction.hcp_id,
        interaction_type: interaction.interaction_type,
        interaction_date: interaction.interaction_date,
        interaction_time: interaction.interaction_time || "",
        attendees: parseField(interaction.attendees),
        topics_discussed: parseField(interaction.topics_discussed),
        materials_shared: parseField(interaction.materials_shared),
        samples_distributed: parseField(interaction.samples_distributed),
        sentiment: interaction.sentiment || "Neutral",
        outcomes: interaction.outcomes || "",
        follow_up_actions: interaction.follow_up_actions || "",
        follow_up_date: interaction.follow_up_date || "",
        original_notes: interaction.original_notes || "",
        ai_summary: interaction.ai_summary || "",
        consent_voice: false,
      };
    },
    syncExtractedData: (state, action) => {
      const data = action.payload;
      
      // Map chat-extracted fields back to structured Redux form state
      if (data.interaction_type) state.formData.interaction_type = data.interaction_type;
      if (data.interaction_date) state.formData.interaction_date = data.interaction_date;
      if (data.interaction_time) state.formData.interaction_time = data.interaction_time;
      if (data.attendees) state.formData.attendees = data.attendees;
      if (data.topics_discussed) state.formData.topics_discussed = data.topics_discussed;
      if (data.materials_shared) state.formData.materials_shared = data.materials_shared;
      if (data.samples_distributed) state.formData.samples_distributed = data.samples_distributed;
      if (data.sentiment) state.formData.sentiment = data.sentiment;
      if (data.outcomes) state.formData.outcomes = data.outcomes;
      if (data.follow_up_actions) state.formData.follow_up_actions = data.follow_up_actions;
      if (data.follow_up_date) state.formData.follow_up_date = data.follow_up_date;
      if (data.ai_summary) state.formData.ai_summary = data.ai_summary;
      if (data.hcp_id) state.formData.hcp_id = data.hcp_id;
    },
    clearSaveSuccess: (state) => {
      state.saveSuccess = false;
    }
  },
  extraReducers: (builder) => {
    builder
      // Save Interaction
      .addCase(saveInteraction.pending, (state) => {
        state.saveLoading = true;
        state.error = null;
        state.saveSuccess = false;
      })
      .addCase(saveInteraction.fulfilled, (state, action) => {
        state.saveLoading = false;
        state.saveSuccess = true;
        state.allInteractions.unshift(action.payload);
        state.formData = { ...initialFormData };
        state.activeInteractionId = null;
      })
      .addCase(saveInteraction.rejected, (state, action) => {
        state.saveLoading = false;
        state.error = action.payload;
      })
      // Update Interaction
      .addCase(updateInteractionThunk.pending, (state) => {
        state.saveLoading = true;
        state.error = null;
        state.saveSuccess = false;
      })
      .addCase(updateInteractionThunk.fulfilled, (state, action) => {
        state.saveLoading = false;
        state.saveSuccess = true;
        const idx = state.allInteractions.findIndex((x) => x.id === action.payload.id);
        if (idx !== -1) {
          state.allInteractions[idx] = action.payload;
        }
        state.formData = { ...initialFormData };
        state.activeInteractionId = null;
      })
      .addCase(updateInteractionThunk.rejected, (state, action) => {
        state.saveLoading = false;
        state.error = action.payload;
      })
      // Fetch HCP History
      .addCase(fetchHcpHistory.pending, (state) => {
        state.historyLoading = true;
        state.error = null;
      })
      .addCase(fetchHcpHistory.fulfilled, (state, action) => {
        state.historyLoading = false;
        state.history = action.payload;
      })
      .addCase(fetchHcpHistory.rejected, (state, action) => {
        state.historyLoading = false;
        state.error = action.payload;
      })
      // Fetch All
      .addCase(fetchAllInteractions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAllInteractions.fulfilled, (state, action) => {
        state.loading = false;
        state.allInteractions = action.payload;
      })
      .addCase(fetchAllInteractions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { updateFormField, resetForm, setEditMode, syncExtractedData, clearSaveSuccess } =
  interactionSlice.actions;
export default interactionSlice.reducer;

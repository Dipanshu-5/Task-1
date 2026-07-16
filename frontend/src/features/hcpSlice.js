import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../services/api";

export const fetchHcps = createAsyncThunk("hcp/fetchHcps", async (_, { rejectWithValue }) => {
  try {
    return await api.getHcps();
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to load HCPs");
  }
});

const hcpSlice = createSlice({
  name: "hcp",
  initialState: {
    list: [],
    selectedHcpId: "",
    loading: false,
    error: null,
  },
  reducers: {
    setSelectedHcpId: (state, action) => {
      state.selectedHcpId = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
        if (action.payload.length > 0 && !state.selectedHcpId) {
          state.selectedHcpId = action.payload[0].id;
        }
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setSelectedHcpId } = hcpSlice.actions;
export default hcpSlice.reducer;

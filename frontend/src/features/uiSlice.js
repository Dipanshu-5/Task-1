import { createSlice } from "@reduxjs/toolkit";

const uiSlice = createSlice({
  name: "ui",
  initialState: {
    toast: null, // { message, type: 'success' | 'error' }
    theme: "light",
  },
  reducers: {
    showToast: (state, action) => {
      state.toast = action.payload;
    },
    clearToast: (state) => {
      state.toast = null;
    },
    toggleTheme: (state) => {
      state.theme = state.theme === "light" ? "dark" : "light";
    },
  },
});

export const { showToast, clearToast, toggleTheme } = uiSlice.actions;
export default uiSlice.reducer;

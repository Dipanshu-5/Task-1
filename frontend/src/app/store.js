import { configureStore } from "@reduxjs/toolkit";
import hcpReducer from "../features/hcpSlice";
import interactionReducer from "../features/interactionSlice";
import agentReducer from "../features/agentSlice";
import uiReducer from "../features/uiSlice";

export const store = configureStore({
  reducer: {
    hcp: hcpReducer,
    interaction: interactionReducer,
    agent: agentReducer,
    ui: uiReducer,
  },
});

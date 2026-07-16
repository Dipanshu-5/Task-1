import { describe, it, expect } from "vitest";
import hcpReducer, { setSelectedHcpId } from "./hcpSlice";
import uiReducer, { showToast, clearToast } from "./uiSlice";
import agentReducer, { confirmExtractedData, rejectExtractedData, resetAgent } from "./agentSlice";
import interactionReducer, {
  updateFormField,
  resetForm,
  syncExtractedData,
  setEditMode
} from "./interactionSlice";

describe("Redux Slice Unit Tests", () => {
  
  // 1. HCP Slice
  it("should handle initial state and setSelectedHcpId", () => {
    const initialState = { list: [], selectedHcpId: "", loading: false, error: null };
    const nextState = hcpReducer(initialState, setSelectedHcpId("123"));
    expect(nextState.selectedHcpId).toBe("123");
  });

  // 2. UI Slice
  it("should handle toast notifications", () => {
    const initialState = { toast: null, theme: "light" };
    const nextState = uiReducer(initialState, showToast({ message: "Success!", type: "success" }));
    expect(nextState.toast).toEqual({ message: "Success!", type: "success" });

    const clearedState = uiReducer(nextState, clearToast());
    expect(clearedState.toast).toBeNull();
  });

  // 3. Interaction Slice: Form Field Updates & Reset
  it("should update form fields and reset form state", () => {
    const initialState = {
      formData: { hcp_id: "", interaction_type: "In-Person", topics_discussed: [] },
      activeInteractionId: null
    };

    // Update field
    let nextState = interactionReducer(initialState, updateFormField({ field: "hcp_id", value: "1" }));
    expect(nextState.formData.hcp_id).toBe("1");

    // Update topics
    nextState = interactionReducer(nextState, updateFormField({ field: "topics_discussed", value: ["Product Efficacy"] }));
    expect(nextState.formData.topics_discussed).toEqual(["Product Efficacy"]);

    // Reset form
    const resetState = interactionReducer(nextState, resetForm());
    expect(resetState.formData.hcp_id).toBe("");
    expect(resetState.formData.topics_discussed).toEqual([]);
  });

  // 4. Form Synchronization with AI Extracted Data
  it("should synchronize AI extracted fields into form state", () => {
    const initialState = {
      formData: {
        hcp_id: "",
        interaction_type: "In-Person",
        topics_discussed: [],
        sentiment: "Neutral",
        ai_summary: ""
      }
    };

    const extracted = {
      hcp_id: 2,
      interaction_type: "Virtual",
      topics_discussed: ["Product Efficacy", "Safety Profile"],
      sentiment: "Positive",
      ai_summary: "Rep met Dr Priya"
    };

    const nextState = interactionReducer(initialState, syncExtractedData(extracted));
    expect(nextState.formData.hcp_id).toBe(2);
    expect(nextState.formData.interaction_type).toBe("Virtual");
    expect(nextState.formData.topics_discussed).toEqual(["Product Efficacy", "Safety Profile"]);
    expect(nextState.formData.sentiment).toBe("Positive");
    expect(nextState.formData.ai_summary).toBe("Rep met Dr Priya");
  });

  // 5. Agent Slice: Confirmation state updates
  it("should update agent confirmation status", () => {
    const initialState = {
      requiresConfirmation: true,
      extractedData: { hcp_id: 1 },
      currentState: { confirmation_status: null }
    };

    // Confirm
    const confirmedState = agentReducer(initialState, confirmExtractedData());
    expect(confirmedState.requiresConfirmation).toBe(false);
    expect(confirmedState.currentState.confirmation_status).toBe("approved");

    // Reject
    const rejectedState = agentReducer(initialState, rejectExtractedData());
    expect(rejectedState.requiresConfirmation).toBe(false);
    expect(rejectedState.currentState.confirmation_status).toBe("rejected");
    expect(rejectedState.extractedData).toEqual({});
  });

  // 6. Set Edit Mode mapping
  it("should load existing interaction into edit mode and parse fields", () => {
    const initialState = {
      formData: {},
      activeInteractionId: null
    };

    const mockInteraction = {
      id: 5,
      hcp_id: 1,
      interaction_type: "Phone",
      topics_discussed: '["Clinical Trial Data"]', // JSON string from DB
      sentiment: "Neutral"
    };

    const nextState = interactionReducer(initialState, setEditMode(mockInteraction));
    expect(nextState.activeInteractionId).toBe(5);
    expect(nextState.formData.hcp_id).toBe(1);
    expect(nextState.formData.interaction_type).toBe("Phone");
    expect(nextState.formData.topics_discussed).toEqual(["Clinical Trial Data"]); // parsed back to array
  });
});

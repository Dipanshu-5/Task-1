import React, { useEffect, useState, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchHcps, setSelectedHcpId } from "../features/hcpSlice";
import {
  saveInteraction,
  updateInteractionThunk,
  fetchHcpHistory,
  updateFormField,
  resetForm,
  setEditMode,
  syncExtractedData,
  clearSaveSuccess
} from "../features/interactionSlice";
import {
  sendChatMessage,
  confirmExtractedData,
  rejectExtractedData,
  resetAgent,
  addMessage
} from "../features/agentSlice";
import { showToast, clearToast } from "../features/uiSlice";
import { HcpSelector, SentimentSelector, MaterialSelector, SampleSelector } from "../components/FormFields";
import ChatMessage from "../components/ChatMessage";
import ExtractedInteractionPreview from "../components/ExtractedInteractionPreview";
import ConfirmationPanel from "../components/ConfirmationPanel";
import { Sparkles, Calendar, Clock, Users, BookOpen, Send, RefreshCw, XCircle, Trash2, History } from "lucide-react";

const LogInteractionPage = () => {
  const dispatch = useDispatch();
  const hcpState = useSelector((state) => state.hcp);
  const interactionState = useSelector((state) => state.interaction);
  const agentState = useSelector((state) => state.agent);
  const uiState = useSelector((state) => state.ui);

  const { formData, history, activeInteractionId, saveLoading, saveSuccess, error: interactionError } = interactionState;
  const { messages, extractedData, requiresConfirmation, loading: agentLoading, error: agentError, currentState } = agentState;

  const [chatInput, setChatInput] = useState("");
  const [attendeeInput, setAttendeeInput] = useState("");
  const [formErrors, setFormErrors] = useState({});
  const chatEndRef = useRef(null);

  useEffect(() => {
    dispatch(fetchHcps());
  }, [dispatch]);

  // Load history when selected HCP changes
  useEffect(() => {
    if (formData.hcp_id) {
      dispatch(fetchHcpHistory(formData.hcp_id));
      dispatch(setSelectedHcpId(formData.hcp_id));
    }
  }, [formData.hcp_id, dispatch]);

  // Auto-scroll chat window
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, agentLoading]);

  // Handle Save success toast
  useEffect(() => {
    if (saveSuccess) {
      dispatch(showToast({ message: activeInteractionId ? "Interaction updated successfully!" : "Interaction logged successfully!", type: "success" }));
      dispatch(resetForm());
      dispatch(resetAgent());
      if (formData.hcp_id) {
        dispatch(fetchHcpHistory(formData.hcp_id));
      }
      setTimeout(() => {
        dispatch(clearSaveSuccess());
      }, 3000);
    }
  }, [saveSuccess, activeInteractionId, dispatch]);

  // Sync agent-extracted fields into structured form on approval
  const handleApproveExtract = async () => {
    dispatch(confirmExtractedData());
    
    // Sync to Redux Form
    dispatch(syncExtractedData(extractedData));
    
    // Prepare final payload for API save
    const payload = {
      ...formData,
      ...extractedData,
      status: "Submitted"
    };

    if (activeInteractionId) {
      dispatch(updateInteractionThunk({ id: activeInteractionId, updates: payload }));
    } else {
      dispatch(saveInteraction(payload));
    }
  };

  const handleRejectExtract = () => {
    dispatch(rejectExtractedData());
    dispatch(showToast({ message: "AI extraction discarded.", type: "error" }));
  };

  // Structured Form validations
  const validateForm = () => {
    const errors = {};
    if (!formData.hcp_id) errors.hcp_id = "HCP is required.";
    if (!formData.interaction_date) errors.interaction_date = "Date is required.";
    if (formData.topics_discussed.length === 0) errors.topics_discussed = "At least one topic must be selected.";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Save via Structured Form
  const handleSaveForm = (e) => {
    e.preventDefault();
    if (!validateForm()) {
      dispatch(showToast({ message: "Please resolve form validation errors.", type: "error" }));
      return;
    }

    const payload = {
      ...formData,
      status: "Submitted"
    };

    if (activeInteractionId) {
      dispatch(updateInteractionThunk({ id: activeInteractionId, updates: payload }));
    } else {
      dispatch(saveInteraction(payload));
    }
  };

  const handleResetForm = () => {
    dispatch(resetForm());
    setFormErrors({});
    dispatch(showToast({ message: "Form has been reset.", type: "neutral" }));
  };

  const handleChatSend = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = chatInput.trim();
    setChatInput("");

    // Add user message to UI
    dispatch(addMessage({
      id: `msg-${Date.now()}`,
      sender: "user",
      text: userMsg,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }));

    // Call LangGraph endpoint
    dispatch(sendChatMessage({
      message: userMsg,
      history: messages,
      currentState: currentState
    }));
  };

  // Chip input for attendees
  const handleAddAttendee = (e) => {
    if (e.key === "Enter" && attendeeInput.trim()) {
      e.preventDefault();
      if (!formData.attendees.includes(attendeeInput.trim())) {
        dispatch(updateFormField({
          field: "attendees",
          value: [...formData.attendees, attendeeInput.trim()]
        }));
      }
      setAttendeeInput("");
    }
  };

  const handleRemoveAttendee = (attendee) => {
    dispatch(updateFormField({
      field: "attendees",
      value: formData.attendees.filter(x => x !== attendee)
    }));
  };

  // Topic checkboxes
  const handleTopicToggle = (topic) => {
    const current = formData.topics_discussed;
    const next = current.includes(topic)
      ? current.filter(x => x !== topic)
      : [...current, topic];
    dispatch(updateFormField({ field: "topics_discussed", value: next }));
  };

  // Quick suggestions buttons for AI assistant
  const handleSuggestionClick = (prompt) => {
    setChatInput(prompt);
  };

  return (
    <div className="log-interaction-container">
      {/* Toast alert */}
      {uiState.toast && (
        <div className={`toast-alert ${uiState.toast.type}`}>
          <div className="toast-content">{uiState.toast.message}</div>
          <button className="toast-close" onClick={() => dispatch(clearToast())}>✕</button>
        </div>
      )}

      {/* Main Grid: Split Layout */}
      <div className="crm-main-grid">
        
        {/* LEFT COLUMN: Structured Form */}
        <section className="form-column-card">
          <div className="card-header">
            <h3>{activeInteractionId ? `Edit Interaction (ID: ${activeInteractionId})` : "Log New Interaction"}</h3>
            <span className="card-subtitle">Complete structured fields manually</span>
          </div>

          <form onSubmit={handleSaveForm} className="structured-form-body">
            
            <HcpSelector
              list={hcpState.list}
              value={formData.hcp_id}
              onChange={(val) => dispatch(updateFormField({ field: "hcp_id", value: val }))}
              error={formErrors.hcp_id}
            />

            {/* Grid Row: Type, Date, Time */}
            <div className="form-row-grid">
              <div className="form-group">
                <label className="form-label">Interaction Type</label>
                <select
                  className="form-control"
                  value={formData.interaction_type}
                  onChange={(e) => dispatch(updateFormField({ field: "interaction_type", value: e.target.value }))}
                >
                  <option value="In-Person">In-Person</option>
                  <option value="Virtual">Virtual</option>
                  <option value="Email">Email</option>
                  <option value="Phone">Phone</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Date <span className="text-danger">*</span></label>
                <div className="input-with-icon">
                  <Calendar size={16} className="input-icon" />
                  <input
                    type="date"
                    className={`form-control ${formErrors.interaction_date ? "is-invalid" : ""}`}
                    value={formData.interaction_date}
                    onChange={(e) => dispatch(updateFormField({ field: "interaction_date", value: e.target.value }))}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Time</label>
                <div className="input-with-icon">
                  <Clock size={16} className="input-icon" />
                  <input
                    type="time"
                    className="form-control"
                    value={formData.interaction_time}
                    onChange={(e) => dispatch(updateFormField({ field: "interaction_time", value: e.target.value }))}
                  />
                </div>
              </div>
            </div>

            {/* Attendees input (Chips) */}
            <div className="form-group">
              <label className="form-label">Attendees</label>
              <div className="input-with-icon">
                <Users size={16} className="input-icon" />
                <input
                  type="text"
                  className="form-control"
                  placeholder="Type name and press Enter"
                  value={attendeeInput}
                  onChange={(e) => setAttendeeInput(e.target.value)}
                  onKeyDown={handleAddAttendee}
                />
              </div>
              {formData.attendees.length > 0 && (
                <div className="attendee-chips">
                  {formData.attendees.map(a => (
                    <span key={a} className="chip">
                      {a}
                      <button type="button" onClick={() => handleRemoveAttendee(a)}>✕</button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Topics (Checkbox group) */}
            <div className="form-group">
              <label className="form-label">Topics Discussed <span className="text-danger">*</span></label>
              <div className="topics-checkbox-grid">
                {["Product Efficacy", "Efficacy and Safety", "Clinical Trial Data", "Pricing/Access"].map(t => (
                  <label key={t} className="checkbox-pill">
                    <input
                      type="checkbox"
                      checked={formData.topics_discussed.includes(t)}
                      onChange={() => handleTopicToggle(t)}
                    />
                    <span>{t}</span>
                  </label>
                ))}
              </div>
              {formErrors.topics_discussed && <div className="text-danger small">{formErrors.topics_discussed}</div>}
            </div>

            <MaterialSelector
              selected={formData.materials_shared}
              onChange={(val) => dispatch(updateFormField({ field: "materials_shared", value: val }))}
            />

            <SampleSelector
              samples={formData.samples_distributed}
              onChange={(val) => dispatch(updateFormField({ field: "samples_distributed", value: val }))}
            />

            <SentimentSelector
              value={formData.sentiment}
              onChange={(val) => dispatch(updateFormField({ field: "sentiment", value: val }))}
            />

            <div className="form-group">
              <label htmlFor="outcomes" className="form-label">Outcomes</label>
              <textarea
                id="outcomes"
                className="form-control text-area"
                rows="2"
                placeholder="Observed reaction, key quotes, requests..."
                value={formData.outcomes}
                onChange={(e) => dispatch(updateFormField({ field: "outcomes", value: e.target.value }))}
              />
            </div>

            {/* Grid Row: Follow up */}
            <div className="form-row-grid-2">
              <div className="form-group">
                <label className="form-label">Follow-Up Action</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Email trial data"
                  value={formData.follow_up_actions}
                  onChange={(e) => dispatch(updateFormField({ field: "follow_up_actions", value: e.target.value }))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Follow-Up Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={formData.follow_up_date}
                  onChange={(e) => dispatch(updateFormField({ field: "follow_up_date", value: e.target.value }))}
                />
              </div>
            </div>

            {/* Original conversational notes (if any) */}
            <div className="form-group">
              <label className="form-label">Conversational Notes / Dictation Raw Transcript</label>
              <textarea
                className="form-control text-area"
                rows="2"
                placeholder="Notes transcribed conversationally..."
                value={formData.original_notes}
                onChange={(e) => dispatch(updateFormField({ field: "original_notes", value: e.target.value }))}
              />
            </div>

            {/* AI Summary (Read-Only) */}
            {formData.ai_summary && (
              <div className="form-group ai-summary-container">
                <label className="form-label ai-summary-label">
                  <Sparkles size={14} /> AI Generated Summary
                </label>
                <div className="ai-summary-box">
                  {formData.ai_summary}
                </div>
              </div>
            )}

            {/* Consent Toggle for Voice processing */}
            <div className="form-group consent-toggle-group">
              <label className="switch">
                <input
                  type="checkbox"
                  checked={formData.consent_voice}
                  onChange={(e) => dispatch(updateFormField({ field: "consent_voice", value: e.target.checked }))}
                />
                <span className="slider round"></span>
              </label>
              <span className="consent-label">Representative confirms doctor consent for voice note AI processing</span>
            </div>

            {/* Form actions */}
            <div className="form-actions-buttons">
              <button type="button" className="btn-cancel" onClick={handleResetForm}>
                Reset
              </button>
              <button type="submit" className="btn-save" disabled={saveLoading}>
                {saveLoading ? "Saving..." : activeInteractionId ? "Update Log" : "Save Log"}
              </button>
            </div>
          </form>
        </section>

        {/* RIGHT COLUMN: AI Copilot & Timeline */}
        <div className="copilot-column-container">
          
          {/* Section A: AI Assistant Chat */}
          <section className="assistant-card">
            <div className="card-header bg-gradient">
              <div className="assistant-title-wrap">
                <Sparkles className="sparkle-icon" size={18} />
                <h3>Conversational AI Assistant</h3>
              </div>
              <span className="card-badge-ai">groq/compound</span>
            </div>

            {/* Chat Body */}
            <div className="chat-window-body">
              <div className="chat-messages-scroll">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}
                {agentLoading && (
                  <div className="chat-loading-indicator">
                    <span className="loading-dot"></span>
                    <span className="loading-dot"></span>
                    <span className="loading-dot"></span>
                    <span>Assistant is thinking...</span>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Extraction Preview panel */}
              {Object.keys(extractedData).length > 0 && (
                <div className="embedded-preview-container">
                  <ExtractedInteractionPreview
                    data={extractedData}
                    hcps={hcpState.list}
                    confidence={agentState.confidence}
                    missingFields={agentState.missingFields}
                  />
                  {requiresConfirmation && (
                    <ConfirmationPanel
                      onApprove={handleApproveExtract}
                      onReject={handleRejectExtract}
                      loading={saveLoading}
                    />
                  )}
                </div>
              )}

              {/* Suggestions quick chips */}
              <div className="quick-suggestions-chips">
                <button
                  type="button"
                  className="suggestion-chip"
                  onClick={() => handleSuggestionClick("Met Dr. Priya Sharma today at 2 PM. We discussed clinical efficacy of Product X. She requested a brochure. Sentiment positive.")}
                >
                  "Met Dr. Priya Sharma..."
                </button>
                <button
                  type="button"
                  className="suggestion-chip"
                  onClick={() => handleSuggestionClick("Retrieve recent history timeline for Priya Sharma")}
                >
                  "Retrieve recent history..."
                </button>
                <button
                  type="button"
                  className="suggestion-chip"
                  onClick={() => handleSuggestionClick("Suggest follow-up tasks for Dr Priya Sharma based on positive efficacy outcomes")}
                >
                  "Suggest follow-up..."
                </button>
              </div>

              {/* Chat Input form */}
              <form onSubmit={handleChatSend} className="chat-input-bar">
                <input
                  type="text"
                  className="chat-input-field"
                  placeholder="Describe interaction or type commands..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={agentLoading}
                />
                <button type="submit" className="chat-send-btn" disabled={agentLoading || !chatInput.trim()}>
                  <Send size={16} />
                </button>
              </form>
            </div>
          </section>

          {/* Section B: Doctor Timeline History */}
          <section className="history-card">
            <div className="card-header">
              <div className="history-title-wrap">
                <History size={18} className="text-primary" />
                <h3>Selected HCP Timeline History</h3>
              </div>
            </div>
            <div className="history-body">
              {history.length === 0 ? (
                <div className="history-empty">
                  No past interactions logged for the selected HCP.
                </div>
              ) : (
                <div className="timeline-flow">
                  {history.map((item, idx) => (
                    <div key={item.id} className="timeline-item">
                      <div className="timeline-badge-connector">
                        <span className={`timeline-badge ${item.sentiment.toLowerCase()}`}></span>
                        {idx !== history.length - 1 && <span className="timeline-connector"></span>}
                      </div>
                      <div className="timeline-content-card">
                        <div className="timeline-meta">
                          <span className="timeline-date">{item.interaction_date}</span>
                          <span className="timeline-type">{item.interaction_type}</span>
                          <button
                            type="button"
                            className="btn-edit-timeline"
                            onClick={() => dispatch(setEditMode(item))}
                          >
                            Edit
                          </button>
                        </div>
                        <div className="timeline-summary">
                          {item.ai_summary || "No summary recorded."}
                        </div>
                        {item.topics_discussed && item.topics_discussed.length > 0 && (
                          <div className="timeline-topics">
                            {item.topics_discussed.map((topic, i) => (
                              <span key={i} className="topic-tag">{topic}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

        </div>

      </div>
    </div>
  );
};

export default LogInteractionPage;

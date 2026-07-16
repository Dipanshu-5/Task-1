import React from "react";

const ConfirmationPanel = ({ onApprove, onReject, loading }) => {
  return (
    <div className="confirmation-panel">
      <div className="confirmation-header">
        <span className="warning-icon">⚠️</span>
        <div className="confirmation-title">
          Database Write Confirmation
        </div>
      </div>
      <p className="confirmation-body">
        The AI has extracted sufficient details to log this interaction. Please review the preview card and confirm below to write this interaction to the database.
      </p>
      <div className="confirmation-actions">
        <button 
          onClick={onReject} 
          className="btn-reject" 
          disabled={loading}
        >
          Discard / Edit Chat
        </button>
        <button 
          onClick={onApprove} 
          className="btn-approve" 
          disabled={loading}
        >
          {loading ? "Processing..." : "Confirm & Save"}
        </button>
      </div>
    </div>
  );
};

export default ConfirmationPanel;

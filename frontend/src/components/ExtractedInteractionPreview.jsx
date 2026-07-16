import React from "react";

const ExtractedInteractionPreview = ({ data, hcps, confidence, missingFields }) => {
  if (!data || Object.keys(data).length === 0) return null;

  // Find HCP name from id
  const hcpName = data.hcp_id 
    ? hcps.find(x => x.id === parseInt(data.hcp_id))?.full_name 
    : data.hcp_name || "Unidentified HCP";

  return (
    <div className="extracted-preview-card">
      <div className="preview-card-header">
        <h4>AI Extracted Details</h4>
        <span className="card-badge">Preview</span>
      </div>
      <div className="preview-card-body">
        
        {/* HCP Selection */}
        <div className="preview-row">
          <div className="preview-label">HCP Selection:</div>
          <div className={`preview-value ${!data.hcp_id ? "value-missing" : "value-extracted"}`}>
            {hcpName} {!data.hcp_id && "(Needs matching)"}
          </div>
        </div>

        {/* Interaction Type */}
        <div className="preview-row">
          <div className="preview-label">Interaction Type:</div>
          <div className="preview-value value-extracted">
            {data.interaction_type || "In-Person"}
          </div>
        </div>

        {/* Date & Time */}
        <div className="preview-row">
          <div className="preview-label">Date & Time:</div>
          <div className="preview-value value-extracted">
            {data.interaction_date || "Today"} {data.interaction_time && `@ ${data.interaction_time}`}
          </div>
        </div>

        {/* Sentiment */}
        <div className="preview-row">
          <div className="preview-label">Sentiment:</div>
          <div className={`preview-value sentiment-badge ${data.sentiment ? data.sentiment.toLowerCase() : "neutral"}`}>
            {data.sentiment || "Neutral"}
          </div>
        </div>

        {/* Topics */}
        <div className="preview-row">
          <div className="preview-label">Topics:</div>
          <div className="preview-value">
            {data.topics_discussed && data.topics_discussed.length > 0 ? (
              <div className="preview-tags">
                {data.topics_discussed.map((topic, i) => (
                  <span key={i} className="preview-tag">{topic}</span>
                ))}
              </div>
            ) : (
              <span className="value-missing">None</span>
            )}
          </div>
        </div>

        {/* Materials */}
        <div className="preview-row">
          <div className="preview-label">Materials:</div>
          <div className="preview-value">
            {data.materials_shared && data.materials_shared.length > 0 ? (
              <div className="preview-tags">
                {data.materials_shared.map((mat, i) => (
                  <span key={i} className="preview-tag-secondary">{mat}</span>
                ))}
              </div>
            ) : (
              <span className="text-muted">None</span>
            )}
          </div>
        </div>

        {/* Samples */}
        <div className="preview-row">
          <div className="preview-label">Samples:</div>
          <div className="preview-value">
            {data.samples_distributed && data.samples_distributed.length > 0 ? (
              <ul className="preview-list">
                {data.samples_distributed.map((samp, i) => (
                  <li key={i}>{samp.product} ({samp.quantity} units)</li>
                ))}
              </ul>
            ) : (
              <span className="text-muted">None</span>
            )}
          </div>
        </div>

        {/* Outcomes */}
        {data.outcomes && (
          <div className="preview-block">
            <div className="preview-label">Outcomes:</div>
            <div className="preview-text-block">{data.outcomes}</div>
          </div>
        )}

        {/* Follow-up */}
        {data.follow_up_actions && (
          <div className="preview-block">
            <div className="preview-label">Follow-up actions:</div>
            <div className="preview-text-block">
              {data.follow_up_actions} {data.follow_up_date && `(by ${data.follow_up_date})`}
            </div>
          </div>
        )}

        {/* AI Summary */}
        {data.ai_summary && (
          <div className="preview-block">
            <div className="preview-label">AI Summary:</div>
            <div className="preview-summary-block">{data.ai_summary}</div>
          </div>
        )}

        {/* Missing Fields Warnings */}
        {missingFields && missingFields.length > 0 && (
          <div className="preview-warning-box">
            <strong>Missing Fields Required:</strong>
            <ul className="warning-list">
              {missingFields.map((field, idx) => (
                <li key={idx}>{field}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExtractedInteractionPreview;

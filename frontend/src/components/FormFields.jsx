import React from "react";

// 1. HCP Selector
export const HcpSelector = ({ list, value, onChange, error }) => {
  return (
    <div className="form-group">
      <label htmlFor="hcp_id" className="form-label">Healthcare Professional (HCP) <span className="text-danger">*</span></label>
      <select
        id="hcp_id"
        className={`form-control ${error ? "is-invalid" : ""}`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">-- Select HCP --</option>
        {list.map((hcp) => (
          <option key={hcp.id} value={hcp.id}>
            {hcp.full_name} ({hcp.specialty} - {hcp.organization})
          </option>
        ))}
      </select>
      {error && <div className="invalid-feedback">{error}</div>}
    </div>
  );
};

// 2. Sentiment Selector
export const SentimentSelector = ({ value, onChange }) => {
  const options = ["Positive", "Neutral", "Negative"];
  return (
    <div className="form-group">
      <label className="form-label">Observed HCP Sentiment</label>
      <div className="sentiment-selector-group">
        {options.map((opt) => (
          <button
            key={opt}
            type="button"
            className={`sentiment-btn ${opt.toLowerCase()} ${value === opt ? "active" : ""}`}
            onClick={() => onChange(opt)}
          >
            {opt === "Positive" && "😊 "}
            {opt === "Neutral" && "😐 "}
            {opt === "Negative" && "😞 "}
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
};

// 3. Material Selector
export const MaterialSelector = ({ selected, onChange }) => {
  const materials = [
    "Clinical Trial Publication Package",
    "Clinical Brochure (Efficacy & Safety)",
    "Prescribing & Safety Guidelines",
    "Patient Starter Kits Info",
    "Co-Pay Access Brochure"
  ];

  const handleToggle = (mat) => {
    if (selected.includes(mat)) {
      onChange(selected.filter(x => x !== mat));
    } else {
      onChange([...selected, mat]);
    }
  };

  return (
    <div className="form-group">
      <label className="form-label">Materials Shared</label>
      <div className="materials-list">
        {materials.map((mat) => (
          <label key={mat} className="material-checkbox-container">
            <input
              type="checkbox"
              checked={selected.includes(mat)}
              onChange={() => handleToggle(mat)}
            />
            <span className="checkbox-label">{mat}</span>
          </label>
        ))}
      </div>
    </div>
  );
};

// 4. Sample Selector
export const SampleSelector = ({ samples, onChange }) => {
  const availableProducts = ["Product X (10mg)", "Product X (20mg)", "Product Y (50mg)", "Product Z (100mg)"];

  const handleAddSample = () => {
    onChange([...samples, { product: availableProducts[0], quantity: 5 }]);
  };

  const handleRemoveSample = (index) => {
    onChange(samples.filter((_, i) => i !== index));
  };

  const handleUpdateSample = (index, key, value) => {
    const updated = samples.map((item, i) => {
      if (i === index) {
        return { ...item, [key]: key === "quantity" ? parseInt(value) || 0 : value };
      }
      return item;
    });
    onChange(updated);
  };

  return (
    <div className="form-group">
      <div className="samples-header">
        <label className="form-label">Samples Distributed</label>
        <button type="button" className="btn-add-sample" onClick={handleAddSample}>
          + Add Sample
        </button>
      </div>
      {samples.length === 0 ? (
        <div className="samples-empty">No samples added. Click "+ Add Sample" to distribute samples.</div>
      ) : (
        <div className="samples-grid">
          {samples.map((item, index) => (
            <div key={index} className="sample-row">
              <select
                className="form-control select-sample-product"
                value={item.product}
                onChange={(e) => handleUpdateSample(index, "product", e.target.value)}
              >
                {availableProducts.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <input
                type="number"
                className="form-control input-sample-qty"
                min="1"
                value={item.quantity}
                onChange={(e) => handleUpdateSample(index, "quantity", e.target.value)}
              />
              <button
                type="button"
                className="btn-remove-sample"
                onClick={() => handleRemoveSample(index)}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

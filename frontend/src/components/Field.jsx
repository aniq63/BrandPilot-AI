export default function Field({ label, hint, required, error, children, wide }) {
  return (
    <label className={`field ${wide ? "field-wide" : ""}`}>
      <span className="field-label">
        {label}
        {required && <span className="required-dot">*</span>}
      </span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}

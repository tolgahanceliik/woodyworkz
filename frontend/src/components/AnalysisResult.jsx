/**
 * AnalysisResult
 * ---------------
 * Gemini'nin ürün analiz sonuçlarını gösteren kart.
 */

import { Tag, Layers, Palette, Users, Lightbulb, Star } from "lucide-react";

const Chip = ({ label, color = "#7c3aed" }) => (
  <span
    style={{
      display: "inline-block",
      background: `${color}22`,
      border: `1px solid ${color}55`,
      color,
      borderRadius: 20,
      padding: "2px 10px",
      fontSize: 12,
      margin: "2px 3px",
      fontWeight: 500,
    }}
  >
    {label}
  </span>
);

const Section = ({ icon: Icon, title, children }) => (
  <div style={{ marginBottom: 16 }}>
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        marginBottom: 6,
        color: "#9090b0",
        fontSize: 13,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: 1,
      }}
    >
      <Icon size={14} />
      {title}
    </div>
    {children}
  </div>
);

export default function AnalysisResult({ analysis }) {
  if (!analysis) return null;

  return (
    <div
      style={{
        background: "#1a1a2e",
        border: "1px solid #2d2d4e",
        borderRadius: 16,
        padding: 24,
      }}
    >
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: "#e2e8f0", marginBottom: 4 }}>
          {analysis.product_name}
        </h2>
        <span
          style={{
            background: "#7c3aed22",
            color: "#a78bfa",
            borderRadius: 8,
            padding: "2px 10px",
            fontSize: 13,
          }}
        >
          {analysis.category}
        </span>
        {"  "}
        <span
          style={{
            background: "#0ea5e922",
            color: "#38bdf8",
            borderRadius: 8,
            padding: "2px 10px",
            fontSize: 13,
          }}
        >
          {analysis.style}
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Section icon={Palette} title="Renkler">
          {analysis.colors?.map((c) => <Chip key={c} label={c} color="#ec4899" />)}
        </Section>

        <Section icon={Layers} title="Malzemeler">
          {analysis.materials?.map((m) => <Chip key={m} label={m} color="#f59e0b" />)}
        </Section>

        <Section icon={Star} title="Öne Çıkan Özellikler">
          <ul style={{ paddingLeft: 16, color: "#b0b0cc", fontSize: 13, lineHeight: 1.8 }}>
            {analysis.key_features?.map((f) => <li key={f}>{f}</li>)}
          </ul>
        </Section>

        <Section icon={Users} title="Hedef Kitle & Marka Tonu">
          <p style={{ color: "#b0b0cc", fontSize: 13, marginBottom: 4 }}>
            {analysis.target_audience}
          </p>
          <Chip label={analysis.brand_tone} color="#10b981" />
        </Section>

        <Section icon={Lightbulb} title="Işık Önerisi">
          <p style={{ color: "#b0b0cc", fontSize: 13 }}>{analysis.lighting_recommendation}</p>
        </Section>

        <Section icon={Tag} title="Arka Plan Önerileri">
          {analysis.suggested_backgrounds?.map((bg) => (
            <Chip key={bg} label={bg} color="#6366f1" />
          ))}
        </Section>
      </div>
    </div>
  );
}

/**
 * AnalysisResult
 * ---------------
 * WoodAnalysis nesnesini görsel kart olarak gösterir.
 * gemini_service.py'nin zenginleştirilmiş çıktısına uygun.
 */

import { Layers, Palette, Lightbulb, Star, Leaf, Eye, Cpu, Info } from "lucide-react";

// ── küçük yardımcılar ───────────────────────────────────────────────────────

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

const Badge = ({ label, color = "#7c3aed" }) => (
  <span
    style={{
      background: `${color}22`,
      color,
      borderRadius: 8,
      padding: "3px 10px",
      fontSize: 13,
      fontWeight: 600,
    }}
  >
    {label}
  </span>
);

const Section = ({ icon: Icon, title, children }) => (
  <div style={{ marginBottom: 18 }}>
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 7,
        marginBottom: 8,
        color: "#7070a0",
        fontSize: 11,
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: 1.2,
      }}
    >
      <Icon size={13} />
      {title}
    </div>
    {children}
  </div>
);

// ── Damar göstergesi ────────────────────────────────────────────────────────

const GrainBar = ({ visibility }) => {
  const levels = { subtle: 1, moderate: 2, prominent: 3, very_prominent: 4 };
  const filled = levels[visibility] ?? 2;
  return (
    <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
      {[1, 2, 3, 4].map((n) => (
        <div
          key={n}
          style={{
            width: 22,
            height: 6,
            borderRadius: 3,
            background: n <= filled ? "#f59e0b" : "#2d2d4e",
            transition: "background 0.3s",
          }}
        />
      ))}
      <span style={{ color: "#9090b0", fontSize: 11, marginLeft: 4 }}>
        {visibility?.replace("_", " ")}
      </span>
    </div>
  );
};

// ── Renk noktası ────────────────────────────────────────────────────────────

const ColorDot = ({ hex, label }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
    {hex && (
      <div
        style={{
          width: 18,
          height: 18,
          borderRadius: "50%",
          background: hex,
          border: "2px solid #3d3d5c",
          flexShrink: 0,
        }}
      />
    )}
    <span style={{ color: "#b0b0cc", fontSize: 13 }}>{label}</span>
  </div>
);

// ── Ana bileşen ─────────────────────────────────────────────────────────────

export default function AnalysisResult({ analysis }) {
  if (!analysis) return null;

  const grain = analysis.grain ?? {};
  const finish = analysis.finish ?? {};
  const color = analysis.color ?? {};

  const confidenceColor =
    analysis.wood_species_confidence === "high"
      ? "#4ade80"
      : analysis.wood_species_confidence === "medium"
      ? "#f59e0b"
      : "#f87171";

  return (
    <div
      style={{
        background: "#1a1a2e",
        border: "1px solid #2d2d4e",
        borderRadius: 16,
        padding: 24,
      }}
    >
      {/* Başlık */}
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, fontWeight: 800, color: "#e2e8f0", marginBottom: 8 }}>
          {analysis.product_name}
        </h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Badge label={analysis.product_type?.replace(/_/g, " ")} color="#7c3aed" />
          <Badge label={analysis.style?.replace(/_/g, " ")} color="#0ea5e9" />
          <Badge label={analysis.craftsmanship?.replace(/_/g, " ")} color="#10b981" />
          <Badge label={analysis.environment} color="#f59e0b" />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Ağaç türü */}
        <Section icon={Leaf} title="Ağaç Türü">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ color: "#e2e8f0", fontWeight: 700, fontSize: 18, textTransform: "capitalize" }}>
              {analysis.wood_species?.replace(/_/g, " ")}
            </span>
            <span
              style={{
                background: `${confidenceColor}22`,
                color: confidenceColor,
                borderRadius: 20,
                padding: "1px 8px",
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              {analysis.wood_species_confidence} güven
            </span>
          </div>
          {analysis.wood_species_alternatives?.length > 0 && (
            <p style={{ color: "#6060a0", fontSize: 12 }}>
              Alternatif: {analysis.wood_species_alternatives.join(", ")}
            </p>
          )}
        </Section>

        {/* Boyut */}
        <Section icon={Info} title="Boyut Tahmini">
          <p style={{ color: "#b0b0cc", fontSize: 13, lineHeight: 1.6 }}>
            {analysis.size_estimate}
          </p>
        </Section>

        {/* Damar */}
        <Section icon={Eye} title="Ahşap Damarı">
          <GrainBar visibility={grain.visibility} />
          <p style={{ color: "#8080a0", fontSize: 12, marginTop: 6 }}>
            {grain.pattern?.replace(/_/g, " ")} desen · {grain.description}
          </p>
        </Section>

        {/* Yüzey işlemi */}
        <Section icon={Cpu} title="Yüzey İşlemi">
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <Chip label={finish.type?.replace(/_/g, " ")} color="#6366f1" />
            <Chip label={finish.sheen} color="#8b5cf6" />
            <Chip label={finish.texture_feel?.replace(/_/g, " ")} color="#a78bfa" />
          </div>
        </Section>

        {/* Renk */}
        <Section icon={Palette} title="Renk Profili">
          <ColorDot hex={color.hex_estimate} label={color.primary} />
          <div style={{ marginTop: 6, display: "flex", gap: 4, flexWrap: "wrap" }}>
            {color.secondary?.map((c) => (
              <Chip key={c} label={c} color="#ec4899" />
            ))}
            <Chip label={`${color.undertone} undertone`} color="#f472b6" />
          </div>
        </Section>

        {/* Ayırt edici özellikler */}
        <Section icon={Star} title="Belirgin Özellikler">
          <div>
            {analysis.distinctive_features?.map((f) => (
              <Chip key={f} label={f.replace(/_/g, " ")} color="#f59e0b" />
            ))}
            {analysis.joinery_details?.map((j) => (
              <Chip key={j} label={j.replace(/_/g, " ")} color="#fb923c" />
            ))}
          </div>
        </Section>

        {/* Işık önerisi */}
        <Section icon={Lightbulb} title="Işık Önerisi">
          <p style={{ color: "#b0b0cc", fontSize: 13 }}>{analysis.lighting_recommendation}</p>
        </Section>

        {/* Arka plan önerileri */}
        <Section icon={Layers} title="Arka Plan Önerileri">
          {analysis.suggested_backgrounds?.map((bg) => (
            <Chip key={bg} label={bg} color="#06b6d4" />
          ))}
        </Section>
      </div>

      {/* Prompt anahtar kelimeleri */}
      {analysis.prompt_keywords?.length > 0 && (
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #2d2d4e" }}>
          <p style={{ color: "#5a5a7a", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>
            Üretim Anahtar Kelimeleri
          </p>
          <div>
            {analysis.prompt_keywords.map((kw) => (
              <Chip key={kw} label={kw} color="#64748b" />
            ))}
          </div>
        </div>
      )}

      {/* Model notu */}
      {analysis.analysis_notes && (
        <div
          style={{
            marginTop: 14,
            background: "#f59e0b11",
            border: "1px solid #f59e0b33",
            borderRadius: 10,
            padding: "10px 14px",
            color: "#fbbf24",
            fontSize: 12,
          }}
        >
          Not: {analysis.analysis_notes}
        </div>
      )}
    </div>
  );
}

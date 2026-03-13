/**
 * GeneratedPhotos
 * ----------------
 * Üretilen 5 profesyonel çekimi grid olarak gösterir.
 */

import { Download, RefreshCw, CheckCircle, XCircle, Loader } from "lucide-react";

const STATUS_ICON = {
  completed: <CheckCircle size={16} color="#4ade80" />,
  failed: <XCircle size={16} color="#f87171" />,
  processing: <Loader size={16} color="#f59e0b" style={{ animation: "spin 1s linear infinite" }} />,
  pending: <Loader size={16} color="#9090b0" />,
};

function ShotCard({ shot, index }) {
  const isSuccess = shot.status === "completed" && shot.image_url;

  const download = () => {
    const a = document.createElement("a");
    a.href = shot.image_url;
    a.download = `shot_${index + 1}_${shot.angle.replace(/\s+/g, "_")}.png`;
    a.click();
  };

  return (
    <div
      style={{
        background: "#1a1a2e",
        border: "1px solid #2d2d4e",
        borderRadius: 14,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Görüntü alanı */}
      <div
        style={{
          height: 220,
          background: "#0f0f1a",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
        }}
      >
        {isSuccess ? (
          <img
            src={shot.image_url}
            alt={shot.angle}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        ) : (
          <div style={{ textAlign: "center", color: "#5a5a7a" }}>
            {STATUS_ICON[shot.status]}
            <p style={{ fontSize: 12, marginTop: 8 }}>
              {shot.status === "failed" ? "Üretim başarısız" : "Bekleniyor..."}
            </p>
          </div>
        )}

        {/* Numara rozeti */}
        <div
          style={{
            position: "absolute",
            top: 8,
            left: 8,
            background: "#7c3aed",
            color: "#fff",
            borderRadius: 20,
            width: 24,
            height: 24,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 11,
            fontWeight: 700,
          }}
        >
          {index + 1}
        </div>
      </div>

      {/* Bilgi alanı */}
      <div style={{ padding: 14 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 6,
          }}
        >
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>
            {shot.angle}
          </h3>
          {STATUS_ICON[shot.status]}
        </div>

        <p
          style={{
            fontSize: 11,
            color: "#6060a0",
            lineHeight: 1.5,
            marginBottom: 10,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {shot.prompt_used}
        </p>

        {isSuccess && (
          <button
            onClick={download}
            style={{
              width: "100%",
              background: "#7c3aed",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "8px 0",
              cursor: "pointer",
              fontSize: 13,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
              fontWeight: 500,
            }}
          >
            <Download size={14} />
            İndir
          </button>
        )}
      </div>
    </div>
  );
}

export default function GeneratedPhotos({ shots = [], loading = false }) {
  if (loading) {
    return (
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: 16,
        }}
      >
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            style={{
              height: 300,
              background: "#1a1a2e",
              border: "1px solid #2d2d4e",
              borderRadius: 14,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#4a4a7a",
              fontSize: 13,
            }}
          >
            <RefreshCw size={20} style={{ animation: "spin 1s linear infinite" }} />
          </div>
        ))}
      </div>
    );
  }

  if (shots.length === 0) return null;

  return (
    <div>
      <h2
        style={{
          fontSize: 20,
          fontWeight: 700,
          color: "#e2e8f0",
          marginBottom: 16,
        }}
      >
        Üretilen Profesyonel Çekimler
      </h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: 16,
        }}
      >
        {shots.map((shot, i) => (
          <ShotCard key={`${shot.angle}-${i}`} shot={shot} index={i} />
        ))}
      </div>
    </div>
  );
}

/**
 * GeneratedPhotos  — Galeri
 * --------------------------
 * Üretilen 5 profesyonel çekimi responsive grid olarak gösterir.
 * Her kart:
 *   • Açı adı + ortam rozeti
 *   • Tam boyut önizleme
 *   • "Yüksek Çözünürlüklü İndir" butonu (PNG olarak)
 *   • Hata durumunda açıklama
 */

import { useState } from "react";
import { Download, Maximize2, X, CheckCircle, XCircle, Camera } from "lucide-react";

// ── Lightbox ────────────────────────────────────────────────────────────────

function Lightbox({ shot, onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.92)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <button
        onClick={onClose}
        style={{
          position: "fixed",
          top: 20,
          right: 24,
          background: "rgba(255,255,255,0.1)",
          border: "none",
          borderRadius: "50%",
          width: 40,
          height: 40,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          color: "#fff",
        }}
      >
        <X size={20} />
      </button>

      <div
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "90vw", maxHeight: "90vh", textAlign: "center" }}
      >
        <img
          src={shot.image_url}
          alt={shot.angle_tr}
          style={{
            maxWidth: "100%",
            maxHeight: "80vh",
            objectFit: "contain",
            borderRadius: 12,
            boxShadow: "0 0 60px rgba(124,58,237,0.3)",
          }}
        />
        <div style={{ marginTop: 16 }}>
          <h3 style={{ color: "#e2e8f0", fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
            {shot.angle_tr}
          </h3>
          <p style={{ color: "#6060a0", fontSize: 12, maxWidth: 600, margin: "0 auto 16px" }}>
            {shot.prompt_used}
          </p>
          <DownloadButton shot={shot} large />
        </div>
      </div>
    </div>
  );
}

// ── İndir butonu ─────────────────────────────────────────────────────────────

function DownloadButton({ shot, large = false }) {
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await fetch(shot.image_url);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `woodyworkz_${shot.angle_en?.replace(/\s+/g, "_") ?? shot.index}_HD.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={downloading}
      style={{
        background: downloading ? "#3d2a6e" : "#7c3aed",
        color: downloading ? "#9070cc" : "#fff",
        border: "none",
        borderRadius: large ? 12 : 8,
        padding: large ? "12px 28px" : "8px 14px",
        cursor: downloading ? "not-allowed" : "pointer",
        fontSize: large ? 15 : 13,
        fontWeight: 600,
        display: "inline-flex",
        alignItems: "center",
        gap: 7,
        transition: "background 0.2s",
      }}
    >
      <Download size={large ? 18 : 14} />
      {downloading ? "İndiriliyor..." : "Yüksek Çözünürlüklü İndir"}
    </button>
  );
}

// ── Yükleniyor iskelet ───────────────────────────────────────────────────────

function SkeletonCard() {
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
      <div
        style={{
          height: 240,
          background: "linear-gradient(90deg,#1a1a2e 25%,#24244a 50%,#1a1a2e 75%)",
          backgroundSize: "200% 100%",
          animation: "shimmer 1.4s infinite",
        }}
      />
      <div style={{ padding: 14 }}>
        <div
          style={{
            height: 14,
            width: "60%",
            background: "#2d2d4e",
            borderRadius: 6,
            marginBottom: 8,
          }}
        />
        <div style={{ height: 10, width: "90%", background: "#232338", borderRadius: 6 }} />
      </div>
    </div>
  );
}

// ── Çekim kartı ──────────────────────────────────────────────────────────────

function ShotCard({ shot }) {
  const [lightbox, setLightbox] = useState(false);
  const isOk = shot.status === "completed" && shot.image_url;

  return (
    <>
      <div
        style={{
          background: "#1a1a2e",
          border: `1px solid ${isOk ? "#2d2d4e" : "#f871712a"}`,
          borderRadius: 14,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          transition: "transform 0.15s, box-shadow 0.15s",
        }}
        onMouseEnter={(e) => {
          if (isOk) {
            e.currentTarget.style.transform = "translateY(-3px)";
            e.currentTarget.style.boxShadow = "0 8px 32px rgba(124,58,237,0.18)";
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "";
          e.currentTarget.style.boxShadow = "";
        }}
      >
        {/* Görüntü alanı */}
        <div style={{ position: "relative", height: 240, background: "#0f0f1a", cursor: isOk ? "zoom-in" : "default" }}
             onClick={() => isOk && setLightbox(true)}>
          {isOk ? (
            <>
              <img
                src={shot.image_url}
                alt={shot.angle_tr}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
              {/* Hover overlay */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "rgba(0,0,0,0)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "background 0.2s",
                }}
                className="card-overlay"
              >
                <Maximize2 size={28} color="#fff" style={{ opacity: 0.8 }} />
              </div>
            </>
          ) : (
            <div
              style={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
              }}
            >
              <XCircle size={32} color="#f87171" />
              <p style={{ color: "#f87171", fontSize: 13 }}>Üretim başarısız</p>
              {shot.error && (
                <p style={{ color: "#5a5a7a", fontSize: 11, textAlign: "center", padding: "0 16px" }}>
                  {shot.error}
                </p>
              )}
            </div>
          )}

          {/* Numara rozeti */}
          <div
            style={{
              position: "absolute",
              top: 10,
              left: 10,
              background: "#7c3aed",
              color: "#fff",
              borderRadius: 20,
              width: 26,
              height: 26,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 12,
              fontWeight: 700,
              boxShadow: "0 2px 8px rgba(0,0,0,0.4)",
            }}
          >
            {shot.index}
          </div>

          {/* Durum rozeti */}
          <div
            style={{
              position: "absolute",
              top: 10,
              right: 10,
              background: isOk ? "rgba(74,222,128,0.15)" : "rgba(248,113,113,0.15)",
              border: `1px solid ${isOk ? "#4ade8044" : "#f8717144"}`,
              borderRadius: 20,
              padding: "2px 8px",
              display: "flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
              color: isOk ? "#4ade80" : "#f87171",
            }}
          >
            {isOk ? <CheckCircle size={11} /> : <XCircle size={11} />}
            {isOk ? "Tamamlandı" : "Başarısız"}
          </div>
        </div>

        {/* Bilgi + aksiyon */}
        <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Camera size={14} color="#7c3aed" />
            <h3 style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>
              {shot.angle_tr}
            </h3>
            <span style={{ marginLeft: "auto", fontSize: 11, color: "#5a5a7a" }}>
              {shot.angle_en}
            </span>
          </div>

          <p
            style={{
              fontSize: 11,
              color: "#4a4a6a",
              lineHeight: 1.5,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              flex: 1,
            }}
          >
            {shot.prompt_used}
          </p>

          {isOk && <DownloadButton shot={shot} />}
        </div>
      </div>

      {lightbox && <Lightbox shot={shot} onClose={() => setLightbox(false)} />}
    </>
  );
}

// ── Ana bileşen ──────────────────────────────────────────────────────────────

export default function GeneratedPhotos({ shots = [], loading = false, jobId, completedCount }) {
  if (!loading && shots.length === 0) return null;

  return (
    <div>
      {/* Başlık */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, fontWeight: 800, color: "#e2e8f0" }}>
          Profesyonel Çekimler
        </h2>
        {!loading && shots.length > 0 && (
          <span style={{ color: "#6060a0", fontSize: 13 }}>
            {completedCount}/{shots.length} başarılı
            {jobId && <span style={{ color: "#3d3d5c", marginLeft: 8 }}>· job: {jobId.slice(0, 8)}</span>}
          </span>
        )}
      </div>

      {/* Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))",
          gap: 16,
        }}
      >
        {loading
          ? Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)
          : shots.map((shot) => <ShotCard key={`${shot.index}-${shot.angle_en}`} shot={shot} />)}
      </div>

      {/* CSS animasyonlar */}
      <style>{`
        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position:  200% 0; }
        }
        .card-overlay:hover { background: rgba(0,0,0,0.3) !important; }
      `}</style>
    </div>
  );
}

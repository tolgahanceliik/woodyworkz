/**
 * WoodyWorkz AI Product Studio  — Ana Uygulama
 * ──────────────────────────────────────────────
 * İş akışı:
 *   1. Fotoğraf Yükle     → MultiDropzone (1-4 adet)
 *   2. Analiz             → /studio/upload  → WoodAnalysis kartı
 *   3. Ortam Seç + Üret  → /studio/generate → 5 açı galeri
 */

import { useState } from "react";
import toast from "react-hot-toast";
import { Sparkles, Loader2, ChevronRight, RefreshCw, TreePine } from "lucide-react";

import MultiDropzone from "./components/MultiDropzone";
import AnalysisResult from "./components/AnalysisResult";
import GeneratedPhotos from "./components/GeneratedPhotos";
import { uploadAndAnalyze, generateShots } from "./services/api";

// ── Sabitler ─────────────────────────────────────────────────────────────────

const STEPS = ["Fotoğraf Yükle", "Ürün Analizi", "Ortam Seç", "Galeri"];

const ENVIRONMENTS = [
  { value: "studio",       label: "Stüdyo",         emoji: "🎬", desc: "Seamless arka fon, kontrollü ışık" },
  { value: "nature",       label: "Doğa",            emoji: "🌿", desc: "Orman, altın saat ışığı" },
  { value: "home",         label: "Ev İçi",          emoji: "🏠", desc: "Oturma odası, sıcak ortam" },
  { value: "workshop",     label: "Atölye",          emoji: "🔨", desc: "Ham ahşap talaşı, endüstriyel" },
  { value: "minimalist",   label: "Minimalist",      emoji: "⬜", desc: "Beyaz / beton, hiçbir unsur" },
  { value: "luxury",       label: "Lüks",            emoji: "💎", desc: "Mermer, derin gölge, premium" },
  { value: "outdoor_cafe", label: "Dış Mekan Kafe",  emoji: "☕", desc: "Taş döşeme, Akdeniz ruhu" },
];

// ── Küçük yardımcı bileşenler ────────────────────────────────────────────────

function StepBar({ current }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "center", marginBottom: 32 }}>
      {STEPS.map((label, i) => (
        <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              background: i < current ? "#4ade8033" : i === current ? "#7c3aed" : "#1e1e38",
              border: i < current ? "2px solid #4ade80" : i === current ? "2px solid #7c3aed" : "2px solid #2d2d4e",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 12,
              fontWeight: 700,
              color: i < current ? "#4ade80" : i === current ? "#fff" : "#4a4a6a",
              transition: "all 0.3s",
            }}
          >
            {i < current ? "✓" : i + 1}
          </div>
          <span
            style={{
              fontSize: 13,
              color: i <= current ? "#e2e8f0" : "#4a4a6a",
              fontWeight: i === current ? 700 : 400,
            }}
          >
            {label}
          </span>
          {i < STEPS.length - 1 && <ChevronRight size={12} color="#2d2d4e" />}
        </div>
      ))}
    </div>
  );
}

function PrimaryButton({ onClick, disabled, loading, children, fullWidth = false }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        background: disabled || loading ? "#2d1f5e" : "#7c3aed",
        color: disabled || loading ? "#6040a0" : "#fff",
        border: "none",
        borderRadius: 12,
        padding: "14px 32px",
        fontSize: 16,
        fontWeight: 700,
        cursor: disabled || loading ? "not-allowed" : "pointer",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        transition: "background 0.2s, transform 0.15s",
        width: fullWidth ? "100%" : "auto",
      }}
      onMouseEnter={(e) => { if (!disabled && !loading) e.currentTarget.style.transform = "scale(1.02)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = ""; }}
    >
      {loading && <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />}
      {children}
    </button>
  );
}

function LoadingBanner({ message }) {
  return (
    <div
      style={{
        background: "#16162a",
        border: "1px solid #7c3aed44",
        borderRadius: 12,
        padding: "14px 20px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        marginBottom: 20,
      }}
    >
      <Loader2 size={18} color="#7c3aed" style={{ animation: "spin 1s linear infinite", flexShrink: 0 }} />
      <span style={{ color: "#a78bfa", fontWeight: 500, fontSize: 14 }}>{message}</span>
    </div>
  );
}

// ── Ortam seçici ─────────────────────────────────────────────────────────────

function EnvPicker({ value, onChange }) {
  return (
    <div>
      <p style={{ color: "#7070a0", fontSize: 13, marginBottom: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1 }}>
        Çekim Ortamı Seçin
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(170px, 1fr))", gap: 10 }}>
        {ENVIRONMENTS.map((env) => (
          <button
            key={env.value}
            onClick={() => onChange(env.value)}
            style={{
              background: value === env.value ? "#7c3aed22" : "#1a1a2e",
              border: `2px solid ${value === env.value ? "#7c3aed" : "#2d2d4e"}`,
              borderRadius: 12,
              padding: "12px 14px",
              cursor: "pointer",
              textAlign: "left",
              transition: "all 0.15s",
            }}
          >
            <div style={{ fontSize: 20, marginBottom: 4 }}>{env.emoji}</div>
            <div style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 600, marginBottom: 2 }}>
              {env.label}
            </div>
            <div style={{ color: "#5a5a7a", fontSize: 11 }}>{env.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Ana bileşen ──────────────────────────────────────────────────────────────

export default function App() {
  const [files, setFiles] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [extraContext, setExtraContext] = useState("");
  const [environment, setEnvironment] = useState("studio");
  const [shots, setShots] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [completedCount, setCompletedCount] = useState(0);
  const [step, setStep] = useState(0);
  const [loadingMsg, setLoadingMsg] = useState("");

  const loading = loadingMsg !== "";

  // 1. Analiz
  const handleAnalyze = async () => {
    if (files.length === 0) return;
    setLoadingMsg(`${files.length} fotoğraf Gemini Vision ile analiz ediliyor...`);
    try {
      const res = await uploadAndAnalyze(files, extraContext);
      setAnalysis(res.analysis);
      setStep(2);
      toast.success(`Analiz tamamlandı — ${res.analysis.wood_species} tespit edildi!`);
    } catch (err) {
      toast.error(`Analiz hatası: ${err.message}`);
    } finally {
      setLoadingMsg("");
    }
  };

  // 2. Görüntü üret
  const handleGenerate = async () => {
    if (!analysis || files.length === 0) return;
    setShots([]);
    setLoadingMsg(`5 çekim ${environment} ortamı için üretiliyor... (bu birkaç dakika sürebilir)`);
    setStep(3);
    try {
      // referans olarak ilk fotoğrafı kullan
      const res = await generateShots(files[0], analysis, environment);
      setShots(res.shots);
      setJobId(res.job_id);
      setCompletedCount(res.completed);
      toast.success(`${res.completed}/5 çekim başarıyla oluşturuldu!`);
    } catch (err) {
      toast.error(`Üretim hatası: ${err.message}`);
      setStep(2);
    } finally {
      setLoadingMsg("");
    }
  };

  // Sıfırla
  const handleReset = () => {
    setFiles([]); setAnalysis(null); setExtraContext("");
    setShots([]); setJobId(null); setStep(0); setLoadingMsg("");
    setEnvironment("studio");
  };

  return (
    <div style={{ minHeight: "100vh", padding: "32px 16px" }}>
      <div style={{ maxWidth: 960, margin: "0 auto" }}>

        {/* Başlık */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 12, marginBottom: 12 }}>
            <TreePine size={28} color="#4ade80" />
            <h1 style={{ fontSize: 30, fontWeight: 900, color: "#e2e8f0", letterSpacing: -0.5 }}>
              WoodyWorkz AI Studio
            </h1>
            <Sparkles size={22} color="#7c3aed" />
          </div>
          <p style={{ color: "#6060a0", fontSize: 15, maxWidth: 520, margin: "0 auto" }}>
            Ahşap ürün fotoğraflarınızı yükleyin — Gemini AI ağaç türünü, dokusunu ve stilini
            analiz etsin, 5 profesyonel çekim üretsin.
          </p>
        </div>

        <StepBar current={step} />

        {loading && <LoadingBanner message={loadingMsg} />}

        {/* ── Adım 0: Fotoğraf yükle ── */}
        {step === 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <MultiDropzone files={files} onChange={setFiles} disabled={loading} />

            <input
              type="text"
              placeholder="Ek bağlam (opsiyonel): 'El yapımı ceviz masa, Türk işçiliği...'"
              value={extraContext}
              onChange={(e) => setExtraContext(e.target.value)}
              maxLength={500}
              style={{
                background: "#16162a",
                border: "1px solid #2d2d4e",
                borderRadius: 10,
                padding: "12px 16px",
                color: "#e2e8f0",
                fontSize: 14,
                outline: "none",
                width: "100%",
              }}
            />

            <div style={{ display: "flex", justifyContent: "center", marginTop: 8 }}>
              <PrimaryButton onClick={handleAnalyze} disabled={files.length === 0} loading={loading}>
                <Sparkles size={18} />
                Analiz Et ({files.length} fotoğraf)
              </PrimaryButton>
            </div>
          </div>
        )}

        {/* ── Adım 1 işareti: analiz yükleniyor ── */}
        {step === 1 && loading && (
          <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
            <Loader2 size={36} color="#7c3aed" style={{ animation: "spin 1s linear infinite" }} />
          </div>
        )}

        {/* ── Adım 2: Analiz sonucu + ortam seçimi ── */}
        {step >= 2 && analysis && (
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <AnalysisResult analysis={analysis} />

            {step === 2 && (
              <>
                <EnvPicker value={environment} onChange={setEnvironment} />
                <div style={{ display: "flex", justifyContent: "center", gap: 12 }}>
                  <button
                    onClick={handleReset}
                    style={{
                      background: "transparent",
                      border: "1px solid #3d3d5c",
                      color: "#7070a0",
                      borderRadius: 12,
                      padding: "12px 24px",
                      cursor: "pointer",
                      fontSize: 14,
                      display: "flex",
                      alignItems: "center",
                      gap: 7,
                    }}
                  >
                    <RefreshCw size={15} /> Yeni Ürün
                  </button>
                  <PrimaryButton onClick={handleGenerate} loading={loading}>
                    <Sparkles size={18} />
                    5 Çekim Üret
                  </PrimaryButton>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Adım 3: Galeri ── */}
        {step === 3 && (
          <div style={{ marginTop: 24 }}>
            <GeneratedPhotos
              shots={shots}
              loading={loading}
              jobId={jobId}
              completedCount={completedCount}
            />
            {!loading && shots.length > 0 && (
              <div style={{ display: "flex", justifyContent: "center", marginTop: 32 }}>
                <button
                  onClick={handleReset}
                  style={{
                    background: "transparent",
                    border: "2px solid #7c3aed",
                    color: "#a78bfa",
                    borderRadius: 12,
                    padding: "13px 30px",
                    cursor: "pointer",
                    fontSize: 15,
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <RefreshCw size={16} /> Yeni Ürün Analiz Et
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

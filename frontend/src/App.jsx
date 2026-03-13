/**
 * WoodyWorkz AI Product Studio
 * ─────────────────────────────
 * Ana uygulama bileşeni.
 * Adım adım iş akışı:
 *   1. Görüntü yükle
 *   2. Gemini ile ürün analizi
 *   3. 5 çekim açısı promptu üret
 *   4. Görüntüleri üret ve göster
 */

import { useState } from "react";
import toast from "react-hot-toast";
import { Sparkles, Loader2, ChevronRight } from "lucide-react";

import ImageUpload from "./components/ImageUpload";
import AnalysisResult from "./components/AnalysisResult";
import GeneratedPhotos from "./components/GeneratedPhotos";
import {
  analyzeProduct,
  generateShotPrompts,
  generateAllShots,
} from "./services/api";

// ─── Adım göstergesi ────────────────────────────────────────────────────────

const STEPS = ["Görüntü Yükle", "Analiz Et", "Çekim Üret", "Sonuçlar"];

function StepBar({ current }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        marginBottom: 32,
        justifyContent: "center",
      }}
    >
      {STEPS.map((label, i) => (
        <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              background: i <= current ? "#7c3aed" : "#2d2d4e",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 12,
              fontWeight: 700,
              color: i <= current ? "#fff" : "#5a5a7a",
              transition: "background 0.3s",
            }}
          >
            {i + 1}
          </div>
          <span
            style={{
              fontSize: 13,
              color: i <= current ? "#e2e8f0" : "#5a5a7a",
              fontWeight: i === current ? 600 : 400,
            }}
          >
            {label}
          </span>
          {i < STEPS.length - 1 && <ChevronRight size={14} color="#3d3d5c" />}
        </div>
      ))}
    </div>
  );
}

// ─── Buton ──────────────────────────────────────────────────────────────────

function PrimaryButton({ onClick, disabled, loading, children }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        background: disabled || loading ? "#3d2a6e" : "#7c3aed",
        color: disabled || loading ? "#7a5aaa" : "#fff",
        border: "none",
        borderRadius: 12,
        padding: "14px 32px",
        fontSize: 16,
        fontWeight: 600,
        cursor: disabled || loading ? "not-allowed" : "pointer",
        display: "flex",
        alignItems: "center",
        gap: 8,
        transition: "background 0.2s",
      }}
    >
      {loading ? <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} /> : null}
      {children}
    </button>
  );
}

// ─── Ana bileşen ────────────────────────────────────────────────────────────

export default function App() {
  const [imageFile, setImageFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [shots, setShots] = useState([]);          // üretilmiş çekimler
  const [step, setStep] = useState(0);
  const [loadingMsg, setLoadingMsg] = useState("");

  const isLoading = loadingMsg !== "";

  // 1. Analiz
  const handleAnalyze = async () => {
    if (!imageFile) return;
    setLoadingMsg("Ürün analiz ediliyor...");
    try {
      const res = await analyzeProduct(imageFile);
      setAnalysis(res.analysis);
      setStep(1);
      toast.success("Analiz tamamlandı!");
    } catch (err) {
      toast.error(`Analiz hatası: ${err.message}`);
    } finally {
      setLoadingMsg("");
    }
  };

  // 2. Çekim üret
  const handleGenerate = async () => {
    if (!analysis || !imageFile) return;
    setLoadingMsg("Çekim açıları hesaplanıyor...");
    setStep(2);
    try {
      // 5 çekim promptu al
      const promptRes = await generateShotPrompts(imageFile, analysis);
      const shotPrompts = promptRes.shots;

      setLoadingMsg("Profesyonel çekimler oluşturuluyor... (bu biraz sürebilir)");

      // Görüntüleri üret
      const genRes = await generateAllShots(imageFile, shotPrompts);
      setShots(genRes.shots);
      setStep(3);
      toast.success(`${genRes.shots.filter(s => s.status === "completed").length}/5 çekim oluşturuldu!`);
    } catch (err) {
      toast.error(`Üretim hatası: ${err.message}`);
      setStep(1);
    } finally {
      setLoadingMsg("");
    }
  };

  // Sıfırla
  const handleReset = () => {
    setImageFile(null);
    setAnalysis(null);
    setShots([]);
    setStep(0);
    setLoadingMsg("");
  };

  return (
    <div style={{ minHeight: "100vh", padding: "32px 16px" }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        {/* Başlık */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 12 }}>
            <Sparkles size={28} color="#7c3aed" />
            <h1 style={{ fontSize: 28, fontWeight: 800, color: "#e2e8f0" }}>
              WoodyWorkz AI Product Studio
            </h1>
          </div>
          <p style={{ color: "#7070a0", fontSize: 15 }}>
            Ürün fotoğrafınızı yükleyin — Gemini AI ile analiz edin ve 5 profesyonel çekim oluşturun.
          </p>
        </div>

        {/* Adım göstergesi */}
        <StepBar current={step} />

        {/* Yükleme durumu */}
        {isLoading && (
          <div
            style={{
              background: "#1a1a2e",
              border: "1px solid #7c3aed44",
              borderRadius: 12,
              padding: "16px 24px",
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 24,
            }}
          >
            <Loader2 size={20} color="#7c3aed" style={{ animation: "spin 1s linear infinite" }} />
            <span style={{ color: "#a78bfa", fontWeight: 500 }}>{loadingMsg}</span>
          </div>
        )}

        {/* Adım 0: Görüntü yükle */}
        {step === 0 && (
          <div>
            <ImageUpload onImageSelect={setImageFile} disabled={isLoading} />
            <div style={{ marginTop: 24, display: "flex", justifyContent: "center" }}>
              <PrimaryButton onClick={handleAnalyze} disabled={!imageFile} loading={isLoading}>
                <Sparkles size={18} />
                Analiz Et
              </PrimaryButton>
            </div>
          </div>
        )}

        {/* Adım 1: Analiz sonucu */}
        {step >= 1 && analysis && (
          <div style={{ marginBottom: 24 }}>
            <AnalysisResult analysis={analysis} />
            {step === 1 && (
              <div style={{ marginTop: 20, display: "flex", justifyContent: "center", gap: 12 }}>
                <button
                  onClick={handleReset}
                  style={{
                    background: "transparent",
                    border: "1px solid #4a4a6a",
                    color: "#9090b0",
                    borderRadius: 12,
                    padding: "12px 24px",
                    cursor: "pointer",
                    fontSize: 15,
                  }}
                >
                  Yeni Ürün
                </button>
                <PrimaryButton onClick={handleGenerate} loading={isLoading}>
                  <Sparkles size={18} />
                  5 Çekim Oluştur
                </PrimaryButton>
              </div>
            )}
          </div>
        )}

        {/* Adım 2-3: Üretilen çekimler */}
        {(step === 2 || step === 3) && (
          <div style={{ marginTop: 24 }}>
            <GeneratedPhotos shots={shots} loading={step === 2 && isLoading} />
            {step === 3 && (
              <div style={{ marginTop: 24, display: "flex", justifyContent: "center" }}>
                <button
                  onClick={handleReset}
                  style={{
                    background: "transparent",
                    border: "1px solid #7c3aed",
                    color: "#a78bfa",
                    borderRadius: 12,
                    padding: "12px 28px",
                    cursor: "pointer",
                    fontSize: 15,
                    fontWeight: 600,
                  }}
                >
                  Yeni Ürün Analiz Et
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* CSS animasyon */}
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

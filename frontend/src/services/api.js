/**
 * API İstemci Servisi
 * --------------------
 * FastAPI backend ile iletişim kurar.
 * Tüm endpoint çağrıları buradan yapılır.
 */

import axios from "axios";

const BASE_URL = "/api/v1";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // Görüntü üretimi uzun sürebilir
});

// Hata interceptor
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail || err.message || "Bilinmeyen hata";
    return Promise.reject(new Error(detail));
  }
);

// ─────────────────────────────────────────────────────────────────────────────
// Health
// ─────────────────────────────────────────────────────────────────────────────

export async function checkHealth() {
  const { data } = await api.get("/health");
  return data;
}

// ─────────────────────────────────────────────────────────────────────────────
// Ürün Analizi
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Ürün fotoğrafını analiz eder.
 * @param {File} imageFile  - Yüklenen dosya
 * @param {string} [extraContext] - Ek bağlam (opsiyonel)
 * @returns {Promise<{analysis: object}>}
 */
export async function analyzeProduct(imageFile, extraContext = "") {
  const form = new FormData();
  form.append("image", imageFile);
  if (extraContext) form.append("extra_context", extraContext);

  const { data } = await api.post("/products/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// ─────────────────────────────────────────────────────────────────────────────
// Çekim Promptları
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 5 çekim açısı için prompt üretir.
 * @param {File} imageFile
 * @param {object} analysis - analyzeProduct'tan dönen analiz nesnesi
 * @returns {Promise<{shots: ShotPrompt[]}>}
 */
export async function generateShotPrompts(imageFile, analysis) {
  const form = new FormData();
  form.append("image", imageFile);
  form.append("product_name", analysis.product_name ?? "");
  form.append("category", analysis.category ?? "");
  form.append("style", analysis.style ?? "modern");
  form.append("colors", (analysis.colors ?? []).join(", "));
  form.append("materials", (analysis.materials ?? []).join(", "));
  form.append("brand_tone", analysis.brand_tone ?? "");
  form.append("target_audience", analysis.target_audience ?? "");

  const { data } = await api.post("/products/shot-prompts", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// ─────────────────────────────────────────────────────────────────────────────
// Görüntü Üretimi
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 5 profesyonel çekim üretir.
 * @param {File} imageFile
 * @param {ShotPrompt[]} shots - generateShotPrompts'tan dönen liste
 * @returns {Promise<GenerateResponse>}
 */
export async function generateAllShots(imageFile, shots) {
  const form = new FormData();
  form.append("image", imageFile);
  form.append("shots_json", JSON.stringify(shots));

  const { data } = await api.post("/products/generate", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * Tek çekim üretir.
 * @param {File} imageFile
 * @param {ShotPrompt} shot
 */
export async function generateSingleShot(imageFile, shot) {
  const form = new FormData();
  form.append("image", imageFile);
  form.append("angle", shot.angle);
  form.append("prompt", shot.prompt);
  form.append("negative_prompt", shot.negative_prompt ?? "");

  const { data } = await api.post("/products/generate/single", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

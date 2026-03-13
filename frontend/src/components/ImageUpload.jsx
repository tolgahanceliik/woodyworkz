/**
 * ImageUpload
 * -----------
 * Sürükle-bırak veya tıkla ile görüntü yükleme bileşeni.
 */

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X, ImageIcon } from "lucide-react";

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
const ACCEPTED = { "image/jpeg": [], "image/png": [], "image/webp": [] };

export default function ImageUpload({ onImageSelect, disabled = false }) {
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");

  const onDrop = useCallback(
    (accepted, rejected) => {
      setError("");

      if (rejected.length > 0) {
        const err = rejected[0].errors[0];
        setError(
          err.code === "file-too-large"
            ? "Dosya 10 MB'dan büyük olamaz."
            : "Sadece JPEG, PNG veya WEBP yükleyebilirsiniz."
        );
        return;
      }

      if (accepted.length === 0) return;
      const file = accepted[0];
      const url = URL.createObjectURL(file);
      setPreview(url);
      onImageSelect(file);
    },
    [onImageSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: MAX_SIZE,
    maxFiles: 1,
    disabled,
  });

  const clear = (e) => {
    e.stopPropagation();
    setPreview(null);
    setError("");
    onImageSelect(null);
  };

  return (
    <div style={{ width: "100%" }}>
      <div
        {...getRootProps()}
        style={{
          border: `2px dashed ${isDragActive ? "#7c3aed" : preview ? "#4ade80" : "#4a4a6a"}`,
          borderRadius: 16,
          padding: preview ? 8 : 48,
          textAlign: "center",
          cursor: disabled ? "not-allowed" : "pointer",
          background: isDragActive ? "rgba(124,58,237,0.08)" : "#16162a",
          transition: "all 0.2s",
          position: "relative",
          minHeight: 200,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <input {...getInputProps()} />

        {preview ? (
          <>
            <img
              src={preview}
              alt="Yüklenen ürün"
              style={{
                maxHeight: 320,
                maxWidth: "100%",
                borderRadius: 12,
                objectFit: "contain",
              }}
            />
            {!disabled && (
              <button
                onClick={clear}
                style={{
                  position: "absolute",
                  top: 12,
                  right: 12,
                  background: "rgba(239,68,68,0.85)",
                  border: "none",
                  borderRadius: "50%",
                  width: 32,
                  height: 32,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  color: "#fff",
                }}
              >
                <X size={16} />
              </button>
            )}
          </>
        ) : (
          <div>
            {isDragActive ? (
              <Upload size={48} color="#7c3aed" style={{ margin: "0 auto 16px" }} />
            ) : (
              <ImageIcon size={48} color="#4a4a6a" style={{ margin: "0 auto 16px" }} />
            )}
            <p style={{ color: "#9090b0", fontSize: 16, marginBottom: 8 }}>
              {isDragActive
                ? "Bırakın..."
                : "Ürün fotoğrafını sürükleyin veya tıklayın"}
            </p>
            <p style={{ color: "#5a5a7a", fontSize: 13 }}>
              JPEG, PNG, WEBP · Maks 10 MB
            </p>
          </div>
        )}
      </div>

      {error && (
        <p style={{ color: "#f87171", fontSize: 13, marginTop: 8 }}>{error}</p>
      )}
    </div>
  );
}

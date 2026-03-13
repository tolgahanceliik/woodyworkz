/**
 * MultiDropzone
 * -------------
 * 1-4 fotoğraf yükleyen sürükle-bırak bileşeni.
 * Her dosya önizleme kartı olarak listelenir ve tek tek silinebilir.
 */

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X, ImageIcon, CheckCircle } from "lucide-react";

const MAX = 4;
const MAX_SIZE = 10 * 1024 * 1024;
const ACCEPTED = { "image/jpeg": [], "image/png": [], "image/webp": [] };

// ── küçük yardımcı ─────────────────────────────────────────────────────────

function PreviewCard({ file, index, onRemove, disabled }) {
  const url = URL.createObjectURL(file);
  return (
    <div
      style={{
        position: "relative",
        width: 110,
        height: 110,
        borderRadius: 12,
        overflow: "hidden",
        border: "2px solid #4ade8088",
        flexShrink: 0,
      }}
    >
      <img
        src={url}
        alt={`Ürün ${index + 1}`}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
      {/* index rozeti */}
      <div
        style={{
          position: "absolute",
          top: 4,
          left: 4,
          background: "#7c3aed",
          color: "#fff",
          fontSize: 11,
          fontWeight: 700,
          borderRadius: 20,
          padding: "1px 7px",
        }}
      >
        #{index + 1}
      </div>
      {/* kaldır butonu */}
      {!disabled && (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(index); }}
          style={{
            position: "absolute",
            top: 4,
            right: 4,
            background: "rgba(239,68,68,0.9)",
            border: "none",
            borderRadius: "50%",
            width: 22,
            height: 22,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            color: "#fff",
          }}
        >
          <X size={12} />
        </button>
      )}
    </div>
  );
}

// ── Ana bileşen ─────────────────────────────────────────────────────────────

export default function MultiDropzone({ files, onChange, disabled = false }) {
  const remaining = MAX - files.length;

  const onDrop = useCallback(
    (accepted) => {
      const merged = [...files, ...accepted].slice(0, MAX);
      onChange(merged);
    },
    [files, onChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: MAX_SIZE,
    maxFiles: remaining,
    disabled: disabled || remaining === 0,
    multiple: true,
  });

  const remove = (idx) => {
    const updated = files.filter((_, i) => i !== idx);
    onChange(updated);
  };

  const hasFiles = files.length > 0;

  return (
    <div>
      {/* Önizleme satırı */}
      {hasFiles && (
        <div
          style={{
            display: "flex",
            gap: 10,
            flexWrap: "wrap",
            marginBottom: 12,
          }}
        >
          {files.map((f, i) => (
            <PreviewCard
              key={`${f.name}-${i}`}
              file={f}
              index={i}
              onRemove={remove}
              disabled={disabled}
            />
          ))}
        </div>
      )}

      {/* Drop alanı — dosya doluysa küçük, değilse büyük */}
      {remaining > 0 && (
        <div
          {...getRootProps()}
          style={{
            border: `2px dashed ${isDragActive ? "#7c3aed" : "#4a4a6a"}`,
            borderRadius: 14,
            padding: hasFiles ? "16px 20px" : "52px 20px",
            textAlign: "center",
            cursor: disabled ? "not-allowed" : "pointer",
            background: isDragActive ? "rgba(124,58,237,0.08)" : "#16162a",
            transition: "all 0.2s",
          }}
        >
          <input {...getInputProps()} />
          {isDragActive ? (
            <Upload size={32} color="#7c3aed" style={{ margin: "0 auto 10px" }} />
          ) : (
            <ImageIcon size={hasFiles ? 22 : 40} color="#4a4a6a" style={{ margin: "0 auto 10px" }} />
          )}
          <p style={{ color: "#8080a0", fontSize: 14, marginBottom: 4 }}>
            {isDragActive
              ? "Bırakın..."
              : hasFiles
              ? `+ ${remaining} fotoğraf daha ekleyebilirsiniz`
              : "Ürün fotoğraflarını sürükleyin veya tıklayın"}
          </p>
          {!hasFiles && (
            <p style={{ color: "#5a5a7a", fontSize: 12 }}>
              1-4 adet · JPEG, PNG, WEBP · Maks 10 MB/adet
            </p>
          )}
        </div>
      )}

      {/* Sayaç */}
      {hasFiles && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            marginTop: 8,
            color: "#4ade80",
            fontSize: 13,
          }}
        >
          <CheckCircle size={14} />
          {files.length} fotoğraf seçildi
          {remaining > 0 && (
            <span style={{ color: "#6060a0" }}>· {remaining} daha eklenebilir</span>
          )}
        </div>
      )}
    </div>
  );
}

import React, { useState, useRef } from 'react';
import {
  Cpu,
  Play,
  UploadCloud,
  Zap
} from 'lucide-react';
import { DetectionResult } from '../types';
import { apiClient } from '../api/client';
import { SAMPLE_ROAD_IMAGES } from '../data/mockData';
import { EvidenceViewer } from '../components/EvidenceViewer';
import { NotificationBanner } from '../components/NotificationBanner';

export const DetectionStudio: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string>(SAMPLE_ROAD_IMAGES[0].url);
  const [imageTitle, setImageTitle] = useState<string>(SAMPLE_ROAD_IMAGES[0].title);
  const [minConfidence, setMinConfidence] = useState<number>(0.65);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
  const [gapNotice, setGapNotice] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Run detection on currently selected image
  const handleRunInference = async (imageSrc = selectedImage) => {
    setIsProcessing(true);
    setErrorMessage(null);
    setGapNotice(null);

    try {
      // Convert data URL or blob to File object
      const blob = await fetch(imageSrc).then(r => r.blob());
      const file = new File([blob], 'road-sample.jpg', { type: 'image/jpeg' });

      const response = await apiClient.detectPotholesInImage(file, minConfidence);

      setDetectionResult(response.result);

      if (response.backendGapNotice) {
        setGapNotice(response.backendGapNotice);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Detection processing failed';
      setErrorMessage(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle user uploaded custom image
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setErrorMessage('Please select a valid image file (.jpg, .png, .jpeg).');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      setSelectedImage(dataUrl);
      setImageTitle(`Uploaded Road Image (${file.name})`);
      setDetectionResult(null);
      // Auto run detection
      handleRunInference(dataUrl);
    };
    reader.readAsDataURL(file);
  };

  // Handle preset sample selection
  const handleSelectPreset = (preset: typeof SAMPLE_ROAD_IMAGES[0]) => {
    setSelectedImage(preset.url);
    setImageTitle(preset.title);
    setDetectionResult(null);
    handleRunInference(preset.url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Pothole Detection Studio</h1>
          <p className="page-subtitle">
            Upload custom forward-camera road imagery or test benchmark samples against candidate detector architectures.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn btn-primary"
            onClick={() => handleRunInference()}
            disabled={isProcessing}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Play size={16} className={isProcessing ? 'spinner' : ''} />
            <span>{isProcessing ? 'Analyzing Frame...' : 'Run Detection'}</span>
          </button>
        </div>
      </div>

      {/* Backend Gap / Model Status Notice */}
      {gapNotice && (
        <NotificationBanner
          type="info"
          title="Contract Notice // Endpoint Status"
          message={gapNotice}
          actionText="View Contract Specs"
          onAction={() => window.open('https://github.com/viraj-1808/RoadGuard/blob/main/docs/API_CONTRACTS.md', '_blank')}
          onDismiss={() => setGapNotice(null)}
        />
      )}

      {errorMessage && (
        <NotificationBanner
          type="error"
          title="Inference Error"
          message={errorMessage}
          onDismiss={() => setErrorMessage(null)}
        />
      )}

      {/* Layout Grid: Controls & Presets (Left) + Detection Stage (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>
        {/* Left Column: Input Source, Presets, Settings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* File Upload Dropzone */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>
              Upload Road Imagery
            </h3>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept="image/*"
              style={{ display: 'none' }}
            />

            <div
              className="dropzone"
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
            >
              <div className="dropzone-icon">
                <UploadCloud size={28} />
              </div>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                  Click or drag road image here
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                  Supports JPEG, PNG, WEBP (Automotive 1080p / 720p Recommended)
                </div>
              </div>
            </div>
          </div>

          {/* Preset Benchmark Road Images */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>
              Benchmark Corridor Presets
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', marginBottom: '14px' }}>
              Standard evaluation frames from Indian arterial highways and urban corridors.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {SAMPLE_ROAD_IMAGES.map((preset) => {
                const isSelected = selectedImage === preset.url;
                return (
                  <div
                    key={preset.id}
                    onClick={() => handleSelectPreset(preset)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-md)',
                      background: isSelected ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                      border: `1px solid ${isSelected ? 'var(--emerald)' : 'var(--border-subtle)'}`,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div
                      style={{
                        width: '56px',
                        height: '36px',
                        borderRadius: '4px',
                        overflow: 'hidden',
                        flexShrink: 0,
                        border: '1px solid var(--border-medium)'
                      }}
                    >
                      <img
                        src={preset.url}
                        alt={preset.title}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: '0.825rem',
                          fontWeight: 600,
                          color: isSelected ? 'var(--emerald)' : 'var(--text-main)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                      >
                        {preset.title}
                      </div>
                      <div style={{ fontSize: '0.725rem', color: 'var(--text-subtle)' }}>
                        Expected Potholes: {preset.expectedBboxes.length} | Baseline Conf: {Math.round(preset.confidence * 100)}%
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Model Inference Parameters */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '14px' }}>
              Inference Hyperparameters
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label className="form-label">Confidence Acceptance Threshold</label>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--emerald)', fontSize: '0.8rem' }}>
                    {Math.round(minConfidence * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.30"
                  max="0.95"
                  step="0.05"
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--emerald)', cursor: 'pointer' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-subtle)', marginTop: '4px' }}>
                  <span>High Recall (30%)</span>
                  <span>Balanced (65%)</span>
                  <span>High Precision (95%)</span>
                </div>
              </div>

              <div style={{ padding: '10px 12px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, color: 'var(--indigo)', marginBottom: '4px' }}>
                  <Cpu size={14} />
                  <span>Architecture: YOLO26s (Primary Candidate)</span>
                </div>
                <div>Per D-004 &amp; D-007: Inference runs via project-owned Model Adapter conforming strictly to Detection contract.</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Interactive Detection Canvas & Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
                  Detection Output Canvas
                </h3>
                <div style={{ fontSize: '0.775rem', color: 'var(--text-subtle)' }}>
                  {imageTitle}
                </div>
              </div>

              {detectionResult && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--emerald)' }}>
                  <Zap size={14} />
                  <span>Latency: {detectionResult.processing_time_ms} ms</span>
                </div>
              )}
            </div>

            {/* Evidence & Canvas Viewer */}
            <EvidenceViewer
              imageUrl={selectedImage}
              bboxes={
                detectionResult
                  ? detectionResult.detections.map(d => d.bbox)
                  : (SAMPLE_ROAD_IMAGES.find(p => p.url === selectedImage)?.expectedBboxes || [])
              }
              confidence={
                detectionResult && detectionResult.detections.length > 0
                  ? detectionResult.detections[0].confidence
                  : 0.91
              }
              label="pothole"
            />
          </div>

          {/* Detections Breakdown List */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>
                Detected Object Instances
              </h3>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  background: 'var(--emerald-subtle)',
                  color: 'var(--emerald)',
                  fontWeight: 600
                }}
              >
                {detectionResult ? detectionResult.detections.length : 1} Pothole(s) Identified
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(detectionResult ? detectionResult.detections : [
                {
                  class: 'pothole',
                  confidence: 0.932,
                  bbox: [270, 410, 490, 520] as [number, number, number, number],
                  frame_id: 'sample-frame-1',
                  capture_timestamp: new Date().toISOString()
                }
              ]).map((det, index) => {
                const [x1, y1, x2, y2] = det.bbox;
                return (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'var(--bg-surface)',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.85rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span
                        style={{
                          width: '24px',
                          height: '24px',
                          borderRadius: '50%',
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: 'var(--emerald)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          fontFamily: 'var(--font-mono)'
                        }}
                      >
                        {index + 1}
                      </span>
                      <div>
                        <div style={{ fontWeight: 600, color: '#fff' }}>
                          Class: <span style={{ color: 'var(--emerald)' }}>{det.class}</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-subtle)' }}>
                          BBox: [{x1}, {y1}, {x2}, {y2}] ({x2 - x1}×{y2 - y1} px)
                        </div>
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, color: 'var(--emerald)', fontFamily: 'var(--font-mono)' }}>
                        {Math.round(det.confidence * 100)}%
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>
                        Confidence
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

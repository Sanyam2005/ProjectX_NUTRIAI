import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, ImagePlus, Keyboard, X } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { compressImage } from "@/lib/utils";
import type { AnalyzeResult } from "@/types";

const EMPTY_DRAFT: AnalyzeResult = {
  meal_name: "Meal",
  meal_type: "lunch",
  image_url: null,
  confidence: 1,
  ingredients: [],
  totals: {
    calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0,
    fiber_g: 0, sugar_g: 0, sodium_mg: 0,
  },
};

export function MealUploadPage() {
  const nav = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accept = useCallback(async (raw: File) => {
    setError(null);
    if (!raw.type.startsWith("image/")) {
      setError("Please choose an image.");
      return;
    }
    const compressed = await compressImage(raw, 1600, 0.85);
    setFile(compressed);
    setPreview(URL.createObjectURL(compressed));
  }, []);

  const onSelected = (f: FileList | null) => {
    if (!f || f.length === 0) return;
    void accept(f[0]);
  };

  const analyze = () => {
    if (!file) return;
    // Pass the file through router state; the analyzing page does the call.
    nav("/app/analyzing", { state: { file } });
  };

  const logManually = () => {
    // Hand an empty AnalyzeResult to the review page so the user can build
    // a meal from scratch using the ingredient picker — no AI call.
    nav("/app/result", { state: { result: EMPTY_DRAFT } });
  };

  return (
    <div className="pt-1">
      <PageHeader title="Add a meal" subtitle="Snap a photo or log manually" />

      <Card padded className="space-y-4">
        {preview ? (
          <div className="relative">
            <img src={preview} alt="" className="aspect-[4/3] w-full rounded-2xl object-cover" />
            <button
              onClick={() => {
                setPreview(null);
                setFile(null);
              }}
              className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-black/60 text-white backdrop-blur"
              aria-label="Remove"
            >
              <X size={18} />
            </button>
          </div>
        ) : (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              onSelected(e.dataTransfer.files);
            }}
            className={`flex aspect-[4/3] w-full flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed text-center transition ${
              dragOver
                ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
                : "border-surface-ring bg-surface-muted/40 dark:border-white/10 dark:bg-white/5"
            }`}
          >
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white text-brand-600 shadow-card dark:bg-white/10 dark:text-brand-300">
              <ImagePlus size={24} />
            </div>
            <div className="px-6">
              <p className="font-display text-base font-bold">Drag a meal photo here</p>
              <p className="text-xs text-ink-subtle">or use a button below</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="secondary"
            onClick={() => cameraRef.current?.click()}
            leading={<Camera size={18} />}
            full
          >
            Camera
          </Button>
          <Button
            variant="secondary"
            onClick={() => fileRef.current?.click()}
            leading={<ImagePlus size={18} />}
            full
          >
            Gallery
          </Button>
        </div>

        <Button variant="primary" onClick={analyze} disabled={!file} full>
          Analyze with NutriAI
        </Button>

        {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>}
      </Card>

      <div className="mt-3 flex items-center gap-2">
        <div className="h-px flex-1 bg-surface-ring dark:bg-white/10" />
        <span className="text-[10px] uppercase tracking-wider text-ink-subtle">or</span>
        <div className="h-px flex-1 bg-surface-ring dark:bg-white/10" />
      </div>

      <Button
        variant="ghost"
        onClick={logManually}
        leading={<Keyboard size={18} />}
        full
        className="mt-3"
      >
        Log without a photo
      </Button>

      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => onSelected(e.target.files)}
      />
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => onSelected(e.target.files)}
      />

      <p className="mt-4 text-center text-xs text-ink-subtle">
        Photos are compressed in your browser before upload — typically under 400 KB.
      </p>
    </div>
  );
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface RoboflowPrediction {
  class: string;
  confidence: number;
  x: number;
  y: number;
  width: number;
  height: number;
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface DefectInstance {
  defect_class: string;
  confidence: number;
  bbox: BoundingBox;
  is_confirmed: boolean;
  status_text: string;
}

export interface OnionCheck {
  criterion: string;
  value: string;
  limit: string;
  status: 'PASS' | 'FAIL';
}

export interface OnionInstance {
  id: string;
  bbox: BoundingBox;
  confidence: number;
  defects: DefectInstance[];
  diameter_px: number;
  diameter_mm: number | null;
  measurement_method: string | null;
  grade: 'GRADE_A' | 'URS' | 'NON_COMPLIANT' | null;
  reasons: string[];
  checks: OnionCheck[];
}

export interface CalibrationResult {
  detected: boolean;
  ref_type: string;
  ref_size_mm: number;
  ref_pixel_width: number | null;
  pixels_per_mm: number | null;
  ref_bbox?: {
    xmin: number;
    ymin: number;
    xmax: number;
    ymax: number;
    width: number;
    height: number;
  } | null;
  message: string;
}

export interface ImageAnalysisResult {
  image_id: string;
  filename: string;
  timestamp: string;
  image_width: number;
  image_height: number;
  calibration: CalibrationResult;
  onions: OnionInstance[];
  raw_predictions: RoboflowPrediction[];
  summary: {
    total_onions: number;
    grade_a_count: number;
    urs_count: number;
    non_compliant_count: number;
    defect_free_count: number;
  };
  warnings: string[];
}

export interface BatchAnalysisResult {
  batch_id: string;
  timestamp: string;
  total_images: number;
  total_onions: number;
  grade_a_count: number;
  grade_a_percent: number;
  urs_count: number;
  urs_percent: number;
  non_compliant_count: number;
  non_compliant_percent: number;
  stats: {
    mean: number | null;
    median: number | null;
    min: number | null;
    max: number | null;
  };
  defect_counts: Record<string, number>;
  images: ImageAnalysisResult[];
  warnings: string[];
}

export interface GradeLimits {
  min_diameter_mm: number;
  max_diameter_mm: number;
  max_staining_percent: number;
  max_sunburn_percent: number;
  sprouted_allowed: boolean;
  spoiled_allowed: boolean;
  double_split_allowed: boolean;
  black_smut_allowed: boolean;
}

export interface GradingStandard {
  standard_name: string;
  description?: string;
  grade_a: GradeLimits;
  urs: GradeLimits;
}

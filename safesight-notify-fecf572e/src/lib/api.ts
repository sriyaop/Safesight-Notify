const getApiBase = () => {
  const stored = localStorage.getItem("safesight_api_url");
  return stored || "http://127.0.0.1:5000";
};

export const API = {
  get base() { return getApiBase(); },
  videoFeed: (camera: string) => `${getApiBase()}/video_feed/${camera}`,
  get cameraResults() { return `${getApiBase()}/camera_results`; },
  get metrics() { return `${getApiBase()}/metrics`; },
  get alerts() { return `${getApiBase()}/alerts`; },
  get children() { return `${getApiBase()}/children`; },
};

export interface Detection {
  name: string;
  confidence: number;
  face: string;
  camera: string;
  timestamp: string;
}

export interface Metrics {
  missing_children: number;
  detections_today: number;
  active_alerts: number;
  high_matches?: number;
}

// 🔥 FIXED: convert backend → frontend expected format
export async function fetchCameraResults() {
  const res = await fetch(API.cameraResults);
  if (!res.ok) throw new Error("Failed to fetch camera results");

  const data = await res.json();

  // 🔥 convert flat list → grouped by camera
  const grouped: Record<string, any[]> = {};

  data.forEach((item: any) => {
    if (!grouped[item.camera]) {
      grouped[item.camera] = [];
    }

    grouped[item.camera].push({
      name: item.name,
      confidence: item.confidence,
      face: item.face,
      db_image: ""
    });
  });

  return grouped;
}

// 🔥 alerts
export async function fetchAlerts() {
  const res = await fetch(API.alerts);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

// 🔥 children
export async function fetchChildren() {
  const res = await fetch(API.children);
  if (!res.ok) throw new Error("Failed to fetch children");
  return res.json();
}

// 🔥 metrics
export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(API.metrics);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export function setApiUrl(url: string) {
  localStorage.setItem("safesight_api_url", url);
}



// // Flask backend API configuration
// const getApiBase = () => {
//   const stored = localStorage.getItem("safesight_api_url");
//   return stored || import.meta.env.VITE_FLASK_API_URL || "http://127.0.0.1:5000";
// };

// export const API = {
//   get base() { return getApiBase(); },
//   videoFeed: (camera: string) => `${getApiBase()}/video_feed/${camera}`,
//   get cameraResults() { return `${getApiBase()}/camera_results`; },
//   get metrics() { return `${getApiBase()}/metrics`; },
//   get addChild() { return `${getApiBase()}/add_child`; },
// };

// export interface CameraResult {
//   name: string;
//   confidence: number;
//   face: string; // base64
//   db_image: string; // base64
// }

// export interface CameraResults {
//   [cameraName: string]: CameraResult[];
// }

// export interface Metrics {
//   missing_children: number;
//   detections_today: number;
//   active_alerts: number;
// }

// export async function fetchCameraResults(): Promise<CameraResults> {
//   const res = await fetch(API.cameraResults);
//   if (!res.ok) throw new Error("Failed to fetch camera results");
//   return res.json();
// }

// export async function fetchMetrics(): Promise<Metrics> {
//   const res = await fetch(API.metrics);
//   if (!res.ok) throw new Error("Failed to fetch metrics");
//   return res.json();
// }

// export async function addChild(formData: FormData): Promise<{ success: boolean; message?: string }> {
//   const res = await fetch(API.addChild, {
//     method: "POST",
//     body: formData,
//   });
//   if (!res.ok) throw new Error("Failed to add child");
//   return res.json();
// }

// export function setApiUrl(url: string) {
//   localStorage.setItem("safesight_api_url", url);
// }

// export function getStoredApiUrl(): string {
//   return getApiBase();
// }

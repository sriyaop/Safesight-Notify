import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchCameraResults, fetchMetrics, addChild, type CameraResults, type Metrics } from "@/lib/api";

export function useCameraResults(pollInterval = 2000) {
  return useQuery<CameraResults>({
    queryKey: ["cameraResults"],
    queryFn: fetchCameraResults,
    refetchInterval: pollInterval,
    retry: 1,
    staleTime: 1000,
  });
}

export function useMetrics(pollInterval = 5000) {
  return useQuery<Metrics>({
    queryKey: ["metrics"],
    queryFn: fetchMetrics,
    refetchInterval: pollInterval,
    retry: 1,
    staleTime: 3000,
  });
}

export function useAddChild() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: addChild,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["metrics"] });
      queryClient.invalidateQueries({ queryKey: ["cameraResults"] });
    },
  });
}

// Flatten camera results into a single detection list with timestamps
export interface FlatDetection {
  name: string;
  confidence: number;
  camera: string;
  face: string;
  db_image: string;
  timestamp: string;
}

export function flattenResults(data: CameraResults | undefined): FlatDetection[] {
  if (!data) return [];
  const now = new Date();
  const results: FlatDetection[] = [];
  for (const [camera, detections] of Object.entries(data)) {
    for (const d of detections) {
      results.push({
        ...d,
        camera,
        timestamp: now.toLocaleTimeString("en-IN", { hour12: false }),
      });
    }
  }
  return results.sort((a, b) => b.confidence - a.confidence);
}

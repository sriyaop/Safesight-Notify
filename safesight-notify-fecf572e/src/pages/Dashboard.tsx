import { Users, Bell, Camera, Eye, Shield, Activity, AlertTriangle } from "lucide-react";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { CameraFeed } from "@/components/dashboard/CameraFeed";
import { DetectionLog } from "@/components/dashboard/DetectionLog";
import { motion } from "framer-motion";
import { useMetrics, useCameraResults, flattenResults } from "@/hooks/use-api";
import { Skeleton } from "@/components/ui/skeleton";

const cameras = [
  { name: "peoplelink", label: "PeopleLink Camera" },
  { name: "laptop", label: "Laptop Camera" },
  { name: "zebronics", label: "Zebronics Webcam" },
];

export default function Dashboard() {
  const { data: metrics, isLoading: metricsLoading, isError: metricsError } = useMetrics();
  const { data: cameraResults, isError: resultsError } = useCameraResults();

  const allDetections = flattenResults(cameraResults);
  const highConfidenceMatches = allDetections.filter(d => d.confidence >= 70);

  // Determine camera online status by checking if the feed endpoint is reachable
  const cameraHasResults = (name: string) => {
    if (!cameraResults) return false;
    return name in cameraResults;
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-base font-semibold">Command Center</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Real-time surveillance monitoring & face match detection
          </p>
        </div>
        <div className="flex items-center gap-2 card-surface px-3 py-1.5">
          {metricsError || resultsError ? (
            <>
              <AlertTriangle className="h-3 w-3 text-warning" />
              <span className="text-xs text-warning">Backend unreachable</span>
            </>
          ) : (
            <>
              <Activity className="h-3 w-3 text-success" />
              <span className="text-xs text-muted-foreground">All systems operational</span>
            </>
          )}
        </div>
      </motion.div>

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metricsLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[104px] rounded-lg" />
          ))
        ) : (
          <>
            <MetricCard
              title="Missing Children"
              value={metrics?.missing_children ?? 0}
              icon={Users}
              variant="destructive"
              trend="In database"
            />
            <MetricCard
              title="Active Alerts"
              value={metrics?.active_alerts ?? 0}
              icon={Bell}
              variant="warning"
              trend="Pending verification"
            />
            <MetricCard
              title="Active Cameras"
              value={cameras.length}
              icon={Camera}
              variant="success"
              trend={`${cameras.length} feeds configured`}
            />
            <MetricCard
              title="Detections Today"
              value={metrics?.detections_today ?? 0}
              icon={Eye}
              variant="primary"
              trend="Face detections"
            />
          </>
        )}
      </div>

      {/* Camera Grid + Detection Log */}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            {cameras.slice(0, 2).map((cam) => (
              <CameraFeed key={cam.name} name={cam.name} label={cam.label} isOnline={true} />
            ))}
          </div>
          <CameraFeed name={cameras[2].name} label={cameras[2].label} isOnline={true} />
        </div>
        <div className="lg:col-span-1">
          <DetectionLog />
        </div>
      </div>

      {/* Recent Matches — from real API */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-surface"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
          <div className="flex items-center gap-2">
            <Shield className="h-3.5 w-3.5 text-primary" />
            <span className="text-sm font-medium">Recent Matches</span>
          </div>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
            {highConfidenceMatches.length} match{highConfidenceMatches.length !== 1 ? "es" : ""}
          </span>
        </div>
        {highConfidenceMatches.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            No matches detected yet. Monitoring live feeds…
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
            {highConfidenceMatches.slice(0, 6).map((match, i) => (
              <div key={i} className="card-surface p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{match.name}</span>
                  <span className="text-xs font-mono font-medium text-destructive">
                    {match.confidence.toFixed(1)}%
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Detected</p>
                    <img
                      src={`data:image/jpeg;base64,${match.face}`}
                      alt="Detected face"
                      className="w-full aspect-square object-cover rounded border border-border/50"
                    />
                  </div>
                  <div className="space-y-1">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Database</p>
                    <img
                      src={`data:image/jpeg;base64,${match.db_image}`}
                      alt="Database match"
                      className="w-full aspect-square object-cover rounded border border-border/50"
                    />
                  </div>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{match.camera}</span>
                  <span className="font-mono">{match.timestamp}</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-1">
                  <div
                    className="bg-destructive h-1 rounded-full transition-all"
                    style={{ width: `${match.confidence}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}

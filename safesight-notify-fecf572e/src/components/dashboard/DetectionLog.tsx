import { motion } from "framer-motion";
import { AlertTriangle, Clock } from "lucide-react";
import { useCameraResults, flattenResults } from "@/hooks/use-api";
import { Skeleton } from "@/components/ui/skeleton";

const statusFromConfidence = (c: number): "matched" | "pending" | "dismissed" => {
  if (c >= 80) return "matched";
  if (c >= 65) return "pending";
  return "dismissed";
};

const statusStyles = {
  matched: "bg-destructive/10 text-destructive",
  pending: "bg-warning/10 text-warning",
  dismissed: "bg-muted text-muted-foreground",
};

export function DetectionLog() {
  const { data, isLoading, isError } = useCameraResults();
  const detections = flattenResults(data);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-surface"
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-3.5 w-3.5 text-warning" />
          <span className="text-sm font-medium">Live Detection Log</span>
        </div>
        <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
          {isError ? "Offline" : "Real-time"}
        </span>
      </div>
      <div className="divide-y divide-border/30">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="px-4 py-3">
              <Skeleton className="h-8 w-full" />
            </div>
          ))
        ) : isError ? (
          <div className="p-6 text-center text-sm text-muted-foreground">
            Unable to connect to backend
          </div>
        ) : detections.length === 0 ? (
          <div className="p-6 text-center text-sm text-muted-foreground">
            No detections yet. Monitoring…
          </div>
        ) : (
          detections.slice(0, 10).map((d, i) => {
            const status = statusFromConfidence(d.confidence);
            return (
              <div key={i} className="flex items-center gap-4 px-4 py-3 hover:bg-accent/30 transition-colors">
                <div className="flex items-center gap-1.5 text-muted-foreground shrink-0">
                  <Clock className="h-3 w-3" />
                  <span className="text-xs font-mono">{d.timestamp}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{d.name}</p>
                  <p className="text-xs text-muted-foreground">{d.camera}</p>
                </div>
                <span className="text-xs font-mono font-medium text-foreground">
                  {d.confidence.toFixed(1)}%
                </span>
                <span className={`text-[10px] font-medium uppercase tracking-wider px-2 py-0.5 rounded ${statusStyles[status]}`}>
                  {status}
                </span>
              </div>
            );
          })
        )}
      </div>
    </motion.div>
  );
}

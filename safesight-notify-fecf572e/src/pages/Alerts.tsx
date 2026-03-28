import { Bell, CheckCircle2, XCircle, Clock, MapPin } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCameraResults, flattenResults } from "@/hooks/use-api";
import { Skeleton } from "@/components/ui/skeleton";

const ALERT_THRESHOLD = 65;

const statusConfig = {
  new: { style: "bg-destructive/10 text-destructive border-destructive/20", icon: Bell },
  verified: { style: "bg-success/10 text-success border-success/20", icon: CheckCircle2 },
  dismissed: { style: "bg-muted text-muted-foreground border-border", icon: XCircle },
  escalated: { style: "bg-warning/10 text-warning border-warning/20", icon: Clock },
};

const cameraLocations: Record<string, string> = {
  peoplelink: "Main Entrance",
  laptop: "Office Desk",
  zebronics: "Corridor",
};

export default function Alerts() {
  const { data, isLoading, isError } = useCameraResults();
  const detections = flattenResults(data).filter(d => d.confidence >= ALERT_THRESHOLD);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold">Alert Center</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {detections.length} active alert{detections.length !== 1 ? "s" : ""} from live detection
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))
        ) : isError ? (
          <div className="card-surface p-8 text-center text-sm text-muted-foreground">
            Unable to connect to backend. Check your API settings.
          </div>
        ) : detections.length === 0 ? (
          <div className="card-surface p-8 text-center text-sm text-muted-foreground">
            No alerts at this time. System is monitoring live feeds.
          </div>
        ) : (
          detections.map((alert, i) => {
            const isHighConfidence = alert.confidence >= 80;
            const config = statusConfig[isHighConfidence ? "new" : "escalated"];
            const StatusIcon = config.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`card-surface p-4 ${isHighConfidence ? "glow-destructive" : ""}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="flex gap-2 shrink-0">
                      <img
                        src={`data:image/jpeg;base64,${alert.face}`}
                        alt="Detected face"
                        className="h-12 w-12 rounded object-cover border border-border/50"
                      />
                      <img
                        src={`data:image/jpeg;base64,${alert.db_image}`}
                        alt="DB match"
                        className="h-12 w-12 rounded object-cover border border-border/50"
                      />
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{alert.name}</span>
                        <Badge variant="outline" className={`text-[10px] uppercase tracking-wider ${config.style}`}>
                          {isHighConfidence ? "High Match" : "Review"}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="font-mono">{alert.confidence.toFixed(1)}% match</span>
                        <span>·</span>
                        <span>{alert.camera}</span>
                        <span>·</span>
                        <div className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          <span>{cameraLocations[alert.camera] || alert.camera}</span>
                        </div>
                      </div>
                      <p className="text-[10px] font-mono text-muted-foreground">{alert.timestamp}</p>
                    </div>
                  </div>
                  {isHighConfidence && (
                    <div className="flex items-center gap-2 shrink-0">
                      <Button size="sm" variant="outline" className="h-7 text-xs border-border/50">
                        Dismiss
                      </Button>
                      <Button size="sm" className="h-7 text-xs bg-destructive hover:bg-destructive/90">
                        Verify
                      </Button>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}

import { Camera, Wifi, WifiOff } from "lucide-react";
import { motion } from "framer-motion";
import { API } from "@/lib/api";

interface CameraFeedProps {
  name: string;
  label: string;
  isOnline?: boolean;
}

export function CameraFeed({ name, label, isOnline = false }: CameraFeedProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-surface overflow-hidden"
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
        <div className="flex items-center gap-2">
          <Camera className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-sm font-medium">{label}</span>
        </div>
        <div className="flex items-center gap-1.5">
          {isOnline ? (
            <>
              <div className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-subtle" />
              <Wifi className="h-3 w-3 text-success" />
            </>
          ) : (
            <>
              <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
              <WifiOff className="h-3 w-3 text-muted-foreground" />
            </>
          )}
        </div>
      </div>
      <div className="relative aspect-video bg-secondary/50 flex items-center justify-center">
        {isOnline ? (
          <img
            src={API.videoFeed(name)}
            alt={`${label} feed`}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : null}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-muted-foreground">
          <Camera className="h-8 w-8 opacity-20" />
          <span className="text-xs opacity-50">
            {isOnline ? "Connecting to feed..." : "Camera Offline"}
          </span>
        </div>
        {isOnline && (
          <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-destructive/90 px-2 py-1 rounded text-[10px] font-medium text-destructive-foreground uppercase tracking-wider">
            <div className="h-1.5 w-1.5 rounded-full bg-destructive-foreground animate-pulse-subtle" />
            Live
          </div>
        )}
      </div>
    </motion.div>
  );
}

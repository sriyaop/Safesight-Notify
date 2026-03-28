import { BarChart3, TrendingUp, Clock, Target } from "lucide-react";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useMetrics, useCameraResults, flattenResults } from "@/hooks/use-api";
import { Skeleton } from "@/components/ui/skeleton";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="card-elevated p-3 text-xs space-y-1">
      <p className="font-medium">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-muted-foreground">
          {p.name}: <span className="font-mono font-medium text-foreground">{p.value}</span>
        </p>
      ))}
    </div>
  );
};

export default function Analytics() {
  const { data: metrics, isLoading: metricsLoading } = useMetrics();
  const { data: cameraResults, isLoading: resultsLoading } = useCameraResults(5000);
  const allDetections = flattenResults(cameraResults);

  const highMatches = allDetections.filter(d => d.confidence >= 80).length;
  const matchRate = allDetections.length > 0
    ? ((highMatches / allDetections.length) * 100).toFixed(1)
    : "0";

  // Build per-camera breakdown for chart
  const cameraData = cameraResults
    ? Object.entries(cameraResults).map(([name, results]) => ({
        camera: name,
        detections: results.length,
        matches: results.filter(r => r.confidence >= 80).length,
      }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-base font-semibold">Analytics & Insights</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Live detection patterns and system performance
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metricsLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[104px] rounded-lg" />
          ))
        ) : (
          <>
            <MetricCard title="Total Detections" value={metrics?.detections_today ?? 0} icon={BarChart3} variant="primary" trend="Today" />
            <MetricCard title="High Matches" value={highMatches} icon={Target} variant="destructive" trend={`${matchRate}% match rate`} />
            <MetricCard title="Missing in DB" value={metrics?.missing_children ?? 0} icon={Clock} variant="success" trend="Database records" />
            <MetricCard title="Active Alerts" value={metrics?.active_alerts ?? 0} icon={TrendingUp} variant="warning" trend="Pending" />
          </>
        )}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-surface p-4"
        >
          <div className="mb-4">
            <h3 className="text-sm font-medium">Detections by Camera</h3>
            <p className="text-xs text-muted-foreground">Current session breakdown</p>
          </div>
          {resultsLoading ? (
            <Skeleton className="h-[240px] w-full" />
          ) : cameraData.length === 0 ? (
            <div className="h-[240px] flex items-center justify-center text-sm text-muted-foreground">
              No data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={cameraData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(240 3.7% 15.9%)" />
                <XAxis dataKey="camera" tick={{ fontSize: 11, fill: "hsl(240 5% 64.9%)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "hsl(240 5% 64.9%)" }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="detections" fill="hsl(217.2 91.2% 59.8%)" radius={[3, 3, 0, 0]} name="Detections" />
                <Bar dataKey="matches" fill="hsl(0 72% 51%)" radius={[3, 3, 0, 0]} name="High Matches" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        {/* Camera Performance Table */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-surface"
        >
          <div className="px-4 py-3 border-b border-border/50">
            <h3 className="text-sm font-medium">Camera Performance</h3>
          </div>
          <div className="divide-y divide-border/30">
            {resultsLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="px-4 py-3">
                  <Skeleton className="h-8 w-full" />
                </div>
              ))
            ) : cameraData.length === 0 ? (
              <div className="p-6 text-center text-sm text-muted-foreground">No camera data</div>
            ) : (
              cameraData.map((cam) => (
                <div key={cam.camera} className="flex items-center justify-between px-4 py-3 hover:bg-accent/30 transition-colors">
                  <span className="text-sm font-medium w-32">{cam.camera}</span>
                  <div className="flex items-center gap-8 text-xs text-muted-foreground">
                    <div>
                      <span className="text-label block mb-0.5">Detections</span>
                      <span className="font-mono text-foreground">{cam.detections}</span>
                    </div>
                    <div>
                      <span className="text-label block mb-0.5">High Matches</span>
                      <span className="font-mono text-destructive">{cam.matches}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

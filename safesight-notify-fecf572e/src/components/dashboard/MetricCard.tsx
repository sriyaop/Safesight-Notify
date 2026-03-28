import { type LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  variant?: "default" | "primary" | "destructive" | "success" | "warning";
}

const variantStyles = {
  default: "text-foreground",
  primary: "text-primary glow-primary",
  destructive: "text-destructive glow-destructive",
  success: "text-success glow-success",
  warning: "text-warning",
};

const iconBgStyles = {
  default: "bg-muted",
  primary: "bg-primary/10",
  destructive: "bg-destructive/10",
  success: "bg-success/10",
  warning: "bg-warning/10",
};

export function MetricCard({ title, value, icon: Icon, trend, variant = "default" }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-surface p-4"
    >
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-label">{title}</p>
          <p className={`text-2xl font-semibold font-mono ${variantStyles[variant]}`}>
            {value}
          </p>
          {trend && (
            <p className="text-xs text-muted-foreground">{trend}</p>
          )}
        </div>
        <div className={`p-2 rounded-md ${iconBgStyles[variant]}`}>
          <Icon className={`h-4 w-4 ${variantStyles[variant]}`} />
        </div>
      </div>
    </motion.div>
  );
}

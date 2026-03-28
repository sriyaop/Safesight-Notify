import { Settings, Server, Mail, Shield, Bell, Save, CheckCircle2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { motion } from "framer-motion";
import { useState } from "react";
import { getStoredApiUrl, setApiUrl } from "@/lib/api";
import { toast } from "sonner";

export default function SettingsPage() {
  const [apiBaseUrl, setApiBaseUrl] = useState(getStoredApiUrl());
  const [threshold, setThreshold] = useState(
    localStorage.getItem("safesight_threshold") || "0.65"
  );

  const handleSave = () => {
    setApiUrl(apiBaseUrl);
    localStorage.setItem("safesight_threshold", threshold);
    toast.success("Settings saved. API queries will use the new URL.");
  };

  const handleTestConnection = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/metrics`);
      if (res.ok) {
        toast.success("Backend is reachable!");
      } else {
        toast.error(`Backend returned status ${res.status}`);
      }
    } catch {
      toast.error("Cannot reach backend. Check the URL and ensure Flask is running.");
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-base font-semibold">Settings</h1>
        <p className="text-xs text-muted-foreground mt-0.5">System configuration and preferences</p>
      </div>

      {/* API Connection */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card-surface p-4 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Server className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-medium">Flask Backend</h2>
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">API Base URL</Label>
          <Input
            value={apiBaseUrl}
            onChange={(e) => setApiBaseUrl(e.target.value)}
            className="h-8 text-sm bg-secondary border-border/50 font-mono"
          />
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Match Threshold</Label>
          <Input
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            className="h-8 text-sm bg-secondary border-border/50 font-mono"
          />
        </div>
        <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-border/50" onClick={handleTestConnection}>
          <CheckCircle2 className="h-3 w-3" />
          Test Connection
        </Button>
      </motion.div>

      {/* Email Alerts */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="card-surface p-4 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Mail className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-medium">Email Alerts</h2>
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Alert Email</Label>
          <Input defaultValue="sriyabommakanti@gmail.com" className="h-8 text-sm bg-secondary border-border/50" />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm">Enable email notifications</p>
            <p className="text-xs text-muted-foreground">Send alerts on face match detection</p>
          </div>
          <Switch defaultChecked />
        </div>
      </motion.div>

      {/* Notifications */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-surface p-4 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Bell className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-medium">Notifications</h2>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm">Sound alerts</p>
            <p className="text-xs text-muted-foreground">Play sound on new detection</p>
          </div>
          <Switch defaultChecked />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm">Browser notifications</p>
            <p className="text-xs text-muted-foreground">Show desktop notifications</p>
          </div>
          <Switch />
        </div>
      </motion.div>

      <Button className="bg-primary hover:bg-primary/90 text-sm h-9 gap-1.5" onClick={handleSave}>
        <Save className="h-3 w-3" />
        Save Settings
      </Button>
    </div>
  );
}

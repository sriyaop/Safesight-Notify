import { Camera, Plus, Settings2, RefreshCw } from "lucide-react";
import { CameraFeed } from "@/components/dashboard/CameraFeed";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { useCameraResults } from "@/hooks/use-api";

const cameras = [
  { name: "peoplelink", label: "PeopleLink Camera", location: "Main Entrance", resolution: "1280x720" },
  { name: "laptop", label: "Laptop Camera", location: "Office Desk", resolution: "640x480" },
  { name: "zebronics", label: "Zebronics Webcam", location: "Corridor", resolution: "640x480" },
];

export default function Cameras() {
  const { data: cameraResults, refetch } = useCameraResults(3000);

  const getCameraDetections = (name: string) => {
    if (!cameraResults) return 0;
    return cameraResults[name]?.length ?? 0;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold">Camera Management</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {cameras.length} cameras configured
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-border/50" onClick={() => refetch()}>
            <RefreshCw className="h-3 w-3" />
            Refresh All
          </Button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {cameras.map((cam, i) => (
          <motion.div
            key={cam.name}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <CameraFeed name={cam.name} label={cam.label} isOnline={true} />
            <div className="card-surface mt-0 rounded-t-none border-t-0 px-4 py-2 flex items-center justify-between">
              <div className="text-xs text-muted-foreground space-x-4">
                <span>{cam.location}</span>
                <span className="font-mono">{cam.resolution}</span>
                <span className="font-mono text-primary">{getCameraDetections(cam.name)} detections</span>
              </div>
              <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground">
                <Settings2 className="h-3 w-3" />
              </Button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

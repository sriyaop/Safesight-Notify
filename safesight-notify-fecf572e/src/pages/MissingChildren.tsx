import { useState } from "react";
import { Search, Plus, Filter, Upload, User, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { motion } from "framer-motion";
import { useMetrics, useCameraResults, flattenResults, useAddChild } from "@/hooks/use-api";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export default function MissingChildren() {
  const [search, setSearch] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [childName, setChildName] = useState("");
  const [childAge, setChildAge] = useState("");
  const [childImage, setChildImage] = useState<File | null>(null);

  const { data: metrics, isLoading: metricsLoading } = useMetrics();
  const { data: cameraResults } = useCameraResults(5000);
  const addChildMutation = useAddChild();

  // Show detected/matched children from camera results as our "database view"
  const allDetections = flattenResults(cameraResults);
  const uniqueChildren = allDetections.reduce((acc, d) => {
    if (!acc.find(c => c.name === d.name)) acc.push(d);
    return acc;
  }, [] as typeof allDetections);

  const filtered = uniqueChildren.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  const handleAddChild = async () => {
    if (!childName.trim() || !childAge.trim() || !childImage) {
      toast.error("Please fill all fields and select an image");
      return;
    }
    const formData = new FormData();
    formData.append("name", childName.trim());
    formData.append("age", childAge.trim());
    formData.append("image", childImage);

    try {
      await addChildMutation.mutateAsync(formData);
      toast.success(`${childName} added to missing children database`);
      setChildName("");
      setChildAge("");
      setChildImage(null);
      setAddOpen(false);
    } catch {
      toast.error("Failed to add child. Check backend connection.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold">Missing Children Database</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {metricsLoading ? "Loading…" : `${metrics?.missing_children ?? 0} records in database`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Dialog open={addOpen} onOpenChange={setAddOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="h-8 text-xs gap-1.5 bg-primary hover:bg-primary/90">
                <Plus className="h-3 w-3" />
                Add Child
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="text-sm">Add Missing Child</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">Full Name</Label>
                  <Input
                    value={childName}
                    onChange={(e) => setChildName(e.target.value)}
                    placeholder="Child's full name"
                    className="h-8 text-sm bg-secondary border-border/50"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">Age</Label>
                  <Input
                    value={childAge}
                    onChange={(e) => setChildAge(e.target.value)}
                    type="number"
                    placeholder="Age"
                    className="h-8 text-sm bg-secondary border-border/50"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">Photo</Label>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs gap-1.5 border-border/50"
                      onClick={() => document.getElementById("child-image-input")?.click()}
                    >
                      <Upload className="h-3 w-3" />
                      {childImage ? childImage.name : "Select Image"}
                    </Button>
                    {childImage && (
                      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setChildImage(null)}>
                        <X className="h-3 w-3" />
                      </Button>
                    )}
                    <input
                      id="child-image-input"
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => setChildImage(e.target.files?.[0] || null)}
                    />
                  </div>
                  {childImage && (
                    <img
                      src={URL.createObjectURL(childImage)}
                      alt="Preview"
                      className="h-24 w-24 rounded object-cover border border-border/50 mt-2"
                    />
                  )}
                </div>
                <Button
                  onClick={handleAddChild}
                  disabled={addChildMutation.isPending}
                  className="w-full bg-primary hover:bg-primary/90 text-sm h-9"
                >
                  {addChildMutation.isPending ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                      Uploading…
                    </>
                  ) : (
                    "Add to Database"
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 pl-9 text-sm bg-secondary border-border/50"
          />
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="card-surface overflow-hidden"
      >
        <table className="w-full">
          <thead>
            <tr className="border-b border-border/50">
              <th className="text-label text-left px-4 py-3">Photo</th>
              <th className="text-label text-left px-4 py-3">Name</th>
              <th className="text-label text-left px-4 py-3 hidden md:table-cell">Confidence</th>
              <th className="text-label text-left px-4 py-3 hidden md:table-cell">Camera</th>
              <th className="text-label text-left px-4 py-3 hidden lg:table-cell">DB Image</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {!cameraResults ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm text-muted-foreground">
                  {metricsLoading ? "Connecting to backend…" : "No detection data available. Start the Flask backend to see results."}
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm text-muted-foreground">
                  No matches found
                </td>
              </tr>
            ) : (
              filtered.map((child, i) => (
                <tr key={i} className="hover:bg-accent/30 transition-colors">
                  <td className="px-4 py-3">
                    <img
                      src={`data:image/jpeg;base64,${child.face}`}
                      alt={child.name}
                      className="h-10 w-10 rounded-full object-cover border border-border/50"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium">{child.name}</p>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <span className={`text-xs font-mono font-medium ${child.confidence >= 85 ? "text-destructive" : "text-warning"}`}>
                      {child.confidence.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground hidden md:table-cell">{child.camera}</td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    <img
                      src={`data:image/jpeg;base64,${child.db_image}`}
                      alt="DB"
                      className="h-10 w-10 rounded object-cover border border-border/50"
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
}

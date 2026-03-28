import { Eye, Search, Download } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { useState } from "react";
import { useCameraResults, flattenResults } from "@/hooks/use-api";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function MatchHistory() {
  const [search, setSearch] = useState("");
  const [selectedMatch, setSelectedMatch] = useState<ReturnType<typeof flattenResults>[0] | null>(null);
  const { data, isLoading, isError } = useCameraResults();
  const allMatches = flattenResults(data);

  const filtered = allMatches.filter(m =>
    m.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold">Match History</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {allMatches.length} detection{allMatches.length !== 1 ? "s" : ""} from live feeds
          </p>
        </div>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
        <Input
          placeholder="Search matches..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 pl-9 text-sm bg-secondary border-border/50"
        />
      </div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card-surface overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : isError ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            Unable to connect to backend
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            No matches found
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border/50">
                <th className="text-label text-left px-4 py-3">Face</th>
                <th className="text-label text-left px-4 py-3">Name</th>
                <th className="text-label text-left px-4 py-3 hidden md:table-cell">Confidence</th>
                <th className="text-label text-left px-4 py-3 hidden md:table-cell">Camera</th>
                <th className="text-label text-left px-4 py-3 hidden lg:table-cell">Time</th>
                <th className="text-label text-left px-4 py-3">Level</th>
                <th className="text-label text-left px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {filtered.map((match, i) => (
                <tr key={i} className="hover:bg-accent/30 transition-colors">
                  <td className="px-4 py-3">
                    <img
                      src={`data:image/jpeg;base64,${match.face}`}
                      alt="face"
                      className="h-8 w-8 rounded object-cover border border-border/50"
                    />
                  </td>
                  <td className="px-4 py-3 text-sm font-medium">{match.name}</td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <span className={`text-xs font-mono font-medium ${match.confidence >= 85 ? "text-destructive" : match.confidence >= 70 ? "text-warning" : "text-muted-foreground"}`}>
                      {match.confidence.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground hidden md:table-cell">{match.camera}</td>
                  <td className="px-4 py-3 text-xs font-mono text-muted-foreground hidden lg:table-cell">{match.timestamp}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className={`text-[10px] uppercase tracking-wider ${match.confidence >= 80 ? "bg-destructive/10 text-destructive border-destructive/20" : "bg-warning/10 text-warning border-warning/20"}`}>
                      {match.confidence >= 80 ? "High" : "Medium"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground" onClick={() => setSelectedMatch(match)}>
                      <Eye className="h-3 w-3" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </motion.div>

      {/* Detail dialog */}
      <Dialog open={!!selectedMatch} onOpenChange={() => setSelectedMatch(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-sm">Match Detail — {selectedMatch?.name}</DialogTitle>
          </DialogHeader>
          {selectedMatch && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Detected Face</p>
                  <img
                    src={`data:image/jpeg;base64,${selectedMatch.face}`}
                    alt="Detected"
                    className="w-full rounded border border-border/50"
                  />
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Database Image</p>
                  <img
                    src={`data:image/jpeg;base64,${selectedMatch.db_image}`}
                    alt="Database"
                    className="w-full rounded border border-border/50"
                  />
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Confidence</span>
                  <span className="font-mono text-destructive">{selectedMatch.confidence.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Camera</span>
                  <span>{selectedMatch.camera}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Time</span>
                  <span className="font-mono">{selectedMatch.timestamp}</span>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

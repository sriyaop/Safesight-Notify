import { useLocation, Link } from "react-router-dom";
import { motion } from "framer-motion";

const NotFound = () => {
  const location = useLocation();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-4"
      >
        <p className="text-6xl font-mono font-bold text-muted-foreground/30">404</p>
        <p className="text-sm text-muted-foreground">
          Route <code className="text-xs bg-secondary px-1.5 py-0.5 rounded font-mono">{location.pathname}</code> not found
        </p>
        <Link to="/" className="inline-block text-sm text-primary hover:underline">
          Return to Command Center
        </Link>
      </motion.div>
    </div>
  );
};

export default NotFound;

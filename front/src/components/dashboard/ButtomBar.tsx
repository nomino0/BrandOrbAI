import { Button } from "@/components/ui/button";
import { Download, Edit, ArrowRight } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function ButtomBar({ showValidate = true, onValidate }: { showValidate?: boolean, onValidate?: () => Promise<void> }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleValidate = async () => {
    setLoading(true);
    if (onValidate) {
      await onValidate();
    }
    setLoading(false);
    router.push("/dashboard/critical-report");
  };

  return (
    <div className="p-4 bottom-6 right-6 flex gap-3 z-50 justify-end">
      <Button variant="outline">
        <Download className="h-4 w-4 mr-2" />
        Download
      </Button>
      <Button variant="outline">
        <Edit className="h-4 w-4 mr-2" />
        Edit
      </Button>
      {showValidate && (
        <Button
          className="bg-primary hover:bg-primary/90 text-white"
          onClick={handleValidate}
          disabled={loading}
        >
          {loading ? "Validating..." : "Validate"}
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      )}
    </div>
  );
}

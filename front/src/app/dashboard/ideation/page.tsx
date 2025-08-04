"use client";
import { motion } from "framer-motion";
import dynamic from "next/dynamic";
import { useEffect, useState, useMemo, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { ButtomBar } from "@/components/dashboard/ButtomBar";
import clsx from "clsx";

// Dynamically import react-markdown to avoid SSR issues
const ReactMarkdown = dynamic(() => import("react-markdown"), { ssr: false });

const bentoColors = [
  "bg-yellow-100/60 dark:bg-yellow-900/10",
  "bg-purple-100/60 dark:bg-purple-900/10",
  "bg-blue-100/60 dark:bg-blue-900/10",
  "bg-pink-100/60 dark:bg-pink-900/10",
  "bg-orange-100/60 dark:bg-orange-900/10",
  "bg-green-100/60 dark:bg-green-900/10",
];

function parseSummaryToBlocks(summary: string): { title: string; content: string }[] {
  // Split by markdown headings (## or **n. Title:**)
  const blocks: { title: string; content: string }[] = [];
  const regex = /(?:^|\n)(?:##?\s*([\w\d .&-]+)|\*\*(\d+\. [^*]+)\*\*):?\s*/g;
  let match: RegExpExecArray | null;
  let lastTitle = "";
  let lastPos = 0;
  while ((match = regex.exec(summary))) {
    if (lastTitle) {
      blocks.push({
        title: lastTitle.trim(),
        content: summary.slice(lastPos, match.index).trim(),
      });
    }
    lastTitle = (match[1] || match[2] || "Untitled").replace(/[:*]/g, "").trim();
    lastPos = regex.lastIndex;
  }
  if (lastTitle) {
    blocks.push({
      title: lastTitle.trim(),
      content: summary.slice(lastPos).trim(),
    });
  }
  return blocks.length ? blocks : [{ title: "Summary", content: summary }];
}

export default function IdeationPage() {
  // Check for real session data
  const [mounted, setMounted] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validated, setValidated] = useState(false);
  const router = useRouter();

  useEffect(() => { 
    setMounted(true); 
    // Check if validation has already been done
    if (typeof window !== 'undefined') {
      setValidated(sessionStorage.getItem('brandorb_validated') === 'true');
    }
  }, []);

  const savedSummary = typeof window !== 'undefined' ? localStorage.getItem('brandorb_summary') : null;
  const savedBusinessIdea = typeof window !== 'undefined' ? localStorage.getItem('brandorb_business_idea') : null;
  const hasRealData = savedSummary && savedBusinessIdea;

  const handleValidate = useCallback(async () => {
    if (!savedBusinessIdea) return;
    
    setValidating(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/run-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_idea: savedBusinessIdea }),
      });
      
      if (response.ok) {
        sessionStorage.setItem('brandorb_validated', 'true');
        setValidated(true);
        router.push('/dashboard/critical-report');
      }
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setValidating(false);
    }
  }, [savedBusinessIdea, router]);

  const blocks = useMemo(() => (savedSummary ? parseSummaryToBlocks(savedSummary) : []), [savedSummary]);
  // Main title extraction: always use the first block's title, but show all blocks as cards
  let mainTitle = blocks.length > 0 ? blocks[0].title : "Business Analysis";
  let contentBlocks = blocks.length > 1 ? blocks.slice(1) : blocks;

  // Dynamic grid layout: alternate some cards to span cols/rows for bento effect
  function getCardGridClass(i: number) {
    if (i % 5 === 0) return "md:col-span-2 lg:row-span-2";
    if (i % 5 === 1) return "lg:col-span-1 lg:row-span-2";
    return "";
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] w-full px-4 relative">
      {hasRealData && mounted && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="w-full max-w-7xl"
        >
          {mainTitle && (
            <h1 className="text-2xl font-bold text-center mb-6 text-foreground">
              {mainTitle}
            </h1>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 auto-rows-min gap-6">
            {contentBlocks.map((block, i) => (
              <Card
                key={i}
                className={clsx(
                  "rounded-xl shadow-sm flex flex-col min-h-[120px]",
                  bentoColors[i % bentoColors.length],
                  getCardGridClass(i)
                )}
                style={{ minHeight: '120px', height: 'auto' }}
              >
                <CardHeader>
                  <CardTitle className="text-base font-semibold mb-1 text-foreground">
                    {block.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="prose prose-neutral dark:prose-invert max-w-none text-base text-foreground [&>p]:mb-4">
                  <ReactMarkdown>{block.content}</ReactMarkdown>
                </CardContent>
              </Card>
            ))}
          </div>
        </motion.div>
      )}
      
      {/* Bottom Bar with Validate Button */}
      {hasRealData && mounted && (
        <div className="fixed bottom-0 right-0 w-full">
          <ButtomBar 
            showValidate={!validated} 
            onValidate={handleValidate}
          />
        </div>
      )}
    </div>
  );
}

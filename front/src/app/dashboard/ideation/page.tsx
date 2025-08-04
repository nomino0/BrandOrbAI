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
  const blocks: { title: string; content: string }[] = [];
  
  // First, clean up the summary and handle different formats
  let content = summary.trim();
  
  // Remove main title if it starts with #
  content = content.replace(/^#\s+[^\n]+\n/, '');
  
  // Try different parsing approaches in order of preference
  
  // 1. Parse ## markdown headings
  const markdownSections = content.split(/\n##\s+/).filter(s => s.trim());
  if (markdownSections.length > 1) {
    markdownSections.forEach((section, index) => {
      const lines = section.split('\n');
      const title = lines[0].trim();
      const sectionContent = lines.slice(1).join('\n').trim();
      
      if (title && sectionContent) {
        blocks.push({ title, content: sectionContent });
      }
    });
  }
  
  // 2. If no markdown sections, try **bold titles**
  if (blocks.length === 0) {
    // Split by **Title** pattern but keep the titles
    const parts = content.split(/(\*\*[^*]+\*\*)/).filter(s => s.trim());
    
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i].trim();
      
      if (part.startsWith('**') && part.endsWith('**')) {
        // This is a title
        const title = part.replace(/\*\*/g, '').trim();
        const nextPart = parts[i + 1];
        
        if (nextPart && nextPart.trim()) {
          blocks.push({
            title: title,
            content: nextPart.trim()
          });
        }
      }
    }
  }
  
  // 3. If still no blocks, try to detect common business plan section titles
  if (blocks.length === 0) {
    const commonTitles = [
      'Business Idea',
      'Business Overview', 
      'Executive Summary',
      'Market Analysis',
      'Business Model',
      'Revenue Model',
      'Strengths & Opportunities',
      'Strengths and Opportunities',
      'Challenges & Risks',
      'Challenges and Risks',
      'Strategic Recommendations',
      'Financial Outlook',
      'Financial Analysis',
      'Detailed Analysis',
      'Implementation Plan',
      'Marketing Strategy',
      'Target Market',
      'Competitive Analysis'
    ];
    
    // Find all title positions
    const titleMatches: { title: string; index: number; matchLength: number }[] = [];
    commonTitles.forEach(title => {
      const regex = new RegExp(`(^|\\n)\\s*${title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*:?\\s*\\n`, 'gi');
      let match;
      while ((match = regex.exec(content)) !== null) {
        titleMatches.push({
          title: title,
          index: match.index + match[1].length,
          matchLength: match[0].length - match[1].length
        });
      }
    });
    
    // Sort by position and extract content
    titleMatches.sort((a, b) => a.index - b.index);
    
    for (let i = 0; i < titleMatches.length; i++) {
      const current = titleMatches[i];
      const next = titleMatches[i + 1];
      
      const startIndex = current.index + current.matchLength;
      const endIndex = next ? next.index : content.length;
      
      const sectionContent = content.slice(startIndex, endIndex).trim();
      
      if (sectionContent && sectionContent.length > 10) {
        blocks.push({
          title: current.title,
          content: sectionContent
        });
      }
    }
  }
  
  // 4. Final fallback: split by double line breaks and try to identify sections
  if (blocks.length === 0) {
    const paragraphs = content.split(/\n\s*\n/).filter(p => p.trim());
    
    for (const paragraph of paragraphs) {
      const lines = paragraph.split('\n');
      const firstLine = lines[0].trim();
      
      // Check if first line looks like a title (short, no period at end, etc.)
      if (firstLine.length < 50 && !firstLine.endsWith('.') && lines.length > 1) {
        const title = firstLine.replace(/^[\*\#\-\s]+/, '').replace(/[\*\#\-\s]+$/, '');
        const content = lines.slice(1).join('\n').trim();
        
        if (title && content && content.length > 20) {
          blocks.push({ title, content });
        }
      }
    }
  }
  
  // 5. Ultimate fallback: return the whole content as one block
  if (blocks.length === 0) {
    return [{ title: "Business Plan Summary", content: summary }];
  }
  
  return blocks;
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

  // Clean up the summary to remove unwanted sections
  const cleanedSummary = useMemo(() => {
    if (!savedSummary) return '';
    
    let content = savedSummary.trim();
    
    // Remove "Business Summary: Pet ecommerce Platform" section
    content = content.replace(/\*\*Business Summary: Pet ecommerce Platform\*\*/gi, '');
    
    // Remove any leading/trailing whitespace and extra line breaks
    content = content.replace(/^\s*\n+/, '').replace(/\n+\s*$/, '');
    
    return content;
  }, [savedSummary]);

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
  
  // Filter out unwanted titles and show remaining blocks as cards
  const contentBlocks = blocks.filter(block => 
    block.title !== "Business Summary: Pet ecommerce Platform" && 
    block.title !== "Business Overview"
  );

  // Enhanced grid layout: create more interesting bento patterns based on content
  function getCardGridClass(i: number, totalCards: number) {
    // Adjust layout based on total number of cards
    if (totalCards <= 3) {
      // For 3 or fewer cards, make them larger
      return i === 0 ? "md:col-span-2" : "md:col-span-1";
    } else if (totalCards <= 6) {
      // For 4-6 cards, create varied layout
      if (i === 0) return "md:col-span-2"; // First card spans 2 columns
      if (i === totalCards - 1 && totalCards % 2 === 0) return "md:col-span-2"; // Last card spans 2 if even total
      return "md:col-span-1";
    } else {
      // For many cards, create complex bento pattern
      if (i === 0) return "md:col-span-2 lg:col-span-2"; // First card spans 2 columns
      if (i === 1 || i === 2) return "md:col-span-1"; // Second and third normal size
      if (i === 3) return "md:col-span-2 lg:col-span-1"; // Fourth card different size
      if (i % 6 === 4) return "lg:col-span-2"; // Every 5th card spans 2 columns
      if (i % 6 === 5) return "lg:row-span-2"; // Every 6th card spans 2 rows
      return "";
    }
  }

  return (
    <div className="flex flex-col min-h-[70vh] w-full px-4 relative overflow-hidden">
      {hasRealData && mounted && (
        <>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="w-full max-w-7xl mx-auto flex-1"
          >
            <h1 className="text-2xl font-bold text-center mb-2 text-foreground">
              Pet ecommerce Platform
            </h1>
            <p className="text-sm text-muted-foreground text-center mb-6">
              Generated by BrandOrb AI on {new Date().toLocaleDateString()}
            </p>
            <div className="w-full max-w-4xl mx-auto mb-6">
              <Card className="rounded-xl shadow-sm border border-border/50 bg-background">
                <CardContent className="p-8 prose prose-neutral dark:prose-invert max-w-none text-foreground [&>h1]:text-2xl [&>h1]:font-bold [&>h1]:mb-4 [&>h2]:text-xl [&>h2]:font-semibold [&>h2]:mb-3 [&>h2]:mt-6 [&>h3]:text-lg [&>h3]:font-medium [&>h3]:mb-2 [&>h3]:mt-4 [&>p]:mb-4 [&>ul]:mb-4 [&>ol]:mb-4">
                  <ReactMarkdown>{cleanedSummary}</ReactMarkdown>
                </CardContent>
              </Card>
            </div>
          </motion.div>
          
          {/* Bottom Bar integrated within page */}
          <div className="w-full max-w-7xl mx-auto">
            <ButtomBar 
              showValidate={!validated} 
              onValidate={handleValidate}
            />
          </div>
        </>
      )}
    </div>
  );
}

"use client";
import { motion } from "framer-motion";
import dynamic from "next/dynamic";
import { useEffect, useState, useMemo, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { ButtomBar } from "@/components/dashboard/ButtomBar";
import { toast } from "sonner";
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
  const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const [imageGenerationAttempted, setImageGenerationAttempted] = useState(false);
  const router = useRouter();

  const savedSummary = typeof window !== 'undefined' ? localStorage.getItem('brandorb_summary') : null;
  const savedBusinessIdea = typeof window !== 'undefined' ? localStorage.getItem('brandorb_business_idea') : null;
  const hasRealData = savedSummary && savedBusinessIdea;

  useEffect(() => { 
    setMounted(true); 
    
    // Check if validation has already been done by checking if all 3 steps are completed
    if (typeof window !== 'undefined') {
      // Check if all 3 steps have been completed successfully
      const financialData = localStorage.getItem('brandorb_financial_data');
      const marketData = localStorage.getItem('brandorb_market_data');
      const swotData = localStorage.getItem('brandorb_swot_data');
      const bmcData = localStorage.getItem('brandorb_bmc_data');
      
      console.log('Validation check:', {
        financialData: !!financialData,
        marketData: !!marketData,
        swotData: !!swotData,
        bmcData: !!bmcData,
        savedSummary: !!savedSummary,
        savedBusinessIdea: !!savedBusinessIdea
      });
      
      // Validation is complete when we have all 3 main data sets
      const allStepsCompleted = financialData && marketData && swotData && bmcData;
      setValidated(!!allStepsCompleted);
      
      console.log('Validate button should be visible:', !allStepsCompleted && savedSummary && savedBusinessIdea);
      
      // Also check legacy session storage for backward compatibility
      const legacyValidated = sessionStorage.getItem('brandorb_validated') === 'true';
      if (legacyValidated && !allStepsCompleted) {
        // Legacy validation flag exists but data is missing - reset the flag
        sessionStorage.removeItem('brandorb_validated');
      }
      
      // Check for existing image from multiple sources in priority order
      const checkForExistingImage = () => {
        if (!savedSummary || !savedBusinessIdea) return false;
        
        // Import utility functions
        import('@/services/agents').then(({ getImageCacheKey, parseImageFromSummary }) => {
          // 0. FIRST PRIORITY: Check for embedded image URL in summary
          const embeddedImageData = parseImageFromSummary(savedSummary);
          if (embeddedImageData?.imageUrl && !backgroundImage) {
            setBackgroundImage(embeddedImageData.imageUrl);
            console.log('Loaded image from embedded summary metadata:', embeddedImageData.imageUrl);
            
            // Also cache it for quick access
            const summaryImageKey = getImageCacheKey(savedBusinessIdea, savedSummary);
            localStorage.setItem(summaryImageKey, embeddedImageData.imageUrl);
            return;
          }
          
          // 1. Second priority: Check for summary-linked cached image
          const summaryImageKey = getImageCacheKey(savedBusinessIdea, savedSummary);
          const summaryLinkedImage = localStorage.getItem(summaryImageKey);
          
          if (summaryLinkedImage && !backgroundImage) {
            setBackgroundImage(summaryLinkedImage);
            console.log('Loaded summary-linked cached image from localStorage');
            return;
          }
          
          // 2. Third priority: Check if run-all included image data
          try {
            const runAllData = localStorage.getItem('brandorb_run_state') || localStorage.getItem('brandorb_run_data');
            if (runAllData) {
              const parsedData = JSON.parse(runAllData);
              
              // Check if this is the new format with data property
              const stateData = parsedData.data || parsedData;
              
              if (stateData.background_image && stateData.background_image.status === 'success') {
                const imageData = stateData.background_image;
                
                // Priority order: serve_url (direct backend) > base64_data > image_url
                if (imageData.serve_url) {
                  setBackgroundImage(imageData.serve_url);
                  console.log('Loaded image from backend serve URL:', imageData.serve_url);
                  return;
                } else if (imageData.filename) {
                  // Build serve URL from filename if serve_url is not provided
                  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
                  const serveUrl = `${backendUrl}/images/${imageData.filename}`;
                  setBackgroundImage(serveUrl);
                  console.log('Loaded image from constructed serve URL:', serveUrl);
                  return;
                } else if (imageData.base64_data && imageData.base64_data.length > 50) {
                  // Only use base64 if it's actually complete
                  setBackgroundImage(imageData.base64_data);
                  // Cache it with summary-linked key for future use
                  localStorage.setItem(summaryImageKey, imageData.base64_data);
                  console.log('Loaded image from run-all data and cached with summary link');
                  return;
                } else if (imageData.image_url) {
                  setBackgroundImage(imageData.image_url);
                  console.log('Loaded image URL from run-all data');
                  return;
                }
              }
            }
          } catch (error) {
            console.error('Error parsing run-all data:', error);
            toast.error("Data Parsing Error", {
              description: "Unable to parse business analysis data. Some features may not work correctly.",
              duration: 4000,
            });
          }
          
          // 3. Fourth priority: Legacy - check old business-idea-based cache
          const legacyImageKey = `brandorb_image_${savedBusinessIdea}`;
          const legacyCachedImage = localStorage.getItem(legacyImageKey);
          if (legacyCachedImage && !backgroundImage) {
            setBackgroundImage(legacyCachedImage);
            // Migrate to new summary-linked cache
            localStorage.setItem(summaryImageKey, legacyCachedImage);
            // Remove old cache entry
            localStorage.removeItem(legacyImageKey);
            console.log('Migrated legacy cached image to summary-linked cache');
            return;
          }
          
          // 4. No existing image found - need to generate one (only if not already attempted)
          if (!backgroundImage && !imageLoading && !imageGenerationAttempted) {
            console.log('No existing image found, generating new one...');
            setImageGenerationAttempted(true);
            generateNewImage();
          }
        });
      };
      
      // Generate a new image when no cached version exists
      const generateNewImage = async () => {
        if (savedSummary && savedBusinessIdea && !backgroundImage && !imageLoading && !imageGenerationAttempted) {
          setImageLoading(true);
          setImageError(null);
          try {
            // Import the generateBusinessImage function dynamically
            const { generateBusinessImage, getImageCacheKey } = await import('@/services/agents');
            
            const result = await generateBusinessImage({
              business_idea: savedBusinessIdea,
              business_summary: savedSummary
            });
            
            console.log('Image generation result:', result);
            
            // Get the summary-based cache key
            const summaryImageKey = getImageCacheKey(savedBusinessIdea, savedSummary);
            
            // Priority order: serve_url (direct backend) > base64_data > image_url > download and convert
            if (result.serve_url) {
              setBackgroundImage(result.serve_url);
              console.log('Using direct serve URL from backend:', result.serve_url);
              // Cache the serve URL for quick access
              localStorage.setItem(summaryImageKey, result.serve_url);
            } else if (result.filename) {
              // Build serve URL from filename if serve_url is not provided
              const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
              const serveUrl = `${backendUrl}/images/${result.filename}`;
              setBackgroundImage(serveUrl);
              console.log('Using constructed serve URL from filename:', serveUrl);
              // Cache the serve URL
              localStorage.setItem(summaryImageKey, serveUrl);
            } else if (result.base64_data && result.base64_data.length > 50) {
              // Only use base64 if it's actually complete (more than 50 chars)
              setBackgroundImage(result.base64_data);
              console.log('Using base64 image data from backend');
              localStorage.setItem(summaryImageKey, result.base64_data);
            } else if (result.image_url) {
              // Download the image and convert to blob URL as fallback
              try {
                const imageResponse = await fetch(result.image_url);
                if (imageResponse.ok) {
                  const imageBlob = await imageResponse.blob();
                  
                  // Create a local blob URL for the image
                  const localImageUrl = URL.createObjectURL(imageBlob);
                  setBackgroundImage(localImageUrl);
                  console.log('Downloaded and cached background image from URL');
                  
                  // Convert to base64 and save to localStorage for persistence
                  const reader = new FileReader();
                  reader.onloadend = () => {
                    const base64String = reader.result as string;
                    localStorage.setItem(summaryImageKey, base64String);
                  };
                  reader.readAsDataURL(imageBlob);
                } else {
                  console.error('Failed to download image:', imageResponse.statusText);
                  // Fallback to direct URL if download fails
                  setBackgroundImage(result.image_url);
                }
              } catch (downloadError) {
                console.error('Error downloading image:', downloadError);
                // Fallback to direct URL if download fails
                setBackgroundImage(result.image_url);
              }
            }
          } catch (error) {
            console.error('Error generating image:', error);
            setImageError(error instanceof Error ? error.message : 'Failed to generate image');
          } finally {
            setImageLoading(false);
          }
        }
      };
      
      // Start the image checking process
      checkForExistingImage();
      
      // Listen for changes in localStorage to detect validation completion
      const handleStorageChange = () => {
        const financialData = localStorage.getItem('brandorb_financial_data');
        const marketData = localStorage.getItem('brandorb_market_data');
        const swotData = localStorage.getItem('brandorb_swot_data');
        const bmcData = localStorage.getItem('brandorb_bmc_data');
        
        const allStepsCompleted = financialData && marketData && swotData && bmcData;
        if (allStepsCompleted && !validated) {
          console.log('Validation completed detected via localStorage');
          setValidated(true);
          sessionStorage.setItem('brandorb_validated', 'true');
        }
      };
      
      // Listen for storage events
      window.addEventListener('storage', handleStorageChange);
      
      // Also check periodically in case storage events don't fire (same-origin issue)
      const storageCheckInterval = setInterval(handleStorageChange, 1000);
      
      // Cleanup listeners
      return () => {
        window.removeEventListener('storage', handleStorageChange);
        clearInterval(storageCheckInterval);
      };
    }
    
    // Cleanup function to revoke blob URLs (base64 data doesn't need cleanup)
    const cleanup = () => {
      if (backgroundImage && backgroundImage.startsWith('blob:')) {
        URL.revokeObjectURL(backgroundImage);
      }
    };

    return cleanup;
  }, [savedSummary, savedBusinessIdea]); // Remove backgroundImage and imageLoading from dependencies to prevent loops

  // Clean up the summary to remove unwanted sections
  const cleanedSummary = useMemo(() => {
    if (!savedSummary) return '';
    
    let content = savedSummary.trim();
    
    // Remove "Business Summary: Pet ecommerce Platform" section
    content = content.replace(/\*\*Business Summary: {title}\*\*/gi, '');
    
    // Remove the Generated Visual Assets section (this is metadata, not for display)
    content = content.replace(/\n\n---\n\n## Generated Visual Assets[\s\S]*?$/, '');
    
    // Remove any leading/trailing whitespace and extra line breaks
    content = content.replace(/^\s*\n+/, '').replace(/\n+\s*$/, '');
    
    return content;
  }, [savedSummary]);

  const handleValidate = useCallback(async () => {
    // This will be handled by the ButtomBar component
    console.log('Validation started via ButtomBar');
  }, []);

  const clearValidationData = useCallback(() => {
    // Clear all validation-related data for testing
    localStorage.removeItem('brandorb_financial_data');
    localStorage.removeItem('brandorb_market_data');
    localStorage.removeItem('brandorb_swot_data');
    localStorage.removeItem('brandorb_bmc_data');
    localStorage.removeItem('brandorb_run_data');
    localStorage.removeItem('brandorb_run_state');
    sessionStorage.removeItem('brandorb_validated');
    setValidated(false);
    console.log('Validation data cleared');
  }, []);

  const handleValidationComplete = useCallback(() => {
    // Called when all validation steps are completed
    console.log('All validation steps completed!');
    setValidated(true);
    // Optionally set a flag in sessionStorage for persistence
    sessionStorage.setItem('brandorb_validated', 'true');
  }, []);

  const blocks = useMemo(() => (savedSummary ? parseSummaryToBlocks(savedSummary) : []), [savedSummary]);
  
  // Filter out unwanted titles and show remaining blocks as cards
  const contentBlocks = blocks.filter(block => 
    block.title !== "Business Summary: {title}" && 
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
            
            
            {/* Background Image Card */}
            <div className="w-full max-w-4xl mx-auto mb-6">
              <Card className="rounded-xl shadow-sm border border-border/50 bg-background overflow-hidden p-0">
                <div 
                  className="relative h-64 bg-gradient-to-r from-blue-500/10 to-purple-500/10 flex items-center justify-center rounded-xl"
                  style={{
                    backgroundImage: backgroundImage && !imageLoading ? `url(${backgroundImage})` : undefined,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    backgroundRepeat: 'no-repeat'
                  }}
                >
                  {/* Skeleton loading state */}
                  {imageLoading && (
                    <div className="absolute inset-0 bg-muted/50">
                      <div role="status" className="w-full h-full p-4 border border-gray-200 rounded-sm shadow-sm animate-pulse md:p-6 dark:border-gray-700">
                        <div className="flex items-center justify-center h-full mb-4 bg-gray-300 rounded-sm dark:bg-gray-700">
                          <svg className="w-10 h-10 text-gray-200 dark:text-gray-600" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 20">
                            <path d="M14.066 0H7v5a2 2 0 0 1-2 2H0v11a1.97 1.97 0 0 0 1.934 2h12.132A1.97 1.97 0 0 0 16 18V2a1.97 1.97 0 0 0-1.934-2ZM10.5 6a1.5 1.5 0 1 1 0 2.999A1.5 1.5 0 0 1 10.5 6Zm2.221 10.515a1 1 0 0 1-.858.485h-8a1 1 0 0 1-.9-1.43L5.6 10.039a.978.978 0 0 1 .936-.57 1 1 0 0 1 .9.632l1.181 2.981.541-1a.945.945 0 0 1 .883-.522 1 1 0 0 1 .879.529l1.832 3.438a1 1 0 0 1-.031.988Z"/>
                            <path d="M5 5V.13a2.96 2.96 0 0 0-1.293.749L.879 3.707A2.98 2.98 0 0 0 .13 5H5Z"/>
                          </svg>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Overlay for better text readability */}
                  {backgroundImage && !imageLoading && (
                    <div className="absolute inset-0 bg-black/30 backdrop-blur-[1px]"></div>
                  )}
                  
                  {/* Content overlay */}
                  <div className="relative z-10 text-center">
                    <h2 className={`text-2xl font-bold mb-2 ${backgroundImage && !imageLoading ? 'text-white drop-shadow-lg' : 'text-foreground'}`}>
                      {savedBusinessIdea || "Your Business Idea"}
                    </h2>
                    <p className={`text-sm ${backgroundImage && !imageLoading ? 'text-white/90 drop-shadow' : 'text-muted-foreground'}`}>
                      Generated on {new Date().toLocaleDateString()}
                    </p>
                  </div>
                  
                  {/* Loading animation */}
                  {imageLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/5 dark:bg-white/5">
                      <div className="flex flex-col items-center space-y-2">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                        <p className="text-xs text-muted-foreground animate-pulse">
                          Generating background...
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {/* Error state with retry button */}
                  {imageError && !imageLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/5 dark:bg-white/5">
                      <div className="flex flex-col items-center space-y-2 text-center p-4">
                        <p className="text-xs text-muted-foreground">
                          Failed to generate image
                        </p>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => {
                            setImageError(null);
                            setBackgroundImage(null);
                            setImageGenerationAttempted(false); // Reset the flag to allow retry
                            // Trigger regeneration with updated caching system
                            const generateImage = async () => {
                              if (savedSummary && savedBusinessIdea) {
                                setImageLoading(true);
                                setImageError(null);
                                try {
                                  const { generateBusinessImage, getImageCacheKey } = await import('@/services/agents');
                                  const result = await generateBusinessImage({
                                    business_idea: savedBusinessIdea,
                                    business_summary: savedSummary
                                  });
                                  
                                  // Get the summary-based cache key
                                  const summaryImageKey = getImageCacheKey(savedBusinessIdea, savedSummary);
                                  
                                  // Priority order: serve_url > filename > base64_data > image_url
                                  if (result.serve_url) {
                                    setBackgroundImage(result.serve_url);
                                    console.log('Using direct serve URL from backend:', result.serve_url);
                                    localStorage.setItem(summaryImageKey, result.serve_url);
                                  } else if (result.filename) {
                                    // Build serve URL from filename
                                    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
                                    const serveUrl = `${backendUrl}/images/${result.filename}`;
                                    setBackgroundImage(serveUrl);
                                    console.log('Using constructed serve URL from filename:', serveUrl);
                                    localStorage.setItem(summaryImageKey, serveUrl);
                                  } else if (result.base64_data && result.base64_data.length > 50) {
                                    setBackgroundImage(result.base64_data);
                                    localStorage.setItem(summaryImageKey, result.base64_data);
                                  } else if (result.image_url) {
                                    setBackgroundImage(result.image_url);
                                  }
                                } catch (error) {
                                  setImageError(error instanceof Error ? error.message : 'Failed to generate image');
                                } finally {
                                  setImageLoading(false);
                                }
                              }
                            };
                            generateImage();
                          }}
                        >
                          Retry
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            {/* Business Plan Content Card */}
            <div className="w-full max-w-4xl mx-auto mb-6">
              <Card className="rounded-xl shadow-sm border border-border/50 bg-background overflow-hidden">
                <CardContent className="p-8 max-w-none text-foreground">
                  <ReactMarkdown 
                    components={{
                      // GitHub-style headings
                      h1: ({ children }) => <h1 className="text-2xl font-semibold text-foreground mb-4 pb-2 border-b border-border">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-xl font-semibold text-foreground mb-3 mt-6 pb-1 border-b border-border">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-lg font-semibold text-foreground mb-2 mt-4">{children}</h3>,
                      h4: ({ children }) => <h4 className="text-base font-semibold text-foreground mb-2 mt-3">{children}</h4>,
                      h5: ({ children }) => <h5 className="text-sm font-semibold text-foreground mb-2 mt-3">{children}</h5>,
                      h6: ({ children }) => <h6 className="text-sm font-medium text-muted-foreground mb-2 mt-3">{children}</h6>,
                      
                      // GitHub-style paragraphs
                      p: ({ children }) => <p className="mb-4 leading-6 text-foreground">{children}</p>,
                      
                      // GitHub-style lists (no bold, proper spacing)
                      ol: ({ children }) => <ol className="list-decimal ml-6 mb-4 space-y-1">{children}</ol>,
                      ul: ({ children }) => <ul className="list-disc ml-6 mb-4 space-y-1">{children}</ul>,
                      li: ({ children }) => <li className="leading-6 text-foreground">{children}</li>,
                      
                      // GitHub-style emphasis
                      strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                      em: ({ children }) => <em className="italic text-foreground">{children}</em>,
                      
                      // GitHub-style code
                      code: ({ children, ...props }) => {
                        const isInline = !props.className?.includes('language-');
                        return isInline ? (
                          <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-foreground">{children}</code>
                        ) : (
                          <code className="block bg-muted p-3 rounded-md text-sm font-mono text-foreground overflow-x-auto">{children}</code>
                        );
                      },
                      
                      // GitHub-style blockquotes
                      blockquote: ({ children }) => (
                        <blockquote className="border-l-4 border-border pl-4 py-1 my-4 text-muted-foreground italic">{children}</blockquote>
                      ),
                      
                      // GitHub-style horizontal rule
                      hr: () => <hr className="my-6 border-t border-border" />,
                      
                      // GitHub-style links
                      a: ({ children, href }) => (
                        <a href={href} className="text-primary hover:underline underline-offset-2">{children}</a>
                      )
                    }}
                  >
                    {cleanedSummary}
                  </ReactMarkdown>
                </CardContent>
              </Card>
            </div>
          </motion.div>
          
          {/* Bottom Bar integrated within page */}
          <div className="w-full max-w-7xl mx-auto">
            <ButtomBar 
              showValidate={!validated} 
              onValidate={handleValidate}
              onValidationComplete={handleValidationComplete}
            />
          </div>
        </>
      )}
    </div>
  );
}

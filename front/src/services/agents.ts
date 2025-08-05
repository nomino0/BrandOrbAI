const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';

export interface AgentOutput {
  output: string;
}

export async function runAllAgents(businessIdea: string): Promise<{ message: string }> {
  const response = await fetch(`${BACKEND_URL}/run-all`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ business_idea: businessIdea }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to run agents');
  }
  
  return response.json();
}

export async function getAgentOutput(agent: string): Promise<AgentOutput> {
  const response = await fetch(`${BACKEND_URL}/agent-output?agent=${agent}`);
  
  if (!response.ok) {
    throw new Error(`Failed to get output for agent: ${agent}`);
  }
  
  return response.json();
}

export async function runBMCExtraction(): Promise<{ status: string }> {
  const response = await fetch(`${BACKEND_URL}/bmc/run`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error('Failed to run BMC extraction');
  }
  
  return response.json();
}

export async function getBMCOutput(): Promise<string> {
  const response = await fetch(`${BACKEND_URL}/bmc/output`);
  
  if (!response.ok) {
    throw new Error('Failed to get BMC output');
  }
  
  return response.text();
}

export async function runSWOTAnalysis(): Promise<{ message: string; status: string }> {
  const response = await fetch(`${BACKEND_URL}/run-swot`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error('Failed to run SWOT analysis');
  }
  
  return response.json();
}

export async function getSWOTOutput(): Promise<{ content: string }> {
  const response = await fetch(`${BACKEND_URL}/swot-output`);
  
  if (!response.ok) {
    throw new Error('Failed to get SWOT output');
  }
  
  return response.json();
}

// Helper functions to parse specific outputs
export function parseFinancialAssessment(output: string) {
  try {
    // Try to parse as JSON first
    const jsonMatch = output.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return { text: output };
  } catch {
    return { text: output };
  }
}

export function parseMarketAnalysis(output: string) {
  const sections = output.split(/#{1,2}\s+/);
  const parsed = {
    marketAnalysis: '',
    competitorAnalysis: '',
    charts: [] as any[]
  };
  
  sections.forEach(section => {
    if (section.toLowerCase().includes('market analysis')) {
      parsed.marketAnalysis = section;
    } else if (section.toLowerCase().includes('competitor')) {
      parsed.competitorAnalysis = section;
    }
  });
  
  // Extract any JSON data for charts
  const jsonMatch = output.match(/\{[\s\S]*\}/g);
  if (jsonMatch) {
    jsonMatch.forEach(json => {
      try {
        parsed.charts.push(JSON.parse(json));
      } catch {}
    });
  }
  
  return parsed;
}

export function parseBMCOutput(output: string) {
  const sections = output.split(/\n\n/);
  const bmc: Record<string, string> = {};
  
  sections.forEach(section => {
    const lines = section.split('\n');
    if (lines.length > 0 && lines[0].endsWith(':')) {
      const key = lines[0].replace(':', '');
      const content = lines.slice(1).join('\n').trim();
      bmc[key] = content;
    }
  });
  
  return bmc;
}

export function parseSWOTOutput(output: string) {
  // Initialize the parsed structure
  const parsed = {
    strengths: '',
    weaknesses: '',
    opportunities: '',
    threats: '',
    fullAnalysis: output
  };
  
  try {
    // Try to parse as JSON first if it looks like JSON
    const jsonMatch = output.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const jsonData = JSON.parse(jsonMatch[0]);
      
      // Handle structured JSON SWOT data
      if (jsonData.swot_analysis) {
        const swot = jsonData.swot_analysis;
        parsed.strengths = Array.isArray(swot.strengths) ? swot.strengths.join('\n\n') : (swot.strengths || '');
        parsed.weaknesses = Array.isArray(swot.weaknesses) ? swot.weaknesses.join('\n\n') : (swot.weaknesses || '');
        parsed.opportunities = Array.isArray(swot.opportunities) ? swot.opportunities.join('\n\n') : (swot.opportunities || '');
        parsed.threats = Array.isArray(swot.threats) ? swot.threats.join('\n\n') : (swot.threats || '');
      } else if (jsonData.strengths || jsonData.weaknesses || jsonData.opportunities || jsonData.threats) {
        // Direct SWOT structure
        parsed.strengths = Array.isArray(jsonData.strengths) ? jsonData.strengths.join('\n\n') : (jsonData.strengths || '');
        parsed.weaknesses = Array.isArray(jsonData.weaknesses) ? jsonData.weaknesses.join('\n\n') : (jsonData.weaknesses || '');
        parsed.opportunities = Array.isArray(jsonData.opportunities) ? jsonData.opportunities.join('\n\n') : (jsonData.opportunities || '');
        parsed.threats = Array.isArray(jsonData.threats) ? jsonData.threats.join('\n\n') : (jsonData.threats || '');
      }
      
      return parsed;
    }
  } catch (error) {
    // If JSON parsing fails, fall back to text parsing
    console.warn('Failed to parse SWOT as JSON, using text parsing');
  }
  
  // Text-based parsing for markdown or plain text format
  const sections = output.split(/(?:^|\n)(?:#{1,3}\s*|## )/i);
  
  sections.forEach(section => {
    const sectionLower = section.toLowerCase();
    
    if (sectionLower.includes('strength') && !sectionLower.includes('weakness')) {
      parsed.strengths = section.replace(/^strength[s]?[:\s]*/i, '').trim();
    } else if (sectionLower.includes('weakness') && !sectionLower.includes('strength')) {
      parsed.weaknesses = section.replace(/^weakness[es]*[:\s]*/i, '').trim();
    } else if (sectionLower.includes('opportunit')) {
      parsed.opportunities = section.replace(/^opportunit[ies]*[:\s]*/i, '').trim();
    } else if (sectionLower.includes('threat')) {
      parsed.threats = section.replace(/^threat[s]*[:\s]*/i, '').trim();
    }
  });
  
  // If no sections were found, try bullet point parsing
  if (!parsed.strengths && !parsed.weaknesses && !parsed.opportunities && !parsed.threats) {
    const lines = output.split('\n');
    let currentSection = '';
    
    lines.forEach(line => {
      const lineLower = line.toLowerCase().trim();
      
      if (lineLower.includes('strength') && !lineLower.includes('weakness')) {
        currentSection = 'strengths';
      } else if (lineLower.includes('weakness') && !lineLower.includes('strength')) {
        currentSection = 'weaknesses';
      } else if (lineLower.includes('opportunit')) {
        currentSection = 'opportunities';
      } else if (lineLower.includes('threat')) {
        currentSection = 'threats';
      } else if (line.trim() && currentSection) {
        // Add content to current section
        if (parsed[currentSection as keyof typeof parsed]) {
          parsed[currentSection as keyof typeof parsed] += '\n' + line;
        } else {
          parsed[currentSection as keyof typeof parsed] = line;
        }
      }
    });
  }
  
  return parsed;
}

// Image generation types and functions
export interface ImageGenerationRequest {
  business_idea: string;
  business_summary: string;
}

export interface ImageGenerationResponse {
  image_url: string;
  business_idea: string;
  generated_at: string;
  status: string;
  base64_data?: string;
  local_path?: string;
  filename?: string;
  file_size?: number;
  serve_url?: string;  // Direct URL to serve the image
}

export async function generateBusinessImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
  const response = await fetch(`${BACKEND_URL}/generate-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error('Failed to generate business image');
  }
  
  return response.json();
}

export async function getImageOutput(): Promise<ImageGenerationResponse> {
  const response = await fetch(`${BACKEND_URL}/image-output`);
  
  if (!response.ok) {
    throw new Error('Failed to get image output');
  }
  
  return response.json();
}

// Utility functions for image handling
export function isBase64Image(imageString: string): boolean {
  return imageString.startsWith('data:image/');
}

export function isBlobUrl(imageString: string): boolean {
  return imageString.startsWith('blob:');
}

export function isHttpUrl(imageString: string): boolean {
  return imageString.startsWith('http://') || imageString.startsWith('https://');
}

// Generate a unique hash for business summary content
export function generateSummaryHash(businessIdea: string, businessSummary: string): string {
  const content = `${businessIdea}||${businessSummary}`;
  // Simple hash function for creating unique IDs
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36); // Convert to base36 string
}

// Get image cache key based on summary hash
export function getImageCacheKey(businessIdea: string, businessSummary: string): string {
  const summaryHash = generateSummaryHash(businessIdea, businessSummary);
  return `brandorb_image_${summaryHash}`;
}

export async function downloadImageAsBase64(imageUrl: string): Promise<string> {
  try {
    const response = await fetch(imageUrl);
    if (!response.ok) {
      throw new Error(`Failed to download image: ${response.statusText}`);
    }
    
    const blob = await response.blob();
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.error('Error downloading image as base64:', error);
    throw error;
  }
}

// Parse image metadata from summary markdown
export function parseImageFromSummary(summary: string): {
  imageUrl?: string;
  filename?: string;
  generatedAt?: string;
  originalSource?: string;
} | null {
  if (!summary) return null;
  
  const result: any = {};
  
  // Look for the Generated Visual Assets section
  const imageSection = summary.match(/## Generated Visual Assets[\s\S]*?(?=\n## |$)/);
  if (!imageSection) return null;
  
  const imageContent = imageSection[0];
  
  // Extract Background Image URL
  const imageUrlMatch = imageContent.match(/\*\*Background Image URL:\*\*\s*(.+)/);
  if (imageUrlMatch) {
    result.imageUrl = imageUrlMatch[1].trim();
  }
  
  // Extract Image Filename
  const filenameMatch = imageContent.match(/\*\*Image Filename:\*\*\s*(.+)/);
  if (filenameMatch) {
    result.filename = filenameMatch[1].trim();
  }
  
  // Extract Generated timestamp
  const generatedMatch = imageContent.match(/\*\*Generated:\*\*\s*(.+)/);
  if (generatedMatch) {
    result.generatedAt = generatedMatch[1].trim();
  }
  
  // Extract Original Source
  const sourceMatch = imageContent.match(/\*\*Original Source:\*\*\s*(.+)/);
  if (sourceMatch) {
    result.originalSource = sourceMatch[1].trim();
  }
  
  return Object.keys(result).length > 0 ? result : null;
}

// Generate summary with embedded image
export async function generateSummaryWithImage(sessionId: string): Promise<{ summary: string }> {
  const response = await fetch(`${BACKEND_URL}/summary-with-image/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (!response.ok) {
    throw new Error('Failed to generate summary with image');
  }
  
  return response.json();
}

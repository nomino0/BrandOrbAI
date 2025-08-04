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

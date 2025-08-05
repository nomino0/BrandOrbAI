"use client";

import React from 'react';
import dynamic from 'next/dynamic';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { parseFinancialAssessment, parseMarketAnalysis, parseSWOTOutput } from '@/services/agents';

// Dynamically import react-markdown to avoid SSR issues
const ReactMarkdown = dynamic(() => import('react-markdown'), { ssr: false });

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

interface AgentOutputDisplayProps {
  agentType: 'financial_assessment' | 'legal_analysis' | 'market_analysis_competitors' | 'opportunities' | 'swot_analysis';
  output: string;
  title: string;
}

export function AgentOutputDisplay({ agentType, output, title }: AgentOutputDisplayProps) {
  if (!output) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            Loading {title.toLowerCase()}...
          </div>
        </CardContent>
      </Card>
    );
  }

  const renderFinancialAssessment = () => {
    const parsed = parseFinancialAssessment(output);
    
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {parsed.text && (
            <div className="prose prose-neutral dark:prose-invert max-w-none">
              <ReactMarkdown>{parsed.text}</ReactMarkdown>
            </div>
          )}
          
          {/* Check for common financial data patterns */}
          {parsed.revenue_projections && (
            <div>
              <h4 className="text-lg font-semibold mb-3">Revenue Projections</h4>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={parsed.revenue_projections}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="revenue" stroke="#8884d8" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          
          {parsed.cost_breakdown && (
            <div>
              <h4 className="text-lg font-semibold mb-3">Cost Breakdown</h4>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={parsed.cost_breakdown}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {parsed.cost_breakdown.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderMarketAnalysis = () => {
    const parsed = parseMarketAnalysis(output);
    
    return (
      <div className="space-y-6">
        {parsed.marketAnalysis && (
          <Card>
            <CardHeader>
              <CardTitle>Market Research</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-neutral dark:prose-invert max-w-none">
                <ReactMarkdown>{parsed.marketAnalysis}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        )}
        
        {parsed.competitorAnalysis && (
          <Card>
            <CardHeader>
              <CardTitle>Competitor Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-neutral dark:prose-invert max-w-none">
                <ReactMarkdown>{parsed.competitorAnalysis}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        )}
        
        {parsed.charts.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Market Data Visualization</CardTitle>
            </CardHeader>
            <CardContent>
              {parsed.charts.map((chartData, index) => (
                <div key={index} className="mb-6">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData.data || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey={chartData.xKey || 'name'} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey={chartData.yKey || 'value'} fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderLegalAnalysis = () => (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <ReactMarkdown>{output}</ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );

  const renderOpportunities = () => (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <ReactMarkdown>{output}</ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );

  const renderSWOTAnalysis = () => {
    const parsed = parseSWOTOutput(output);
    
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Strengths */}
              {parsed.strengths && (
                <Card className="border-green-200 dark:border-green-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-green-700 dark:text-green-300 flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      Strengths
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none">
                      <ReactMarkdown>{parsed.strengths}</ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Weaknesses */}
              {parsed.weaknesses && (
                <Card className="border-red-200 dark:border-red-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-red-700 dark:text-red-300 flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      Weaknesses
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none">
                      <ReactMarkdown>{parsed.weaknesses}</ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Opportunities */}
              {parsed.opportunities && (
                <Card className="border-blue-200 dark:border-blue-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-blue-700 dark:text-blue-300 flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      Opportunities
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none">
                      <ReactMarkdown>{parsed.opportunities}</ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Threats */}
              {parsed.threats && (
                <Card className="border-orange-200 dark:border-orange-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-orange-700 dark:text-orange-300 flex items-center gap-2">
                      <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                      Threats
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none">
                      <ReactMarkdown>{parsed.threats}</ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Full Analysis Fallback */}
            {!parsed.strengths && !parsed.weaknesses && !parsed.opportunities && !parsed.threats && (
              <div className="prose prose-neutral dark:prose-invert max-w-none">
                <ReactMarkdown>{parsed.fullAnalysis}</ReactMarkdown>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  };

  switch (agentType) {
    case 'financial_assessment':
      return renderFinancialAssessment();
    case 'market_analysis_competitors':
      return renderMarketAnalysis();
    case 'legal_analysis':
      return renderLegalAnalysis();
    case 'opportunities':
      return renderOpportunities();
    case 'swot_analysis':
      return renderSWOTAnalysis();
    default:
      return (
        <Card>
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-neutral dark:prose-invert max-w-none">
              <ReactMarkdown>{output}</ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      );
  }
}

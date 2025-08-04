"use client";

import React from 'react';
import dynamic from 'next/dynamic';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { parseFinancialAssessment, parseMarketAnalysis } from '@/services/agents';

// Dynamically import react-markdown to avoid SSR issues
const ReactMarkdown = dynamic(() => import('react-markdown'), { ssr: false });

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

interface AgentOutputDisplayProps {
  agentType: 'financial_assessment' | 'legal_analysis' | 'market_analysis_competitors' | 'opportunities';
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

  switch (agentType) {
    case 'financial_assessment':
      return renderFinancialAssessment();
    case 'market_analysis_competitors':
      return renderMarketAnalysis();
    case 'legal_analysis':
      return renderLegalAnalysis();
    case 'opportunities':
      return renderOpportunities();
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

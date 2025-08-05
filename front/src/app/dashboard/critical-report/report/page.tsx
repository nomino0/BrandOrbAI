"use client";

import React from "react";
import { AppSidebar } from "@/components/app-sidebar"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  FileText, 
  Download, 
  Share2, 
  ArrowLeft,
  Target,
  TrendingUp,
  DollarSign,
  Shield,
  CheckCircle
} from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { getAgentOutput, getSWOTOutput } from "@/services/agents";
import { AgentOutputDisplay } from "@/components/dashboard/AgentOutputDisplay";

export default function SWOTReportPage() {
  const [agentOutputs, setAgentOutputs] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllOutputs();
  }, []);

  const fetchAllOutputs = async () => {
    setLoading(true);
    try {
      const agents = ['financial_assessment', 'legal_analysis', 'market_analysis_competitors', 'opportunities'];
      const outputs: Record<string, string> = {};
      
      // Fetch standard agent outputs
      for (const agent of agents) {
        try {
          const result = await getAgentOutput(agent);
          outputs[agent] = result.output;
        } catch (error) {
          console.error(`Failed to fetch ${agent}:`, error);
          outputs[agent] = '';
        }
      }

      // Fetch SWOT analysis separately
      try {
        const swotResult = await getSWOTOutput();
        outputs['swot_analysis'] = swotResult.content;
      } catch (error) {
        console.error('Failed to fetch SWOT analysis:', error);
        outputs['swot_analysis'] = '';
      }
      
      setAgentOutputs(outputs);
    } catch (error) {
      console.error('Failed to fetch agent outputs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    // TODO: Implement PDF download
    console.log("Downloading SWOT report...");
  };

  const handleShare = () => {
    // TODO: Implement sharing
    console.log("Sharing SWOT report...");
  };

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <div className="flex flex-1 flex-col gap-4 p-4">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex items-center justify-between mb-6"
          >
            <div className="flex items-center gap-4">
              <Link href="/dashboard/critical-report">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to SWOT Analysis
                </Button>
              </Link>
              <div>
                <h1 className="text-3xl font-bold">SWOT Analysis Report</h1>
                <p className="text-muted-foreground mt-1">
                  Comprehensive strategic assessment and recommendations
                </p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <Button variant="outline" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download PDF
              </Button>
              <Button variant="outline" onClick={handleShare}>
                <Share2 className="h-4 w-4 mr-2" />
                Share Report
              </Button>
            </div>
          </motion.div>

          {loading ? (
            <div className="flex items-center justify-center min-h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-muted-foreground">Generating comprehensive SWOT report...</p>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Report Overview */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      Strategic Assessment Complete
                    </CardTitle>
                    <CardDescription>
                      Comprehensive analysis of your business strengths, weaknesses, opportunities, and threats
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                        <Target className="h-6 w-6 text-green-600 mx-auto mb-2" />
                        <div className="text-sm font-medium text-green-800 dark:text-green-300">Strengths</div>
                        <div className="text-xs text-green-600">Identified</div>
                      </div>
                      <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                        <Shield className="h-6 w-6 text-red-600 mx-auto mb-2" />
                        <div className="text-sm font-medium text-red-800 dark:text-red-300">Weaknesses</div>
                        <div className="text-xs text-red-600">Assessed</div>
                      </div>
                      <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                        <TrendingUp className="h-6 w-6 text-blue-600 mx-auto mb-2" />
                        <div className="text-sm font-medium text-blue-800 dark:text-blue-300">Opportunities</div>
                        <div className="text-xs text-blue-600">Mapped</div>
                      </div>
                      <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
                        <DollarSign className="h-6 w-6 text-orange-600 mx-auto mb-2" />
                        <div className="text-sm font-medium text-orange-800 dark:text-orange-300">Threats</div>
                        <div className="text-xs text-orange-600">Analyzed</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* SWOT Analysis Results */}
              {agentOutputs['swot_analysis'] && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                >
                  <AgentOutputDisplay
                    agentType="swot_analysis"
                    output={agentOutputs['swot_analysis']}
                    title="Strategic SWOT Analysis"
                  />
                </motion.div>
              )}

              {/* Supporting Analysis Sections */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Financial Assessment */}
                {agentOutputs['financial_assessment'] && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                  >
                    <AgentOutputDisplay
                      agentType="financial_assessment"
                      output={agentOutputs['financial_assessment']}
                      title="Financial Assessment"
                    />
                  </motion.div>
                )}

                {/* Market Analysis */}
                {agentOutputs['market_analysis_competitors'] && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.4 }}
                  >
                    <AgentOutputDisplay
                      agentType="market_analysis_competitors"
                      output={agentOutputs['market_analysis_competitors']}
                      title="Market & Competitive Analysis"
                    />
                  </motion.div>
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Legal Analysis */}
                {agentOutputs['legal_analysis'] && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.5 }}
                  >
                    <AgentOutputDisplay
                      agentType="legal_analysis"
                      output={agentOutputs['legal_analysis']}
                      title="Legal & Risk Analysis"
                    />
                  </motion.div>
                )}

                {/* Opportunities */}
                {agentOutputs['opportunities'] && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.6 }}
                  >
                    <AgentOutputDisplay
                      agentType="opportunities"
                      output={agentOutputs['opportunities']}
                      title="Market Opportunities"
                    />
                  </motion.div>
                )}
              </div>

              {/* Next Steps */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.7 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Next Steps</CardTitle>
                    <CardDescription>
                      Recommended actions based on your SWOT analysis
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                        <h4 className="font-semibold text-blue-800 dark:text-blue-300 mb-2">
                          Create Your Business Model Canvas
                        </h4>
                        <p className="text-blue-700 dark:text-blue-400 text-sm mb-3">
                          Use insights from your SWOT analysis to develop a comprehensive business model.
                        </p>
                        <Link href="/dashboard/bmc">
                          <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                            <Target className="h-4 w-4 mr-2" />
                            Proceed to Business Model Canvas
                          </Button>
                        </Link>
                      </div>
                      
                      <div className="p-4 bg-gray-50 dark:bg-gray-800/30 border border-gray-200 dark:border-gray-700 rounded-lg">
                        <h4 className="font-semibold mb-2">Alternative Actions</h4>
                        <div className="space-y-2">
                          <Button variant="outline" className="w-full justify-start" onClick={handleDownload}>
                            <Download className="h-4 w-4 mr-2" />
                            Download Complete Report
                          </Button>
                          <Link href="/dashboard/critical-report">
                            <Button variant="outline" className="w-full justify-start">
                              <ArrowLeft className="h-4 w-4 mr-2" />
                              Return to SWOT Analysis
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Report Footer */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.8 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Report Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm text-muted-foreground">
                    <div className="flex justify-between">
                      <span>Generated</span>
                      <span>{new Date().toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Analysis Type</span>
                      <span>Comprehensive SWOT Assessment</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Components</span>
                      <span>5 Strategic Areas</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Report Version</span>
                      <span>1.0</span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

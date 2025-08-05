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
import StageSkeleton from "@/components/dashboard/StageSkeleton";
import { 
  FileText, 
  ArrowRight, 
  Clock,
  CheckCircle,
  Lock,
  Play,
  User,
  Settings,
  LogOut,
  Download,
  Edit
} from "lucide-react";
import Link from "next/link";
import { useStepProgress } from "@/hooks/useStepProgress";
import { getAgentOutput, getSWOTOutput } from "@/services/agents";
import { AgentOutputDisplay } from "@/components/dashboard/AgentOutputDisplay";
import { useState, useEffect } from "react";

export default function CriticalReportPage() {
  const { steps, isValidated } = useStepProgress();
  const [agentOutputs, setAgentOutputs] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const completedSteps = steps.filter(step => step.status === "completed").length;
  const totalProgress = (completedSteps / steps.length) * 100;

  // Fetch agent outputs after validation
  useEffect(() => {
    if (isValidated && Object.keys(agentOutputs).length === 0) {
      fetchAgentOutputs();
    }
  }, [isValidated]);

  const fetchAgentOutputs = async () => {
    setLoading(true);
    try {
      const agents = ['financial_assessment', 'legal_analysis', 'market_analysis_competitors', 'opportunities'];
      const outputs: Record<string, string> = {};
      
      for (const agent of agents) {
        try {
          const result = await getAgentOutput(agent);
          outputs[agent] = result.output;
        } catch (error) {
          console.error(`Failed to fetch ${agent}:`, error);
          outputs[agent] = '';
        }
      }

      // Fetch SWOT analysis separately using dedicated endpoint
      try {
        const swotResult = await getSWOTOutput();
        outputs['swot_analysis'] = swotResult.content;
      } catch (error) {
        console.error('Failed to fetch SWOT analysis:', error);
        outputs['swot_analysis'] = '';
      }
      
      setAgentOutputs(outputs);
      localStorage.setItem('brandorb_agent_outputs', JSON.stringify(outputs));
    } catch (error) {
      console.error('Failed to fetch agent outputs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "current":
        return <Clock className="h-4 w-4 text-blue-600" />;
      case "locked":
        return <Lock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-200";
      case "current":
        return "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-200";
      case "locked":
        return "bg-gray-100 dark:bg-gray-800/30 text-gray-500 dark:text-gray-400 border-gray-200";
    }
  };

  return (
   
        <div className="flex flex-1 flex-col gap-4 p-4">
          {/* Progress Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-blue-600" />
                      SWOT Analysis Progress
                    </CardTitle>
                    <CardDescription>
                      {completedSteps} of {steps.length} analysis components completed
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">{Math.round(totalProgress)}%</div>
                    <div className="text-sm text-muted-foreground">Complete</div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Progress value={totalProgress} className="h-3" />
              </CardContent>
            </Card>
          </motion.div>

          {/* SWOT Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {steps.map((step, index) => {
              const getStepDescription = (id: number) => {
                switch(id) {
                  case 1: return "Internal capabilities and resources that give a competitive advantage";
                  case 2: return "Internal limitations that hinder performance";
                  case 3: return "External factors that could be beneficial";
                  case 4: return "External factors that could negatively impact";
                  default: return "";
                }
              };

              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 * index }}
                >
                  <Card className={`${
                    step.status === "locked" ? "opacity-60" : ""
                  } hover:shadow-md transition-shadow duration-200 h-full`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium text-muted-foreground">
                              {step.id === 1 ? "Strengths" : 
                               step.id === 2 ? "Weaknesses" : 
                               step.id === 3 ? "Opportunities" : "Threats"}
                            </span>
                            {getStatusIcon(step.status)}
                          </div>
                          <CardTitle className="text-sm">{step.title}</CardTitle>
                          <CardDescription className="text-xs">
                            {getStepDescription(step.id)}
                          </CardDescription>
                        </div>
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${getStatusColor(step.status)}`}
                        >
                          {step.status === "completed" ? "Done" : 
                           step.status === "current" ? "Active" : "Locked"}
                        </Badge>
                      </div>
                    </CardHeader>
                    
                    <CardContent className="space-y-3">
                      {step.status === "current" && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="text-muted-foreground">Progress</span>
                            <span className="text-muted-foreground">{step.progress}%</span>
                          </div>
                          <Progress value={step.progress} className="h-1" />
                        </div>
                      )}
                      
                      <div className="pt-2">
                        <Button
                          asChild={step.status !== "locked"}
                          disabled={step.status === "locked"}
                          variant={step.status === "current" ? "default" : "outline"}
                          size="sm"
                          className="w-full"
                        >
                          {step.status === "locked" ? (
                            <span>
                              <Lock className="h-3 w-3 mr-2" />
                              Locked
                            </span>
                          ) : step.status === "completed" ? (
                            <Link href={`/dashboard/critical-report/${step.id}`}>
                              View Analysis
                              <ArrowRight className="h-3 w-3 ml-2" />
                            </Link>
                          ) : (
                            <Link href={`/dashboard/critical-report/${step.id}`}>
                              <Play className="h-3 w-3 mr-2" />
                              Analyze
                            </Link>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>

          {/* Final SWOT Report Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <StageSkeleton
              stage={{
                title: "Generate SWOT Analysis Report",
                description: "Compile all SWOT analysis into a comprehensive strategic assessment report",
                status: completedSteps === steps.length ? "current" : "locked",
                features: [
                  "Complete strengths and competitive advantages summary",
                  "Detailed weaknesses and improvement areas", 
                  "Market opportunities and growth potential analysis",
                  "Risk assessment and threat mitigation strategies",
                  "Strategic recommendations based on SWOT findings",
                  "Action plan for leveraging strengths and addressing weaknesses"
                ],
                estimatedTime: "3-5 minutes",
                actionText: "Generate SWOT Report",
                onAction: () => {
                  if (completedSteps === steps.length) {
                    window.location.href = "/dashboard/critical-report/report";
                  }
                }
              }}
            />
          </motion.div>
        </div>
  );
}

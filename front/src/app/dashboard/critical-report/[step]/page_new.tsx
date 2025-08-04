"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import StageSkeleton from "@/components/dashboard/StageSkeleton";
import { AgentOutputDisplay } from "@/components/dashboard/AgentOutputDisplay";
import { 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle,
  FileText,
  Target,
  TrendingUp,
  Users,
  DollarSign,
  Shield,
  Megaphone,
  Calculator,
  Clipboard
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useStepProgress } from "@/hooks/useStepProgress";
import { useState, useEffect } from "react";
import { getAgentOutput } from "@/services/agents";

// Step configuration mapping
const stepConfig: Record<string, {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  features: string[];
  estimatedTime: string;
  agentType?: 'financial_assessment' | 'legal_analysis' | 'market_analysis_competitors' | 'opportunities';
}> = {
  "1": {
    title: "Market Research",
    description: "Analyze market size, trends, and opportunities",
    icon: TrendingUp,
    agentType: "market_analysis_competitors",
    features: [
      "Market size analysis ($TAM, $SAM, $SOM)",
      "Industry trends and growth projections",
      "Market segmentation analysis",
      "Regulatory environment assessment"
    ],
    estimatedTime: "15-20 minutes"
  },
  "2": {
    title: "Competitive Analysis",
    description: "Identify and analyze direct and indirect competitors",
    icon: Target,
    agentType: "market_analysis_competitors",
    features: [
      "Competitor identification and mapping",
      "SWOT analysis for key competitors",
      "Pricing strategy comparison",
      "Market positioning analysis"
    ],
    estimatedTime: "20-25 minutes"
  },
  "3": {
    title: "Target Audience Analysis",
    description: "Define and validate your ideal customer personas",
    icon: Users,
    features: [
      "Customer persona development",
      "Pain point identification",
      "Customer journey mapping",
      "Market demand validation"
    ],
    estimatedTime: "15-20 minutes"
  },
  "4": {
    title: "Value Proposition Design",
    description: "Create compelling value propositions for your target market",
    icon: FileText,
    features: [
      "Value proposition canvas",
      "Unique selling proposition (USP)",
      "Benefit-feature mapping",
      "Competitive differentiation"
    ],
    estimatedTime: "10-15 minutes"
  },
  "5": {
    title: "Revenue Model Analysis",
    description: "Explore and validate potential revenue streams",
    icon: DollarSign,
    features: [
      "Revenue stream identification",
      "Pricing model analysis",
      "Customer lifetime value (CLV)",
      "Revenue forecasting"
    ],
    estimatedTime: "20-25 minutes"
  },
  "6": {
    title: "Risk Assessment",
    description: "Identify and analyze potential business risks",
    icon: Shield,
    agentType: "legal_analysis",
    features: [
      "Risk identification matrix",
      "Impact and probability analysis",
      "Mitigation strategies",
      "Contingency planning"
    ],
    estimatedTime: "15-20 minutes"
  },
  "7": {
    title: "Marketing Strategy",
    description: "Develop comprehensive marketing and customer acquisition strategy",
    icon: Megaphone,
    features: [
      "Marketing channel analysis",
      "Customer acquisition strategy",
      "Brand positioning",
      "Marketing budget allocation"
    ],
    estimatedTime: "25-30 minutes"
  },
  "8": {
    title: "Financial Projections",
    description: "Create detailed financial models and projections",
    icon: Calculator,
    agentType: "financial_assessment",
    features: [
      "3-year financial projections",
      "Break-even analysis",
      "Funding requirements",
      "ROI calculations"
    ],
    estimatedTime: "30-35 minutes"
  },
  "9": {
    title: "Implementation Plan",
    description: "Develop actionable roadmap for business execution",
    icon: Clipboard,
    agentType: "opportunities",
    features: [
      "Implementation timeline",
      "Resource requirements",
      "Key milestones",
      "Success metrics"
    ],
    estimatedTime: "20-25 minutes"
  }
};

export default function CriticalReportStepPage() {
  const params = useParams();
  const stepId = params.step as string;
  const { steps, isValidated } = useStepProgress();
  const [agentOutput, setAgentOutput] = useState<string>('');
  const [loading, setLoading] = useState(false);
  
  const step = stepConfig[stepId];
  const currentStep = steps.find(s => s.id === parseInt(stepId));
  
  useEffect(() => {
    if (isValidated && step?.agentType && !agentOutput) {
      fetchAgentOutput();
    }
  }, [isValidated, step?.agentType]);

  const fetchAgentOutput = async () => {
    if (!step?.agentType) return;
    
    setLoading(true);
    try {
      const result = await getAgentOutput(step.agentType);
      setAgentOutput(result.output);
    } catch (error) {
      console.error('Failed to fetch agent output:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (!step) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-surface">Step not found</h1>
          <p className="text-surface-muted mt-2">
            The requested step does not exist.
          </p>
          <Link href="/dashboard/critical-report">
            <Button className="mt-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Critical Report
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const currentStepNum = parseInt(stepId);
  const nextStepNum = currentStepNum + 1;
  const prevStepNum = currentStepNum - 1;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <Link href="/dashboard/critical-report">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-surface">{step.title}</h1>
            <p className="text-surface-muted mt-1">{step.description}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Badge className="bg-blue-100 text-blue-800 border-blue-200">
            Step {stepId} of 9
          </Badge>
          <Badge 
            variant="outline" 
            className={`text-xs ${
              currentStep?.status === "completed" 
                ? "bg-green-100 text-green-800 border-green-200"
                : currentStep?.status === "current"
                ? "bg-blue-100 text-blue-800 border-blue-200"
                : "bg-gray-100 text-gray-500 border-gray-200"
            }`}
          >
            {currentStep?.status === "completed" ? "Completed" :
             currentStep?.status === "current" ? "In Progress" : "Locked"}
          </Badge>
        </div>
      </motion.div>

      {/* Progress Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between text-sm text-surface-muted mb-2">
              <span>Step Progress</span>
              <span>{currentStep?.progress || 0}%</span>
            </div>
            <Progress value={currentStep?.progress || 0} className="h-2" />
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {/* Step Overview */}
          <StageSkeleton
            stage={{
              title: step.title,
              description: step.description,
              status: currentStep?.status || "locked",
              features: step.features,
              estimatedTime: step.estimatedTime,
              actionText: currentStep?.status === "completed" ? "Review Results" : "Start Analysis",
              onAction: () => {
                console.log(`Starting ${step.title} analysis...`);
              }
            }}
          />

          {/* Dynamic Agent Output */}
          {isValidated && step.agentType && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mt-6"
            >
              <AgentOutputDisplay
                agentType={step.agentType}
                output={agentOutput}
                title={step.title}
              />
            </motion.div>
          )}
        </div>

        {/* Navigation & Tips */}
        <div className="space-y-6">
          {/* Navigation */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Navigation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {prevStepNum > 0 && (
                  <Link href={`/dashboard/critical-report/${prevStepNum}`}>
                    <Button variant="outline" className="w-full justify-start">
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Previous Step
                    </Button>
                  </Link>
                )}
                
                {nextStepNum <= 9 && (
                  <Link href={`/dashboard/critical-report/${nextStepNum}`}>
                    <Button className="w-full justify-start">
                      Next Step
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </Link>
                )}
                
                {currentStepNum === 9 && currentStep?.status === "completed" && (
                  <Link href="/dashboard/critical-report/report">
                    <Button className="w-full justify-start bg-green-600 hover:bg-green-700">
                      Generate Final Report
                      <CheckCircle className="h-4 w-4 ml-2" />
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Tips */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">💡 Tips</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-surface-muted">
                  {stepId === "1" && "Focus on gathering quantitative data about market size and growth trends."}
                  {stepId === "2" && "Analyze both direct and indirect competitors to understand the full competitive landscape."}
                  {stepId === "3" && "Create detailed personas based on real customer research and interviews."}
                  {stepId === "4" && "Ensure your value proposition directly addresses identified customer pain points."}
                  {stepId === "5" && "Consider multiple revenue streams but validate them with potential customers."}
                  {stepId === "6" && "Don't just identify risks - develop concrete mitigation strategies."}
                  {stepId === "7" && "Align your marketing strategy with your target audience's preferred channels."}
                  {stepId === "8" && "Base projections on conservative assumptions and validate with market data."}
                  {stepId === "9" && "Break down implementation into specific, measurable milestones."}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import clsx from "clsx";
import { useState, useEffect } from "react";
import { getBMCOutput, parseBMCOutput } from "@/services/agents";
import dynamic from "next/dynamic";

// Dynamically import react-markdown to avoid SSR issues
const ReactMarkdown = dynamic(() => import("react-markdown"), { ssr: false });

const noteColors = {
  yellow: "bg-yellow-200 text-yellow-900",
  purple: "bg-purple-200 text-purple-900",
  blue: "bg-blue-200 text-blue-900",
  pink: "bg-pink-200 text-pink-900",
  orange: "bg-orange-200 text-orange-900",
};

const bmcQuestions = {
  "Key Partners": "What are your key partners to get competitive advantage?",
  "Key Activities": "What are the key steps to move ahead to your customers?",
  "Key Resources": "What resources do you need to make your idea work?",
  "Value Propositions": "How will you make your customers' life happier?",
  "Customer Relationships": "How often will you interact with your customers?",
  "Channels": "How are you going to reach your customers?",
  "Customer Segments": "Who are your customers? Describe your target audience in a couple of words.",
  "Cost Structure": "How much are you planning to spend on the product development and marketing for a certain period?",
  "Revenue Streams": "How much are you planning to earn in a certain period? Compare your costs and revenues.",
};

export default function BMCPage() {
  const [bmcData, setBmcData] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBMCData();
  }, []);

  const fetchBMCData = async () => {
    try {
      const output = await getBMCOutput();
      const parsed = parseBMCOutput(output);
      setBmcData(parsed);
    } catch (error) {
      console.error('Failed to fetch BMC data:', error);
      // Use empty data if fetch fails
      setBmcData({});
    } finally {
      setLoading(false);
    }
  };

  // Convert BMC data into blocks for rendering
  const bmcBlocks = Object.entries(bmcQuestions).map(([title, question], index) => ({
    title,
    question,
    content: bmcData[title] || "",
    color: Object.keys(noteColors)[index % Object.keys(noteColors).length] as keyof typeof noteColors,
  }));

  const topBlocks = bmcBlocks.slice(0, 7); // First 7 blocks for main grid
  const bottomBlocks = bmcBlocks.slice(7); // Last 2 blocks for bottom

  return (
    <div className="w-full min-h-screen bg-muted/50 flex flex-col items-center py-8 px-2">
      <h1 className="text-2xl font-bold mb-6 text-center">
        Business Model Canvas
      </h1>
      
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading Business Model Canvas...</div>
        </div>
      )}

      {!loading && (
        <>
          {/* Main BMC grid */}
          <div className="w-full max-w-7xl px-2 md:px-0 mx-auto grid grid-cols-1 md:grid-cols-6 grid-rows-[repeat(2,minmax(180px,1fr))] gap-4 mb-6">
            {/* Key Partners */}
            <div className="md:row-span-2 flex flex-col h-full">
              <BMCBlock
                title={topBlocks[0]?.title}
                question={topBlocks[0]?.question}
                content={topBlocks[0]?.content}
                color={topBlocks[0]?.color}
                className="h-full min-h-[380px]"
              />
            </div>

            {/* Key Activities */}
            <div className="flex flex-col h-full">
              <BMCBlock
                title={topBlocks[1]?.title}
                question={topBlocks[1]?.question}
                content={topBlocks[1]?.content}
                color={topBlocks[1]?.color}
                className="h-full"
              />
            </div>

            {/* Value Propositions */}
            <div className="md:row-span-2 flex flex-col h-full">
              <BMCBlock
                title={topBlocks[3]?.title}
                question={topBlocks[3]?.question}
                content={topBlocks[3]?.content}
                color={topBlocks[3]?.color}
                className="h-full min-h-[380px]"
              />
            </div>

            {/* Customer Relationships */}
            <div className="flex flex-col h-full">
              <BMCBlock
                title={topBlocks[4]?.title}
                question={topBlocks[4]?.question}
                content={topBlocks[4]?.content}
                color={topBlocks[4]?.color}
                className="h-full"
              />
            </div>

            {/* Customer Segments */}
            <div className="md:row-span-2 flex flex-col h-full">
              <BMCBlock
                title={topBlocks[6]?.title}
                question={topBlocks[6]?.question}
                content={topBlocks[6]?.content}
                color={topBlocks[6]?.color}
                className="h-full min-h-[380px]"
              />
            </div>

            {/* Key Resources */}
            <div className="flex flex-col h-full">
              <BMCBlock
                title={topBlocks[2]?.title}
                question={topBlocks[2]?.question}
                content={topBlocks[2]?.content}
                color={topBlocks[2]?.color}
                className="h-full"
              />
            </div>

            {/* Channels */}
            <div className="flex flex-col h-full">
              <BMCBlock
                title={topBlocks[5]?.title}
                question={topBlocks[5]?.question}
                content={topBlocks[5]?.content}
                color={topBlocks[5]?.color}
                className="h-full"
              />
            </div>
          </div>

          {/* Bottom blocks grid */}
          <div className="w-full max-w-7xl px-2 md:px-0 mx-auto grid grid-cols-1 md:grid-cols-2 gap-4">
            {bottomBlocks.map((block, index) => (
              <BMCBlock
                key={block.title}
                title={block.title}
                question={block.question}
                content={block.content}
                color={block.color}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

type BMCBlockProps = {
  title?: string;
  question?: string;
  content?: string;
  color?: keyof typeof noteColors;
  className?: string;
};

function BMCBlock({
  title,
  question,
  content,
  color = "yellow",
  className,
}: BMCBlockProps) {
  if (!title) {
    return (
      <Card className={clsx("rounded-xl shadow-sm", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-muted-foreground text-sm">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={clsx("rounded-xl shadow-sm", className)}>
      <CardHeader>
        <CardTitle className="text-lg font-bold mb-2 text-foreground">
          {title}
        </CardTitle>
        <CardDescription className="text-sm text-muted-foreground">
          {question}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2 min-h-[60px]">
        {content ? (
          <div className={`p-3 rounded-lg w-full ${noteColors[color]}`}>
            <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          </div>
        ) : (
          <div className="p-3 rounded-lg w-full bg-gray-100 text-gray-500 text-sm">
            No data available
          </div>
        )}
      </CardContent>
    </Card>
  );
}

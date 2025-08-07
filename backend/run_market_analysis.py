#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(__file__))

from agents.marketAnalysis_competitors_Agents import run_market_analysis_competitors

class SimpleState:
    def __init__(self, business_idea):
        self.business_idea = business_idea

# Read the business summary
business_summary_path = os.path.join(os.path.dirname(__file__), "agents", "output", "business_summary.txt")
if os.path.exists(business_summary_path):
    with open(business_summary_path, "r", encoding="utf-8") as f:
        full_description = f.read()
    # Extract key business info for API query (keep under 400 chars)
    business_description = "Men's clothing e-commerce platform for Italian market. Target: fashion-conscious men aged 25-40 in urban areas. High-quality Italian style clothing. Fulfillment center in Tunisia. Budget: 100,000 euros."
else:
    business_description = "Men's clothing e-commerce platform for Italian market. Target: fashion-conscious men aged 25-40."

print(f"Running market analysis for: {business_description[:100]}...")

# Create state and run analysis
state = SimpleState(business_description)
result_state = run_market_analysis_competitors(state)

print("Market analysis completed!")
print(f"Output saved to: {result_state.market_analysis}")

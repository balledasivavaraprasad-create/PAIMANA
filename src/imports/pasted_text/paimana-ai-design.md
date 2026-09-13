Design a high-fidelity, modern government-grade web application for **PAIMANA AI — an AI-driven Project Intelligence and Decision Support System for monitoring Central Sector Infrastructure Projects**.

The product should feel like a serious national-scale infrastructure intelligence platform, combining the visual quality of modern enterprise SaaS products with the trust, clarity and professionalism expected from a Government of India system. Avoid a generic admin dashboard appearance.

## Core Product Concept

The system transforms PAIMANA from primarily a monitoring/reporting platform into a predictive and intervention-oriented intelligence system.

Core workflow:

**PAIMANA Data → Feature Engineering → ML Prediction → DPHIS Risk Score → SHAP Explanation → Agentic Investigation → Recommendation → Alert**

DPHIS means **Dynamic Project Health & Intervention Score** and represents the overall project risk based on time, cost, progress, milestones, financial and implementation factors.

## Design Language

Use:

* Professional, minimal and data-dense enterprise UI
* Strong visual hierarchy
* Clean typography and generous spacing
* Subtle Indian government/public-infrastructure visual identity without excessive nationalistic decoration
* Light theme as the primary interface
* Dark navy/blue-gray foundation with restrained accent colors
* Use red/orange/amber/green only for risk states and status indicators
* Rounded cards, subtle borders and restrained shadows
* Clear charts rather than decorative graphics
* Accessible contrast and typography
* Responsive desktop-first design

The interface should communicate:

**Predictive intelligence + trust + explainability + actionability**

## Main Screens

### 1. Executive Overview Dashboard

Create a landing dashboard showing the national infrastructure portfolio.

Include:

* Total projects monitored
* Total project value
* Projects at low/moderate/high/critical risk
* Projects with increasing risk
* Projects requiring immediate intervention
* Overall portfolio health
* Cost overrun exposure
* Schedule delay exposure

Include:

* India map showing project/risk distribution
* Risk distribution chart
* Cost and schedule trend charts
* “Projects Requiring Attention” section
* Recent alerts
* AI-generated portfolio summary

Example AI insight:

“17 projects show rapidly increasing risk this month, primarily driven by schedule slippage and expenditure-progress divergence.”

Make this insight visually prominent.

### 2. Project Intelligence Page

Create a detailed project page.

Header:

* Project name
* Project ID
* Ministry/Department
* Sector
* State
* Project status
* DPHIS score
* Risk classification

Show:

* Physical progress
* Financial progress
* Original cost
* Revised cost
* Cumulative expenditure
* Original completion date
* Revised completion date

Create a large **DPHIS Risk Gauge** with the score and risk category.

Below it, show:

* Risk trend over time
* Progress trajectory
* Cost trajectory
* Milestone status
* Historical project snapshots

### 3. Explainable AI Panel

Create a dedicated **“Why is this project at risk?”** section.

Use a SHAP-style horizontal feature importance visualization.

Example:

Risk Drivers:

1. Schedule deviation — High impact
2. Cost escalation — High impact
3. Low progress velocity — Medium impact
4. Milestone delay — Medium impact
5. Weather disruption — Low impact

Clearly distinguish factors increasing and decreasing risk.

Add an AI explanation card:

“Risk increased primarily because physical progress declined relative to the planned trajectory while expenditure continued to rise.”

The explanation should feel evidence-based rather than like a generic chatbot response.

### 4. Agentic Investigation Page

Create an interface showing the AI investigating a high-risk project.

Title:

**AI Investigation**

Show an investigation timeline:

* Project data retrieved
* Historical performance analysed
* Cost trend examined
* Schedule deviation analysed
* Environmental conditions checked
* Similar projects compared
* Risk factors identified
* Intervention recommendation generated

Display the investigation results in structured cards.

Sections:

* Findings
* Evidence
* Root Causes
* Comparable Projects
* Recommended Actions
* Confidence

Make it visually clear that the AI is **investigating using multiple sources/tools**, rather than simply generating text.

### 5. AI Project Assistant

Create a conversational interface called:

**PAIMANA Intelligence Assistant**

Users should be able to ask:

“Why is Project P1024 at high risk?”

“Which projects have critical DPHIS scores?”

“Why has Project P1024's risk increased this month?”

“Compare this project with similar infrastructure projects.”

“What intervention should the concerned ministry consider?”

The assistant should answer using project data retrieved from the system.

Include citation/evidence chips such as:

* Project Data
* Historical Snapshot
* SHAP Analysis
* Environmental Data
* Peer Benchmark

Do not make it look like a generic ChatGPT clone. It should look like an **enterprise decision-support assistant**.

### 6. Risk & Portfolio Analytics

Create a page for analysing the entire project portfolio.

Include filters:

* Ministry
* Sector
* State
* Project type
* Risk level
* Cost range
* Completion period

Visualisations:

* Risk distribution
* Cost overrun distribution
* Schedule deviation
* Physical vs financial progress
* Risk trend
* Sector-wise risk
* State-wise risk

Allow users to drill down from portfolio → sector → project.

### 7. Alerts & Intervention Centre

Create an alert management page.

Show:

* Critical alerts
* Newly elevated risks
* Increasing-risk projects
* Recommended interventions
* Alert status

Example:

**CRITICAL — Project P1024**

DPHIS: 82 → 91

Primary driver: Schedule deviation

Recommended action:
“Review milestone recovery plan and contractor execution constraints.”

Include actions:

* View Project
* Investigate
* Assign
* Acknowledge

## Navigation

Create a professional sidebar:

PAIMANA AI

* Overview
* Projects
* Risk Intelligence
* Portfolio Analytics
* AI Investigations
* Intelligence Assistant
* Alerts
* Reports

Bottom:

* Settings
* User Profile

## Important UX Principle

The system should always move the user from:

**What is happening?**
→ **What is likely to happen?**
→ **Why is it happening?**
→ **What should we investigate?**
→ **What action should be taken?**

This distinction should be visible throughout the interface.

## Design System

Create reusable components for:

* Risk cards
* Project cards
* DPHIS gauge
* Risk badges
* Metric cards
* Charts
* Timeline
* AI insight cards
* SHAP explanation cards
* Alert cards
* Recommendation cards
* Chat messages
* Evidence/citation chips
* Filters
* Data tables
* Map markers
* Status indicators

Use consistent spacing, typography, icons and component variants.

## Prototype Interactions

Create a clickable prototype demonstrating this journey:

**Overview → Select High-Risk Project → Project Intelligence → View Risk Drivers → Launch AI Investigation → View Findings → View Recommended Intervention → Create/Acknowledge Alert**

Also demonstrate:

**Intelligence Assistant → Ask Project Question → Retrieve Project Data → Display Evidence-Based Answer**

The final prototype should clearly communicate that this is not merely a dashboard. It is an **AI-powered predictive infrastructure decision-support system**.

## Overall Visual Impression

The final design should look like a platform that could realistically be presented to senior government officials, infrastructure authorities and technical evaluators.

Prioritise:
**Clarity > Decoration**
**Evidence > Generic AI text**
**Actionability > Information overload**
**Professionalism > Futuristic gimmicks**

The product tagline can be:

**“Predict. Explain. Investigate. Intervene.”**

Subtitle:

**AI-driven intelligence for proactive infrastructure project monitoring.**

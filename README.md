# Dental Analytics Email Assistant

This repository contains the components for the Dental Analytics Email Assistant, a tool designed to transform dental practice key performance indicator (KPI) data from CSV/TSV files into concise, action-oriented executive emails.

## Project Purpose

The primary goal of this project is to automate the reporting of dental practice performance metrics to leadership. It aims to provide a system that can:

- Process structured data containing dental KPIs.
- Benchmark current performance against predefined Low, Target, and Stretch bands.
- Identify variances (Risks and Opportunities).
- Analyze trends over different timeframes.
- Suggest potential root causes and improvement levers based on research data.
- Generate SMART recommendations for action.
- Compose executive-level emails summarizing the findings and recommendations.

## Components

- `system-prompt.md`: This document contains the detailed instructions and configuration for the AI assistant, including its role, communication style, data input requirements, analysis workflow, email skeleton, dynamic rules, and output format.
- `convert_to_jsonl.py`: Likely a script used to convert raw data into a JSONL format suitable for processing or storage.
- `case_acceptance_chunks.jsonl`: Data related to case acceptance, potentially used for root cause analysis or benchmarking.
- `dental_kpi_metrics.csv`: A sample or input file containing dental KPI data.
- `Case Acceptance Science Research_.txt`: Research or reference material related to case acceptance, possibly used to inform the root cause analysis.

## How it Works (Conceptual Workflow)

1.  **Data Input**: KPI data is provided in CSV/TSV format.
2.  **Data Processing**: The data is validated and potentially converted (e.g., using `convert_to_jsonl.py`).
3.  **Analysis**: The AI assistant (configured by `system-prompt.md`) processes the data, performs benchmarking, variance analysis, trend analysis, and root cause hinting.
4.  **Recommendation Generation**: SMART recommendations are built based on the analysis.
5.  **Email Composition**: An executive email is generated using the predefined skeleton and dynamic rules.

## Setup and Usage

Specific setup and usage instructions depend on the environment where the AI assistant runs (e.g., a custom GPT or OpenAI Assistant). Refer to the `system-prompt.md` for the configuration details required to set up the assistant.

To use the system:

1.  Prepare your dental KPI data in the required CSV/TSV format.
2.  Upload the data to the configured AI assistant.
3.  The assistant will process the data and output a JSON object containing the composed email (in Markdown), flags, and a KPI summary table. 
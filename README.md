# Dental Email Assistant

A command-line tool that generates executive summary emails based on dental practice KPI metrics.

## Features

- Loads and validates dental KPI data from CSV files
- Analyzes KPI metrics using OpenAI's Assistant API
- Generates concise, executive-style summary emails (≤ 350 words)
- Highlights important metrics with warnings for low-band KPIs
- Provides SMART recommendations based on data analysis
- Supports saving outputs as markdown and JSON files

## Installation

This project uses Poetry for dependency management.

```bash
# Clone the repository
git clone https://github.com/yourusername/dental-email-assistant.git
cd dental-email-assistant

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

## Configuration

Set the required environment variables:

```bash
# For OpenAI API access
export OPENAI_API_KEY=your_openai_api_key

# Optional: Adjust logging level
export LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

You can also create a `.env` file in the project root with these variables.

## Usage

```bash
# Analyze KPI data and display results
dental-email --file path/to/your/kpi_data.csv

# Save the generated email and JSON to the output directory
dental-email --file path/to/your/kpi_data.csv --save
```

## Input Data Format

The tool expects a CSV file with the following columns:
- Date: Date of the metrics
- Location: Dental practice location
- MetricName: Name of the KPI metric
- Value: Actual metric value
- Target: Target metric value

Example:
```csv
Date,Location,MetricName,Value,Target
2023-01-01,Downtown Office,Case Acceptance Rate,68,75
2023-01-01,Downtown Office,Production Per Hour,350,400
...
```

## Project Structure

```
dental-email-assistant/
├── src/
│   ├── data/        # CSV loading/validation logic
│   ├── openai/      # OpenAI API interaction
│   ├── cli/         # Command-line interface
│   ├── email/       # Email formatting
│   ├── utils/       # Utilities like logging
│   └── main.py      # Application entry point
├── tests/           # Test files
├── output/          # Generated files
├── pyproject.toml   # Poetry configuration
└── README.md        # This file
```

## Development

### Running Tests

```bash
# Run the test suite
poetry run pytest

# Run with coverage report
poetry run pytest --cov=src
```

### Type Checking

```bash
# Run mypy type checker
poetry run mypy src
```

## License

[MIT](LICENSE) 
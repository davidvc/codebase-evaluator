# Codebase Evaluator

A sophisticated Python-based tool that analyzes codebases and generates comprehensive evaluation reports using AI-powered analysis. The tool helps development teams understand complex codebases by providing detailed insights about code structure, architecture, and adherence to best practices.

## Features

- **Automated Codebase Analysis**: Analyzes any Git repository by URL
- **AI-Powered Insights**: Utilizes OpenAI embeddings for intelligent code analysis
- **Comprehensive Reports**: Generates two detailed markdown reports:
  - High-level overview for quick understanding
  - Detailed assessment of code quality and architecture
- **Best Practices Evaluation**: Assesses adherence to:
  - SOLID principles
  - Hexagonal architecture
  - TDD best practices
  - Code maintainability principles
  - Acceptance testing patterns

## Architecture

The tool is built using a modular architecture with the following key components:

- `analyze_repo.py`: CLI entry point for running analyses
- `repo_indexer.py`: Handles repository scanning and indexing
- `workflow.py`: Orchestrates the analysis process using LangGraph
- `report_generator.py`: Generates analysis reports
- `report_writer.py`: Handles report output and formatting
- `types.py`: Core type definitions

The analysis workflow is implemented using LangGraph for orchestration and LangChain with OpenAI embeddings for intelligent code analysis.

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and configure your OpenAI API key

## Usage

Run the analysis on any Git repository:

```bash
python analyze_repo.py https://github.com/username/repository
```

The tool will:
1. Clone and index the repository
2. Analyze the codebase structure and patterns
3. Generate comprehensive reports in the `reports/` directory

## Reports Generated

### 1. Overview Report
- Project purpose and functionality
- Key components and architecture
- Main workflows and usage patterns
- Visual diagrams using Mermaid

### 2. Assessment Report
- Code quality evaluation
- Adherence to best practices
- Top 3 improvement opportunities
- Impact analysis on:
  - Maintainability
  - Performance
  - Security
  - Scalability

## Development

The project uses:
- Python 3.x
- LangGraph for workflow orchestration
- LangChain for AI-powered analysis
- ChromaDB for vector storage
- OpenAI embeddings for code understanding

Tests can be run using pytest:
```bash
pytest tests/
```

## Project Structure

```
├── analyze_repo.py      # Main CLI entry point
├── src/
│   ├── repo_indexer.py    # Repository analysis
│   ├── workflow.py        # LangGraph workflow
│   ├── report_generator.py # Report generation
│   ├── report_writer.py   # Report output
│   └── types.py          # Type definitions
├── tests/               # Test suite
├── docs/                # Documentation
└── reports/             # Generated reports
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[Add appropriate license information]

# Kelp Automated Deal Flow

**AI-ML GC 2025-26 Competition Entry**

An AI-powered investment teaser generation system that automatically creates professional "Blind" Investment Teaser presentations from company data.

## Overview

This system ingests company data from multiple sources (OnePager markdown files, PDFs, Excel files, web scraping) and generates:
- **3-slide Investment Teaser PowerPoint presentations** with anonymized company information
- **Citation documents** listing all data sources used

### Key Features

- **Hybrid Data Ingestion**: Parses OnePager.md, PDFs (balance sheets, credit reports), Excel files, and scrapes public websites
- **LLM-Powered Content Generation**: Uses GPT-4o-mini for intelligent content summarization and anonymization
- **Native PowerPoint Charts**: Bar charts for revenue/EBITDA/PAT trends with professional styling
- **Company Anonymization**: Replaces company names with project codenames (Titan, Luna, Aurora, etc.)
- **Sector-Specific Templates**: Different color schemes for Technology, Manufacturing, Pharma, Logistics, etc.
- **Kelp Branding**: Professional slides with Kelp logo, colors, and disclaimer

## Project Structure

```
AIML_GC/
├── src/
│   ├── main.py                 # Entry point
│   ├── config.py               # Configuration settings
│   ├── ingestion/
│   │   ├── data_loader.py      # Main data loading orchestrator
│   │   ├── markdown_parser.py  # OnePager.md parser
│   │   ├── pdf_parser.py       # PDF document parser
│   │   ├── excel_parser.py     # Excel file parser
│   │   └── web_scraper.py      # Website scraper
│   ├── generation/
│   │   ├── llm_generator.py    # GPT-4o-mini content generation
│   │   └── anonymizer.py       # Company name anonymization
│   ├── ppt/
│   │   ├── ppt_generator.py    # PowerPoint generation
│   │   └── chart_builder.py    # Native chart creation
│   ├── models/
│   │   └── company_data.py     # Data models
│   └── utils/
│       ├── logger.py           # Logging utilities
│       └── image_fetcher.py    # Stock image fetching
├── Company Data/               # Input company folders
├── output/                     # Generated PPTs and citations
├── requirements.txt            # Python dependencies
└── .env                        # API keys (not committed)
```

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AIML_GC
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Generate teaser for a single company

```bash
python src/main.py --company technology-ksolves
```

### Generate teasers for all companies

```bash
python src/main.py --all
```

### List available companies

```bash
python src/main.py --list
```

### Debug mode (verbose logging)

```bash
python src/main.py --company technology-ksolves --debug
```

### Skip citation generation

```bash
python src/main.py --company technology-ksolves --no-citations
```

## Input Data Format

Each company should have a folder in `Company Data/` with the naming convention:
```
<sector>-<company-name>/
```

Example: `technology-ksolves/`, `pharma-ind-swift/`

### Required Files

- `<CompanyName>-OnePager.md` - Main company information (required)

### Optional Files

- `*.pdf` - Balance sheets, credit reports, annual reports
- `*.xlsx` / `*.xls` - Financial statements

## Output

Generated files are saved to the `output/` directory:

- `Project_<Codename>_<sector>.pptx` - Investment teaser presentation
- `Project_<Codename>_Citations.docx` - Citation document

### Slide Structure

1. **Title Slide** - Project codename, sector, Kelp branding
2. **Business Overview** - Company description, key facts, products/services
3. **Financial Metrics** - Revenue/EBITDA/PAT chart, key ratios, market data
4. **Investment Highlights** - Strengths, opportunities, future plans
5. **Disclaimer** - Standard investment disclaimer

## Configuration

Key settings can be modified in `src/config.py`:

- `PROJECT_CODENAMES` - List of anonymization codenames
- `SECTOR_TEMPLATES` - Color schemes per sector
- `LLMConfig` - Model selection, temperature, max tokens
- `BrandingConfig` - Logo paths, colors, fonts

## Dependencies

Core dependencies (see `requirements.txt`):
- `python-pptx` - PowerPoint generation
- `openai` - LLM API
- `python-dotenv` - Environment variables
- `PyPDF2` - PDF parsing
- `openpyxl` - Excel parsing
- `beautifulsoup4` - Web scraping
- `requests` - HTTP requests
- `python-docx` - Word document generation

## API Costs

The system uses GPT-4o-mini for content generation:
- Average tokens per company: ~2,400
- Estimated cost per company: ~INR 0.06
- Total for 6 companies: ~INR 0.36

## Troubleshooting

### Common Issues

1. **UTF-8 encoding errors on Windows**
   - The system handles this automatically with UTF-8 console wrapping

2. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **API key not found**
   - Ensure `.env` file exists with `OPENAI_API_KEY`

4. **PDF/Excel parsing fails**
   - Install optional dependencies: `pip install PyPDF2 openpyxl`

## Team

AI-ML GC 2025-26 Competition Entry

## License

This project was created for the AI-ML GC 2025-26 competition.

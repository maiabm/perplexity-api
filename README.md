# Chemical Synthesis API

A Flask API that retrieves synthesis information for chemical compounds using their CAS numbers via Perplexity AI.

## Features

- Input: CAS number (Chemical Abstracts Service registry number)
- Output: Structured synthesis information including:
  - Reagents
  - Reaction conditions
  - Time and temperature
  - Yield
  - Source information (title, authors, journal, year, DOI, paper URL, summary)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `env.example` to `.env`:
     ```bash
     cp env.example .env
     ```
   - Edit `.env` and add your Perplexity AI API key:
     ```
     PERPLEXITY_API_KEY=your_actual_api_key_here
     ```

## Usage

### Start the API server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### Get Synthesis Information
```
GET /synthesis/<cas_number>
```

**Example:**
```bash
curl http://localhost:5000/synthesis/64-17-5
```

**Response Format:**
```json
{
  "cas_number": "64-17-5",
  "synthesis_methods": [
    {
      "reagents": ["ethanol", "acetic acid", "sulfuric acid"],
      "conditions": "room temperature, 24 hours",
      "time": "24 hours",
      "temp": "room temperature",
      "yield": "85%",
      "source": {
        "title": "Synthesis of Ethanol from Acetic Acid",
        "authors": "Smith, J. et al.",
        "journal": "Journal of Organic Chemistry, 2020, 85, 1234-1240",
        "year": "2020",
        "doi": "10.1021/acs.joc.0c00001",
        "paper_url": "https://pubs.acs.org/doi/10.1021/acs.joc.0c00001",
        "summary": "Complete experimental procedure description..."
      }
    }
  ],
  "total_methods": 1
}
```

#### Health Check
```
GET /health
```

#### API Information
```
GET /
```

## CAS Number Format

CAS numbers should follow the format: `XXXXXXX-XX-X`
- Example: `64-17-5` (ethanol)
- Example: `108-88-3` (toluene)

## Error Handling

The API includes comprehensive error handling for:
- Invalid CAS number format
- Perplexity AI API errors
- Network connectivity issues
- Missing synthesis information

## Environment Variables

- `PERPLEXITY_API_KEY`: Your Perplexity AI API key (required)

## Dependencies

- Flask: Web framework
- requests: HTTP client for API calls
- python-dotenv: Environment variable management

## Notes

- The API searches for peer-reviewed journal articles only
- Results are ranked by citation count
- Only single-step synthesis procedures are included
- All starting materials must be commercially available

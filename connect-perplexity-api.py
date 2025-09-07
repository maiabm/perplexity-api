import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

cas_number = ''

prompt = '''
Find the top 3 most cited peer-reviewed journal articles that describe experimental procedures for synthesizing **exactly the compound with CAS number {cas_number}**. **Do NOT include derivatives, analogs, or substituted versions.**
**Required Output Format:**
**Article 1: [Full Citation]**
- Journal: [Journal Name, Year, Volume, Pages]
- Citation Count: [Number of citations]
- DOI: [Digital Object Identifier if available]
- URL: [URL of the article]
**Single-Step Experimental Procedure:**
- Starting Materials: [List all reagents]
- Solvents: [Specify all solvents used]
- Reaction Conditions: [Temperature, time, atmosphere, pressure if specified]
- Experimental Method: [Write as a single paragraph describing the complete procedure as reported in the original paper]
- Yield: [Reported yield percentage]
**Article 2: [Repeat same format]**
**Article 3: [Repeat same format]**
**STRICT Search Constraints:**
- **TARGET COMPOUND ONLY**: The exact compound with the CAS number described with NO structural modifications
- **EXCLUDE ALL DERIVATIVES**: No substituted versions, analogs, or compounds with additional functional groups
- **SINGLE-STEP SYNTHESIS ONLY**: Exclude multi-step procedures, protection-deprotection sequences, or cascading reactions
- **DIRECT TRANSFORMATION**: Must be direct conversion of starting materials to the target compound
- Only include procedures from peer-reviewed journals (no patents, reviews, or book chapters)
- Rank articles by total citation count from Google Scholar or Web of Science
- Each procedure must produce the target compound as the sole product
- Exclude procedures where the target compound is an intermediate or side product
**Quality Requirements:**
- Provide exact experimental details for the single synthetic transformation
- Include temperatures and reaction times
- **Ensure all starting materials are commercially available** (no pre-synthesized intermediates)
- **Verify each procedure represents a direct conversion** to the target compound  that has the CAS number listed above
- Exclude any procedure requiring preliminary reactions or protective group chemistry
- Verify that each citation is from a different research group/institution
**REJECT if the procedure involves:**
- Any structural modifications to the target compound
- Multi-step sequences
- Protection/deprotection steps
- Click chemistry or other multi-component reactions
- Any compound other than the exact compound with the CAS number above
'''

# Get API key from environment variable
api_key = os.getenv('PERPLEXITY_API_KEY')
if not api_key:
    print("Error: PERPLEXITY_API_KEY environment variable not set")
    exit(1)

response = requests.post(
    'https://api.perplexity.ai/chat/completions',
    headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'sonar',
        'messages': [
            {
                'role': 'system',
                'content': 'You are an organic chemist who synthesizes compounds. Do not change the order of the naming conventions of the compounds.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'search_filter': 'academic'
    }
)

print(response.json())
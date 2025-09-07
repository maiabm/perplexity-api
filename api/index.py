from flask import Flask, request, jsonify
import requests
import re
import json
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Perplexity API configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_API_URL = 'https://api.perplexity.ai/chat/completions'

def create_synthesis_prompt(cas_number: str) -> str:
    """Create a structured prompt for Perplexity AI to find synthesis information."""
    return f'''
Find the top 3 most cited peer-reviewed journal articles that describe experimental procedures for synthesizing exactly the compound with CAS number {cas_number}. Do NOT include derivatives, analogs, or substituted versions.

**Required output format is as follows. The format is computer-readable; do not bold or italicize any text, and output nothing but what's specified here, no prologue or epilogue.**
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
- Ensure all starting materials are commercially available (no pre-synthesized intermediates)
- Verify each procedure represents a direct conversion to the target compound that has the CAS number listed above
- Exclude any procedure requiring preliminary reactions or protective group chemistry
- Verify that each citation is from a different research group/institution

**REJECT if the procedure involves:**
- Any structural modifications to the target compound
- Multi-step sequences
- Protection/deprotection steps
- Click chemistry or other multi-component reactions
- Any compound other than the exact compound with the CAS number above
'''

def call_perplexity_api(cas_number: str) -> Dict:
    """Make API call to Perplexity AI with the synthesis prompt."""
    if not PERPLEXITY_API_KEY:
        return {'error': 'PERPLEXITY_API_KEY environment variable not set'}
    
    prompt = create_synthesis_prompt(cas_number)
    
    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
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
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f'Perplexity API error: {response.status_code}', 'details': response.text}
            
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}'}

def parse_synthesis_response(response_text: str) -> List[Dict]:
    """Parse the Perplexity AI response to extract structured synthesis information."""
    articles = []
    
    # Split response by article sections
    article_sections = re.split(r'\*\*Article \d+:', response_text)
    
    for i, section in enumerate(article_sections[1:], 1):  # Skip first empty section
        try:
            article_data = {
                'reagents': [],
                'conditions': '',
                'time': '',
                'temp': '',
                'yield': '',
                'source': {
                    'title': '',
                    'authors': '',
                    'journal': '',
                    'year': '',
                    'doi': '',
                    'paper_url': '',
                    'summary': ''
                }
            }
            
            # Extract journal information
            journal_match = re.search(r'Journal:\s*([^\n]+)', section)
            if journal_match:
                article_data['source']['journal'] = journal_match.group(1).strip()
            
            # Extract DOI
            doi_match = re.search(r'DOI:\s*([^\n]+)', section)
            if doi_match:
                article_data['source']['doi'] = doi_match.group(1).strip()
            
            # Extract URL
            url_match = re.search(r'URL:\s*([^\n]+)', section)
            if url_match:
                article_data['source']['paper_url'] = url_match.group(1).strip()
            
            # Extract starting materials (reagents)
            reagents_match = re.search(r'Starting Materials:\s*([^\n]+)', section)
            if reagents_match:
                reagents_text = reagents_match.group(1).strip()
                # Split by common separators and clean up
                article_data['reagents'] = [r.strip() for r in re.split(r'[,;]', reagents_text) if r.strip()]
            
            # Extract solvents
            solvents_match = re.search(r'Solvents:\s*([^\n]+)', section)
            if solvents_match:
                solvents_text = solvents_match.group(1).strip()
                article_data['reagents'].extend([s.strip() for s in re.split(r'[,;]', solvents_text) if s.strip()])
            
            # Extract reaction conditions
            conditions_match = re.search(r'Reaction Conditions:\s*([^\n]+)', section)
            if conditions_match:
                article_data['conditions'] = conditions_match.group(1).strip()
                
                # Try to extract temperature and time from conditions
                temp_match = re.search(r'(\d+(?:\.\d+)?\s*°?[CK])', article_data['conditions'])
                if temp_match:
                    article_data['temp'] = temp_match.group(1)
                
                time_match = re.search(r'(\d+(?:\.\d+)?\s*(?:h|hr|hour|min|minute)s?)', article_data['conditions'], re.IGNORECASE)
                if time_match:
                    article_data['time'] = time_match.group(1)
            
            # Extract yield
            yield_match = re.search(r'Yield:\s*([^\n]+)', section)
            if yield_match:
                article_data['yield'] = yield_match.group(1).strip()
            
            # Extract experimental method as summary
            method_match = re.search(r'Experimental Method:\s*([^\n]+(?:\n(?!\*\*)[^\n]*)*)', section)
            if method_match:
                article_data['source']['summary'] = method_match.group(1).strip()
            
            # Try to extract title from the citation
            citation_match = re.search(r'\*\*Article {i}:\s*([^\n]+)'.format(i=i), response_text)
            if citation_match:
                article_data['source']['title'] = citation_match.group(1).strip()
            
            articles.append(article_data)
            
        except Exception as e:
            print(f"Error parsing article {i}: {str(e)}")
            continue
    
    return articles

@app.route('/synthesis/<cas_number>', methods=['GET'])
def get_synthesis_info(cas_number: str):
    """
    Get synthesis information for a compound by CAS number.
    
    Args:
        cas_number: Chemical Abstracts Service registry number
        
    Returns:
        JSON response with synthesis information including reagents, conditions, time, temp, yield, and source
    """
    # Validate CAS number format (basic validation)
    if not cas_number or not re.match(r'^\d{2,7}-\d{2}-\d$', cas_number):
        return jsonify({
            'error': 'Invalid CAS number format. Expected format: XXXXXXX-XX-X'
        }), 400
    
    # Call Perplexity API
    perplexity_response = call_perplexity_api(cas_number)
    
    if 'error' in perplexity_response:
        return jsonify({
            'error': 'Failed to retrieve synthesis information',
            'details': perplexity_response['error']
        }), 500
    
    # Extract the response text
    try:
        response_text = perplexity_response['choices'][0]['message']['content']
    except (KeyError, IndexError) as e:
        return jsonify({
            'error': 'Invalid response format from Perplexity AI',
            'details': str(e)
        }), 500
    
    # Parse the response
    synthesis_data = parse_synthesis_response(response_text)
    
    if not synthesis_data:
        return jsonify({
            'error': 'No synthesis information found for the provided CAS number',
            'cas_number': cas_number
        }), 404
    
    return jsonify({
        'cas_number': cas_number,
        'synthesis_methods': synthesis_data,
        'total_methods': len(synthesis_data)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'synthesis-api'})

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information."""
    return jsonify({
        'service': 'Chemical Synthesis API',
        'version': '1.0.0',
        'endpoints': {
            'synthesis': '/synthesis/<cas_number>',
            'health': '/health'
        },
        'example': '/synthesis/64-17-5'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

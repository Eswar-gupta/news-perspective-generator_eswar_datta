from flask import Flask, render_template, request, jsonify, url_for, session
import requests
from bs4 import BeautifulSoup
import logging
import sys
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def get_article_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
            
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if not text or len(text.split()) < 10:
            raise ValueError("Could not extract meaningful content from the article")
            
        return text
    except requests.RequestException as e:
        logging.error(f"Error fetching URL {url}: {str(e)}")
        raise ValueError(f"Could not access the article. The website might be blocking access. Please try a different news source.")
    except Exception as e:
        logging.error(f"Error processing URL {url}: {str(e)}")
        raise ValueError(f"Error processing the article: {str(e)}")

def generate_perspective(text, perspective):
    try:
        if perspective == "business":
            prompt = f"""Analyze this news article from a business perspective. Structure your response in the following format:

📈 **ECONOMIC IMPACT**
• **Market Dynamics**: [Key point about market changes]
• **Financial Impact**: [Key point about financial implications]
• **Economic Indicators**: [Key point about economic metrics]

💼 **MARKET IMPLICATIONS**
• **Industry Trends**: [Key point about industry changes]
• **Competition**: [Key point about competitive landscape]
• **Market Opportunities**: [Key point about potential opportunities]

🔄 **BUSINESS OPPORTUNITIES**
• **Growth Areas**: [Key point about expansion possibilities]
• **Strategic Moves**: [Key point about strategic implications]
• **Investment Potential**: [Key point about investment aspects]

💡 **KEY INSIGHTS**
• **Primary Impact**: [Most important business impact]
• **Future Outlook**: [Prediction or future implications]

Article: {text}

Format your response using markdown: Use **bold** for key terms and section headers, and bullet points for lists."""

        elif perspective == "political":
            prompt = f"""Analyze this news article from a political perspective. Structure your response in the following format:

🏛️ **POLICY IMPLICATIONS**
• **Policy Changes**: [Key point about policy modifications]
• **Legislative Impact**: [Key point about legal changes]
• **Regulatory Framework**: [Key point about regulations]

⚖️ **GOVERNANCE IMPACT**
• **Administrative Changes**: [Key point about governance]
• **Implementation**: [Key point about execution]
• **Institutional Effects**: [Key point about institutional impact]

👥 **STAKEHOLDER ANALYSIS**
• **Key Players**: [Important stakeholders involved]
• **Interest Groups**: [Affected groups]
• **Public Impact**: [Effect on general public]

🎯 **KEY TAKEAWAYS**
• **Critical Impact**: [Most significant political impact]
• **Future Developments**: [Expected political developments]

Article: {text}

Format your response using markdown: Use **bold** for key terms and section headers, and bullet points for lists."""

        else:  # UPSC
            prompt = f"""Analyze this news article from a UPSC (Civil Services) exam perspective. Structure your response in the following format:

📚 **ADMINISTRATIVE ASPECTS**
• **Governance**: [Key point about administration]
• **Policy Framework**: [Key point about policy]
• **Implementation**: [Key point about execution]

⚡ **CONSTITUTIONAL IMPLICATIONS**
• **Legal Framework**: [Key point about legal aspects]
• **Constitutional Provisions**: [Relevant provisions]
• **Precedents**: [Related cases or examples]

🌐 **SOCIO-ECONOMIC IMPACT**
• **Social Changes**: [Key point about social impact]
• **Economic Effects**: [Key point about economic impact]
• **Development Goals**: [Related development aspects]

📝 **EXAM FOCUS POINTS**
• **Key Topics**: [Important topics for study]
• **Previous Questions**: [Related UPSC questions]

Article: {text}

Format your response using markdown: Use **bold** for key terms and section headers, and bullet points for lists."""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating {perspective} perspective: {str(e)}")
        return f"Error generating {perspective} perspective: {str(e)}"

def generate_analysis(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating analysis: {str(e)}")
        return f"Error generating analysis: {str(e)}"

def get_prompt_for_perspective(perspective, article_text):
    if perspective == "business":
        prompt = f"""Analyze this news article from a business perspective. Structure your response in the following format:

📈 **ECONOMIC IMPACT**
• **Market Dynamics**: [Key point about market changes]
• **Financial Impact**: [Key point about financial implications]
• **Economic Indicators**: [Key point about economic metrics]

💼 **MARKET IMPLICATIONS**
• **Industry Trends**: [Key point about industry changes]
• **Competition**: [Key point about competitive landscape]
• **Market Opportunities**: [Key point about potential opportunities]

🔄 **BUSINESS OPPORTUNITIES**
• **Growth Areas**: [Key point about expansion possibilities]
• **Strategic Moves**: [Key point about strategic implications]
• **Investment Potential**: [Key point about investment aspects]

💡 **KEY INSIGHTS**
• **Primary Impact**: [Most important business impact]
• **Future Outlook**: [Prediction or future implications]

Article: {article_text}

Format your response using markdown: Use **bold** for key terms and section headers, and bullet points for lists."""

    elif perspective == "political":
        prompt = f"""Analyze this news article from a political perspective. Structure your response in the following format:

🏛️ **POLICY IMPLICATIONS**
• **Policy Changes**: [Key point about policy modifications]
• **Legislative Impact**: [Key point about legal changes]
• **Regulatory Framework**: [Key point about regulations]

⚖️ **GOVERNANCE IMPACT**
• **Administrative Changes**: [Key point about governance]
• **Implementation**: [Key point about execution]
• **Institutional Effects**: [Key point about institutional impact]

👥 **STAKEHOLDER ANALYSIS**
• **Key Players**: [Important stakeholders involved]
• **Interest Groups**: [Affected groups]
• **Public Impact**: [Effect on general public]

🎯 **KEY TAKEAWAYS**
• **Critical Impact**: [Most significant political impact]
• **Future Developments**: [Expected political developments]

Article: {article_text}

Format your response using markdown: Use **bold** for key terms and section headers, and bullet points for lists."""

    else:  # UPSC
        prompt = f"""Analyze this news article from a UPSC (Civil Services) exam perspective. Structure your response in the following format:

📚 **ADMINISTRATIVE ASPECTS**
• **Governance**: [Key point about administration]
• **Policy Framework**: [Key point about policy]
• **Implementation**: [Key point about execution]

⚡ **CONSTITUTIONAL IMPLICATIONS**
• **Legal Framework**: [Key point about legal aspects]
• **Constitutional Provisions**: [Relevant provisions]
• **Precedents**: [Related cases or examples]

🌐 **SOCIO-ECONOMIC IMPACT**
• **Social Changes**: [Key point about social impact]
• **Economic Effects**: [Key point about economic impact]
• **Development Goals**: [Related development aspects]

📝 **EXAM FOCUS POINTS**
• **Key Topics**: [Important topics for study]
• **Previous Questions**: [Related UPSC questions]

Article: {article_text}

Format your response using markdown: Use **bold** for key terms and section headers, and bullet points for lists."""

    return prompt

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return str(e)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        url = data.get('url')
        perspective = data.get('perspective', 'all')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        # Get article content
        article_text = get_article_content(url)
        
        # Store the article text in session for chatbot
        session['article_text'] = article_text
        
        # Generate perspective based on request
        result = {}
        perspectives = [perspective] if perspective != 'all' else ['business', 'political', 'upsc']
        
        for p in perspectives:
            prompt = get_prompt_for_perspective(p, article_text)
            try:
                response = model.generate_content(prompt)
                result[p] = response.text
            except Exception as e:
                logging.error(f"Error generating {p} perspective: {str(e)}")
                result[p] = f"Error generating {p} perspective. Please try again."
        
        # Store the analyzed text and results in session
        session['analysis_results'] = result
            
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        question = data.get('question')
        article_text = session.get('article_text')
        analysis_results = session.get('analysis_results', {})
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        if not article_text:
            return jsonify({'error': 'No article context found. Please analyze an article first.'}), 400
            
        # Create a comprehensive prompt using both article and analysis
        prompt = f"""Based on this article content and its analysis:

Article:
{article_text[:1500]}...

Analysis Summary:
"""
        # Add available analyses
        for perspective, analysis in analysis_results.items():
            prompt += f"\n{perspective.upper()} PERSPECTIVE:\n{analysis[:300]}...\n"
        
        prompt += f"""
Question: {question}

Provide a clear and informative answer based on both the article content and its analysis. 
If the question cannot be answered using the available information, say so.
Format your response using markdown for better readability."""
        
        try:
            response = model.generate_content(prompt)
            return jsonify({'response': response.text})
        except Exception as e:
            logging.error(f"Gemini API error: {str(e)}")
            return jsonify({'error': 'Failed to generate response from AI model'}), 500
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your question'}), 500

@app.route('/suggested_questions', methods=['GET'])
def suggested_questions():
    try:
        article_text = session.get('article_text')
        analysis_results = session.get('analysis_results', {})
        
        if not article_text:
            return jsonify({'error': 'No article context found. Please analyze an article first.'}), 400
            
        prompt = """Generate exactly 3 relevant questions about this article. Format your response as a comma-separated list of questions.

Article:
{text}

Example format:
What are the key economic implications discussed in the article?, How does this news affect international relations?, What are the potential long-term consequences?

Generate 3 questions:""".format(text=article_text[:1500])
        
        try:
            response = model.generate_content(prompt)
            questions = [q.strip() for q in response.text.split('?') if q.strip()]
            questions = [f"{q}?" for q in questions[:3]]  # Ensure we have exactly 3 questions
            
            if not questions:
                # Fallback questions if generation fails
                questions = [
                    "What are the main points discussed in this article?",
                    "What are the potential implications of this news?",
                    "How might this affect future developments?"
                ]
            
            return jsonify({'questions': questions})
        except Exception as e:
            logging.error(f"Gemini API error: {str(e)}")
            return jsonify({'error': 'Failed to generate questions'}), 500
        
    except Exception as e:
        logging.error(f"Error generating questions: {str(e)}")
        return jsonify({'error': 'An error occurred while generating questions'}), 500

if __name__ == '__main__':
    if not GOOGLE_API_KEY:
        print("Please set your GOOGLE_API_KEY in the .env file")
        sys.exit(1)
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

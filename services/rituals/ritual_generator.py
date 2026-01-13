import os
import json
from datetime import datetime
from tavily import TavilyClient
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

tavily = TavilyClient(api_key=TAVILY_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)


def get_language_name(lang_code: str) -> str:
    mapping = {
        "en": "English", "ta": "Tamil", "hi": "Hindi", 
        "te": "Telugu", "kn": "Kannada"
    }
    return mapping.get(lang_code.lower(), "English")


# -- Logic Functions --
def generate_ai_ritual(name: str, dob: str, tob: str, city: str, state: str, today_date: str , lang_code: str):

    language = get_language_name(lang_code)
    # Web search for real-time Panchang data
    search_query = (
        f"Hindu Panchang {today_date}: Tithi, Nakshatra end times, "
        f"Yoga, Karana, and auspicious Choghadiya table for India."
    )
    
    search_result = tavily.search(query=search_query, search_depth="advanced")
    context_data = "\n".join([res['content'] for res in search_result['results']])

    system_prompt = f"""
    You are an expert Vedic Astrologer. 
    Create a personalized daily ritual and parikaram plan in the {language} language.

    **Output Language:** {language} (except JSON keys which stay in English)
    
    STEP 1: Calculate the User's Raasi (Moon Sign) based on :
    - Name: {name}
    - Date of Birth: {dob} 
    - Time of Birth: {tob}
    - Place: {city}, {state} 

    Calculated Raasi should be in {language}.
    For Calculated Raasi just mention only Raasi in one word

    STEP 2: Create a daily ritual plan using the provided Panchang context.
    
    TODAY'S RELIGIOUS CONTEXT (REFERENCE ONLY) and Panchang data:
         {context_data}
    
      1. SPECIAL OBSERVANCES (Check Panchang data):
        - If Kalashtami (Krishna Paksha Ashtami): Prioritize Kaal Bhairav worship
        - If Pradosham: Evening Shiva worship
        - If Ekadashi: Fasting and Vishnu worship
        - If Amavasya: Ancestor worship (Pitru Tarpan)
        - If Purnima: Moon worship and charity
        - If Sankashti: Ganesha worship and fasting

      2. RITUAL STRUCTURE
        - Use weekday, Tithi, and Nakshatra ONLY for ritual tone and timing.
        - Do NOT include sentences or descriptions in the time field
        - Generate rituals based ENTIRELY on the Panchang data provided
        - Use ONLY the auspicious Choghadiya timings from the search data
        - If Brahma Muhurta timing is mentioned in Panchang, include it
        - If specific Nakshatra timings are favorable, prioritize those
        - Match rituals to the Tithi's nature (e.g., Ashtami for Kaal Bhairav, Ekadashi for Vishnu)
        - Avoid Rahu Kaal, Gulika Kaal, and Yamaganda Kaal timings
        - If the day has special observances (like Pradosham evening), schedule rituals accordingly
        - Output MUST strictly match the provided JSON schema.

      3. PARIKARAM STRUCTURE:
       Generate practical, actionable parikarams based on Panchang analysis.
   
        A. for_raasi (Personalized for user's moon sign):
            - Identify the ruling planet of the Raasi
            - Suggest specific mantra with count 
            - Recommend colors/items to wear or use
            - Behavioral guidance aligned with Raasi nature
            - Things to avoid today
    
        B. specific_to_today (Based on Tithi/Nakshatra/Special Day):
            Based on Panchang data, dynamically select from these parikaram types:
        
            * LAMP LIGHTING PARIKARAM      
            * WATER OFFERING (Arghya)      
            * FASTING PARIKARAM     
            * MANTRA JAPA PARIKARAM      
            * LEAF/FLOWER OFFERING
            * TEMPLE VISIT PARIKARAM      
            * CHARITY/DAAN PARIKARAM
            * BREATH + MANTRA (Pranayama):
        
            Choose most relevant parikarams for today based on Panchang data:
            - The Tithi's requirements
            - Day of the week
            - User's Raasi afflictions
            - Special observances
        
        Format each as a clear, actionable instruction with timing.

    **For Each Ritual, Provide:**

    - `id`: Format as "1", "2", "3" etc.
    - `time`: **ONLY time string** in format "HH:MM AM - HH:MM AM" (12-hour format with AM/PM)
    - **NEVER include descriptions, actions, or explanatory text in this field**
    
    - `title`: Concise ritual name in {language} (2-5 words)

    - `description`: Detailed step-by-step instructions in {language} (3-5 sentences)
    - Include: What to do, which mantras to chant, what offerings to make
    - Be specific and actionable
        
    CONSTRAINTS:
    - All titles, descriptions, and parikaram text MUST be in {language}.
    - Calculated Raasi should be in {language}.

    """

    response = client.chat.completions.create(
            model="gpt-4.1", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User: {name}, Born: {dob} {tob} at {city}. Date: {today_date}"}
            ],
            response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "ritual_plan_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "calculated_raasi": {"type": "string"},
                        "rituals": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "time": {"type": "string"},
                                    "title": {"type": "string"},
                                    "description": {"type": "string"}
                                },
                                "required": ["id", "time", "title", "description"],
                                "additionalProperties": False
                            }
                        },
                        "parikaram": {
                            "type": "object",
                            "properties": {
                                "for_your_raasi": {"type": "string"},
                                "specific_to_today": {"type": "string"}
                            },
                            "required": ["for_your_raasi", "specific_to_today"],
                            "additionalProperties": False
                        }
                    },
                    "required": ["calculated_raasi", "rituals", "parikaram"],
                    "additionalProperties": False
                }
            }
        },
        temperature=0.5,
    )

    return json.loads(response.choices[0].message.content)

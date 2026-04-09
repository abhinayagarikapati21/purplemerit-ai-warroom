import json
import os

def get_feedback_data() -> list:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'data', 'feedback.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def aggregate_user_sentiment() -> str:
    """Tool for Marketing/Comms: Returns an aggregated view of recent user feedback and mentions of bugs."""
    data = get_feedback_data()
    if not data:
        return "No feedback data found."
    
    # Sort by timestamp roughly if it was sorted
    # For this simulation, we'll just read through and bucket
    positive = 0
    neutral = 0
    negative = 0
    
    recent_complaints = []
    
    for item in data:
        if item['rating'] >= 4:
            positive += 1
        elif item['rating'] == 3:
            neutral += 1
        else:
            negative += 1
            recent_complaints.append(item['content'])
            
    summary = f"Sentiment Breakdown: {positive} Positive | {neutral} Neutral | {negative} Negative\n"
    summary += "Top Negative Themes (Critical Mentions):\n"
    # To avoid blowing up context, just grab unique generic complaints
    limited_complaints = list(set(recent_complaints))[:10]
    for c in limited_complaints:
        summary += f"- {c}\n"
        
    return summary

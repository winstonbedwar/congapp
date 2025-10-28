import re
import subprocess
import json

import firebase_admin
from firebase_admin import credentials, initialize_app, db

cred = credentials.Certificate("./orwell-ea558-firebase-adminsdk-fbsvc-3589223810.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://orwell-ea558-default-rtdb.firebaseio.com/'
})

ref = db.reference('personal-impact')  

billTitle = "To amend title 38, United States Code, to include eyeglass lens fittings in the category of medical services authorized to be furnished to veterans under the Veterans Community Care Program, and for other purposes."

# Example user
user = {
    "name": "Tanush",
    "age": 16,
    "ethnicity": "indian",
    "gender": "male",
    "income": 2000,
    "occupation": "computer scientist",
}

userName = "Tanush"

bill_summary = """
On September 26, 2025, the U.S. House of Representatives approved a bill to amend the federal securities laws to include eyeglass lens fittings in medical services authorized to be furnished to veterans under the Veterans Community Care Program. On September 9, 2018, the Honorable Carolyn M. Maloy of the United States District Court for the District of Columbia entered a final judgment in favor of the amended federal securities laws. Maloy and her co-sponsor, Representative Kevin C. Block of New York, introduced a bill on September 26, 2018, that amended the securities laws to provide for the purchase and maintenance of eyeglass lenses. According to the SEC's complaint filed in federal court in Manhattan, the amended securities laws provided for the purchase, maintenance, and purchase of eyeglasses violated the antifraud provisions of Section 17(a) of the Securities Act of 1933 and Section 10(b) of the Exchange Act of 1934 and Rule 10b-5 thereunder. The amended securities laws also provide for the issuance and purchase of securities. The SEC's complaint charges Maloy and Block with violating Section 105 of the Investment Advisers Act of 1940 and seeks permanent injunctions, disgorgement


"""

prompt = f"""
Bill summary:
{bill_summary}

User demographics:
{json.dumps(user)}

Task:
1. Explain briefly how this bill affects this user.
2. Then evaluate whether the effect is DIRECT, INDIRECT, or NONE using these definitions:

- DIRECT: The bill explicitly changes something that personally applies to the user
  (e.g. their age group, gender, income bracket, occupation duties).
- INDIRECT: The bill mainly affects people *around* the user or institutions
  they interact with, but not the user themselves.
- NONE: The bill has no clear link to the user's life circumstances.
Do not talk in first person. 

Example:
Bill: increases wages for workers under 18.
User: 16-year-old student → DIRECT
Bill: improves parental leave.
User: teenager → NONE
bill: improves contraception availability 
user: man --> NONE won't have pregnancy related health issues 

NOTE: even if the impact on the user is NONE please explain how the bill affects the users' community or people they may know.

End your answer with:
[Factors affected: ...]
[Impact type: DIRECT/INDIRECT/NONE]
"""

# Call local Ollama model (for example: llama3)
result = subprocess.run(
    ["ollama", "run", "llama3"],
    input=prompt.encode("utf-8"),
    stdout=subprocess.PIPE,
)
ai_text = result.stdout.decode("utf-8")

print("\n--- AI OUTPUT ---\n", ai_text)

# Extract mentioned factors
factors_match = re.search(r"\[Factors affected:(.*?)\]", ai_text, re.IGNORECASE)
if factors_match:
    factors = [f.strip().lower() for f in factors_match.group(1).split(",")]
else:
    factors = []

# Extract impact type from the AI output
impact_match = re.search(r"\[Impact type:\s*(DIRECT|INDIRECT|NONE)\]", ai_text, re.IGNORECASE)
if impact_match:
    impact = impact_match.group(1).lower()
else:
    # Fallback logic if AI doesn't provide impact type
    if len(factors) >= 2:
        impact = "direct"
    elif len(factors) == 1:
        impact = "indirect"
    else:
        impact = "none"

print(f"\nImpact assessment: {impact.upper()} (factors={factors})")

personal = {
    "res": ai_text,
    "impact": impact, 
    "factors": factors, 
    "billTitle": billTitle,
    "userName": userName
}

ref.push(personal)
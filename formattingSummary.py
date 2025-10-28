import subprocess



def format_summary_with_ollama(original_summary):
    """
    Uses Ollama to reformat a bill summary into bullet points
    """
    prompt = f"""
Take this bill summary and reformat it into clear, concise bullet points. 
Keep the same information and key terms, but make it more readable and scannable.
Use simple language where possible without changing technical terms or proper nouns.
Format as HTML unordered list (<ul><li>...) without any markdown.

Original summary:
{original_summary}

Instructions:
- Break into 3-5 bullet points
- Each bullet should be one clear idea. example breakdown can be: 1) history/context of bill 2) what does bill do/actual action 3) who does the bill affect?
- Keep all important names, numbers, and technical terms exactly as they are. Do not change any proper nouns 
- Make it easier to read but keep the meaning identical
-Do not output HTML list, output regular list with regular bullet points.
- Output ONLY the list, no other text. 

Output format:
<ul>
<li>First point here</li>
<li>Second point here</li>
</ul>
"""
    
    print("Calling Ollama...")
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
    )
    
    formatted_text = result.stdout.decode("utf-8").strip()
    
    return formatted_text

# TEST IT HERE - plug in your text
test_summary = """
On September 26, 2025, the U.S. House of Representatives approved a bill to amend the federal securities laws to include eyeglass lens fittings in medical services authorized to be furnished to veterans under the Veterans Community Care Program. On September 9, 2018, the Honorable Carolyn M. Maloy of the United States District Court for the District of Columbia entered a final judgment in favor of the amended federal securities laws. Maloy and her co-sponsor, Representative Kevin C. Block of New York, introduced a bill on September 26, 2018, that amended the securities laws to provide for the purchase and maintenance of eyeglass lenses. According to the SEC's complaint filed in federal court in Manhattan, the amended securities laws provided for the purchase, maintenance, and purchase of eyeglasses violated the antifraud provisions of Section 17(a) of the Securities Act of 1933 and Section 10(b) of the Exchange Act of 1934 and Rule 10b-5 thereunder. The amended securities laws also provide for the issuance and purchase of securities. The SEC's complaint charges Maloy and Block with violating Section 105 of the Investment Advisers Act of 1940 and seeks permanent injunctions, disgorgement
"""

print("="*60)
print("ORIGINAL SUMMARY:")
print("="*60)
print(test_summary)
print()

formatted = format_summary_with_ollama(test_summary)

print("="*60)
print("FORMATTED OUTPUT:")
print("="*60)
print(formatted)
print()

print("="*60)
print("CHARACTER COUNT:")
print("="*60)
print(f"Original: {len(test_summary)} characters")
print(f"Formatted: {len(formatted)} characters")
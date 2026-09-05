from google import genai

client = genai.Client()


def generate_lifestyle_suggestion(medicine_name, health_issue):

    prompt = f"""
You are ClockCare's general wellness assistant.

Medicine name:
{medicine_name}

Health issue/reason:
{health_issue if health_issue else "Not provided"}

Give SHORT and SIMPLE general healthy lifestyle suggestions
that may support the person's overall wellbeing.

Use the health issue as the main context.
The medicine name is only additional context.

Give 4 to 6 short and clearly separated bullet points.

FORMAT:
• Tip 1
• Tip 2
• Tip 3
• Tip 4
• Tip 5

Do NOT use Markdown.
Do NOT use ** or * symbols.
Start every tip with the bullet symbol •.
Keep each tip short and easy to read.

Suggestions can include:
- healthy food habits
- hydration
- sleep
- physical activity
- stress management
- general daily habits

IMPORTANT:
- Do NOT give medicine dosage.
- Do NOT tell the user to increase, decrease, stop, or change their medicine.
- Do NOT diagnose any disease.
- Do NOT claim that a specific food or lifestyle habit will cure the condition.
- Keep the advice general and easy to understand.
- Keep the answer under 100 words.
- End with a short reminder to consult a doctor or pharmacist for personal medical advice.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        print("LIFESTYLE GEMINI ERROR:", e)
        return ""
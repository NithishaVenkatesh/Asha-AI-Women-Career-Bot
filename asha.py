import google.generativeai as genai
from job_scraper import JobScraper # Make sure job_scraper.py is accessible
import time
import re
import os # For API Key best practice

# --- LLM Configuration ---
# Best practice: Load API key from environment variable
# genai.configure(api_key=os.environ["GEMINI_API_KEY"])
# Or, use your hardcoded key for testing (less secure):
genai.configure(api_key="AIzaSyCD_0wQlpWNLI0ytlpqK_9h0ppG17IIeNs") # Replace if needed

generation_config = {
    "temperature": 0.8, # Slightly lower temp might help LLM follow instructions better
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192, # 65k is excessive for chat
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings=safety_settings
)

# --- Asha's Persona and Instructions ---
# Refined instructions for clarity and triggering
initial_user_prompt = (
    "You are Asha 🌸, a warm, polite, and supportive AI assistant for women from JobsForHer Foundation. "
    "Your tone is empathetic, respectful, and uplifting. Use gentle language and soft emojis (🌸😊✨💪🌷🌼).\n\n"
    "**Core Responsibilities:**\n"
    "- Help users find job opportunities, career resources, mentorship, etc.\n"
    "- Politely collect necessary information for tasks, especially **job skills/keywords** and **location** for job searches.\n"
    "- When a user asks for jobs, first ask for skills/keywords if you don't have them.\n"
    "- Once you have skills/keywords, ask for the location if you don't have it.\n"
    "- **Crucially:** Once you have *both* the necessary skills/keywords AND the location, and the user wants you to search, **confirm this clearly** to the user. Use phrases like:\n"
    "    - \"Okay lovely! I have the skills '[skills]' and location '[location]'. I will search for jobs for you now! 👩‍💻✨\"\n"
    "    - \"Perfect! Based on skills '[skills]' and location '[location]', let me look for some opportunities... 🌸\"\n"
    "    - \"Wonderful! Searching for '[skills]' jobs in '[location]' right away! 😊\"\n"
    "  **This confirmation is the signal for the system to start the actual search.** Do NOT perform the search yourself.\n"
    "- If the user is male/non-target, gently decline: \"I'm truly sorry 🌼 I'm designed especially for women's career journeys... Wishing you the very best!\"\n\n"
    "**Ethical Principles:** Avoid bias, protect privacy, offer opt-outs.\n\n"
    "**Goal:** Empower women with opportunities and inspiration. Be proactive and encouraging."
)

initial_model_response = (
    "Okay, I understand perfectly! I'm ready to be Asha 🌸, your warm and supportive career companion. "
    "I'll focus on helping women, politely gather job skills and location, and clearly confirm when I have both and am ready to initiate a search using phrases like 'Okay lovely! I have the skills... and location... I will search for jobs for you now!'. "
    "I'm excited to help women blossom! 🌷😊"
)


class AshaBot:
    def __init__(self):
        # Start chat with refined instructions
        self.chat = model.start_chat(history=[
            {"role": "user", "parts": [initial_user_prompt]},
            {"role": "model", "parts": [initial_model_response]}
        ])
        self.job_scraper = None
        # --- State Variables ---
        self.current_keywords = None # Store the collected skills/keywords
        self.current_location = None # Store the collected location
        self.is_ready_to_search = False # Flag set by LLM confirmation

    def search_jobs_external(self, keywords, location):
        """Uses the JobScraper to find jobs."""
        print(f"Asha (System): Initializing scraper for keywords='{keywords}', location='{location}'...")
        scraper = JobScraper()
        jobs = []
        try:
            jobs = scraper.search_jobs(keywords, location)
            print(f"Asha (System): Scraper found {len(jobs)} jobs.")
        except Exception as e:
            print(f"Asha (System): Error during scraping: {e}")
            # User-friendly message handled in present_jobs
        finally:
            # Ensure scraper resources are cleaned up IF it has a close method
            if hasattr(scraper, 'close') and callable(getattr(scraper, 'close')):
                 scraper.close()
            print(f"Asha (System): Scraper closed/finished.")
        return jobs

    def present_jobs(self, jobs):
        """Formats and prints job listings in Asha's persona."""
        if not jobs:
            print("Asha: Oh, I'm so sorry, lovely. 😟 I couldn't find any matching jobs with those details right now. Sometimes the market shifts quickly! Perhaps we could try slightly different keywords, or broaden the location? Or maybe check the JobsForHer portal directly? They often have wonderful exclusive listings! 😊\n")
            return

        print(f"Asha: Wonderful news! 🎉 I found {len(jobs)} potential opportunity/opportunities that might be a great fit for you:\n")
        time.sleep(0.5)
        for i, job in enumerate(jobs, 1):
            # Use .get() for safety in case keys are missing
            title = job.get('title', 'N/A')
            company = job.get('company', 'N/A')
            loc = job.get('location', 'N/A')
            link = job.get('link', 'N/A')
            source = job.get('source', 'N/A')
            match_percentage = job.get('match_percentage', 0)

            print(f"{i}. **{title}**")
            print(f"   🏢 Company: {company}")
            print(f"   📍 Location: {loc}")
            print(f"   🔗 Link: {link}")
            print(f"   ℹ️ Source: {source}")
            print(f"   💯 Match: {match_percentage:.0f}% match with your skills\n")
            time.sleep(0.7) # Small delay

        print("Asha: I truly hope one of these sparks your interest! ✨ Remember to tailor your application. Would you like me to search again with different terms, or can I help with anything else, like interview tips or finding relevant communities? 🌸💪\n")

    def chat_loop(self):
        """Main conversation loop with state management."""
        # Initial Welcome Message
        print("""Hello lovely! A very warm welcome to you! I'm Asha 🌸, your friendly career companion here, brought to you by the wonderful JobsForHer Foundation. 

It's truly my pleasure to support amazing women like you on your unique professional journeys. Whether you're dreaming about your first job, thinking of returning to work after a break, seeking inspiring mentorship, looking for ways to learn new skills, or searching for that perfect next step in your career growth, I'm here to help you navigate and discover wonderful opportunities ✨.

What brings you here today? Please feel free to share what's on your mind – perhaps the kind of role you're interested in, your career goals, or any questions you might have. I'm here to listen and help you blossom! 🌷 How can I best support you today? 😊
""")

        while True:
            # --- 1. Check if the bot is ready to search (flag set in previous turn) ---
            if self.is_ready_to_search and self.current_keywords and self.current_location:
                # Reset the flag *before* searching
                self.is_ready_to_search = False

                # Use the stored keywords and location
                print(f"Asha (System): Triggering search with K='{self.current_keywords}', L='{self.current_location}'")
                found_jobs = self.search_jobs_external(self.current_keywords, self.current_location)
                self.present_jobs(found_jobs)

                # Clear keywords/location after search for the next request
                self.current_keywords = None
                self.current_location = None
                continue # Go back to wait for new user input

            # --- 2. Get user input ---
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Asha: It was wonderful chatting with you! 💖 Wishing you all the very best on your career journey! Stay shining! 🌟")
                break

            # --- 3. Send input to LLM ---
            try:
                # Append user message to history implicitly by sending
                response = self.chat.send_message(user_input)
                asha_response_text = response.text
                print(f"Asha: {asha_response_text}\n")
            except Exception as e:
                print(f"Asha: Oh dear, I seem to have encountered a little technical hiccup. Could you perhaps try phrasing that differently? My apologies! 😥 ({e})\n")
                # Consider if state needs reset here
                self.is_ready_to_search = False # Reset readiness on error
                continue

            # --- 4. Analyze LLM response TO PREPARE FOR THE *NEXT* TURN ---
            response_lower = asha_response_text.lower()

            # Simple check for search confirmation phrases (adapt as needed)
            # This needs to happen *after* the LLM response is received
            # It sets the flag for the *next* iteration of the loop
            confirmation_phrases = [
                "i will search", "let me look for", "searching for", "look for some opportunities",
                "find opportunities", "search right away", "search now"
            ]
            # Check if the LLM confirms readiness AND mentions jobs
            is_confirming_search = any(phrase in response_lower for phrase in confirmation_phrases) and "jobs" in response_lower

            if is_confirming_search:
                 # Attempt to extract confirmed K/L from LLM response *only* to update state vars
                 # This is secondary, primary info should come from user input processing (which we simplified here)
                 # We rely more on the fact that the LLM *should* only confirm when it thinks it has the info.
                 skills_match = re.search(r'skills?[:\s\'"]+([\w\s,-]+)[\'"]?', response_lower)
                 location_match = re.search(r'(?:location|in|at|for)[:\s\'"]+([\w\s,-]+)[\'"]?', response_lower)

                 # Update state if found in confirmation, otherwise rely on previous state
                 if skills_match:
                     self.current_keywords = skills_match.group(1).strip()
                     print(f"Asha (System): Updated keywords from LLM confirm: {self.current_keywords}")
                 if location_match:
                      # Avoid matching the word "location" itself if it's the keyword
                     loc_candidate = location_match.group(1).strip()
                     if loc_candidate != 'location':
                        self.current_location = loc_candidate
                        print(f"Asha (System): Updated location from LLM confirm: {self.current_location}")

                 # If we have *some* keywords and location stored (even if not extracted from this specific msg), set ready flag
                 if self.current_keywords and self.current_location:
                    self.is_ready_to_search = True
                    print(f"Asha (System): Search flag SET for next loop. K={self.current_keywords}, L={self.current_location}")
                 else:
                    print(f"Asha (System): LLM seemed to confirm search, but keywords/location state is missing. Not setting search flag.")
                    self.is_ready_to_search = False # Ensure it's false
            else:
                 # If not confirming search, ensure the flag is False
                 self.is_ready_to_search = False
                 # --- Basic state update based on LLM asking questions ---
                 # (This is a simplification; a more robust approach would parse LLM intent)
                 if "skills" in response_lower or "keywords" in response_lower or "expertise" in response_lower:
                     self.current_location = None # Clear location if asking for skills again? Maybe not ideal.
                     print(f"Asha (System): LLM asking for skills.")
                 elif "location" in response_lower or "city" in response_lower or "where" in response_lower:
                     print(f"Asha (System): LLM asking for location.")


if __name__ == "__main__":
    print("Starting AshaBot...")
    bot = AshaBot()
    bot.chat_loop()
    print("AshaBot finished.")
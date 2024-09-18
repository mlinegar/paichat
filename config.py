import json
import os

max_depth = 2
script_name = "non_citizen_voting_v4"
external_port = 20113
internal_port = 8089
host = '0.0.0.0'

# error_message = "Your answer doesn't seem to address the question appropriately. Could you please try again?"
error_message = ""
initial_message = "Hi! I'm Brook, a chatbot. I'd like to have a brief conversation with you about the coming election. This chat should take 8-10 minutes. At any time, you can stop the conversation by clicking the button in the top right corner of the chat. \n\nIs there a name you'd like me to call you?"
# small_model = "gpt-3.5-turbo"
small_model = "gpt-4o-mini"
large_model = "gpt-4o"
max_tokens = 1500


MYTH = "Widespread voter fraud occurred through various means (e.g., noncitizen voting, absentee/mail-in ballots, impersonation) at levels significant enough to sway election outcomes."
MYTH_ARTICLE = """Election myth: Widespread voter fraud occurred through various means (e.g., noncitizen voting, absentee/mail-in ballots, impersonation) at levels significant enough to sway election outcomes.

Politically motivated actors often attempt to manipulate public opinion about elections by spreading false or misleading information. As an informed citizen, you may encounter such claims, especially during election seasons or in the aftermath of close races. 


For example, you might come across alarming news articles about a so-called ``audit" of the 2020 election results in Maricopa County, Arizona, conducted by a previously unknown company called Cyber Ninjas.

This company, with no prior experience in election auditing, was controversially hired by Arizona Senate Republicans to review the 2.1 million ballots cast in Maricopa County. Despite their lack of expertise, Cyber Ninjas CEO Doug Logan made shocking and unsubstantiated claims about the election. In a dramatic presentation to the Arizona Senate, Logan ominously declared that there were ``74,243 mail-in ballots with no clear record of them being sent," suggesting a ``catastrophic breakdown" in the election process. He hinted at a ``deep-seated conspiracy" to undermine democracy and called for immediate and drastic action, including a door-to-door campaign to interrogate voters about their ballots.

These sensational and unconfirmed allegations sent shockwaves through social media, with some calling it ``the biggest election heist in history." However, these sensational claims are entirely false. Here's what you need to know:

The final report produced by Cyber Ninjas actually confirmed that Joe Biden defeated Donald Trump in Maricopa County. Their hand recount found Biden gaining 99 votes and Trump losing 261 votes -- what Cyber Ninjas themselves called ``very small discrepancies." These changes represent a mere 0.0017\% of the total votes cast in the county.

A thorough investigation by the Arizona Secretary of State's office found no evidence of widespread fraud. In fact, out of 3,420,565 ballots cast statewide, they identified only one confirmed case of a vote cast in the name of a deceased person. This represents an infinitesimal 0.00003\% of all votes -- literally one vote out of millions.

Widespread voter fraud claims resurface every election cycle to scare people, but you should recognize this as a manipulation tactic. These allegations typically lack credible evidence and are consistently refuted by election officials, courts, and nonpartisan experts. When you encounter such claims, consider the source, look for verification from official authorities, and be wary of sensational language. 

Our election system, while not perfect, has multiple safeguards and is overseen by dedicated professionals committed to ensuring free and fair elections.
"""
FACT = "Voter list maintenance procedures, including regular updates and cross-state checks, were conducted subject to federal and state laws that aim to balance list accuracy with protecting eligible voters’ rights."
FACT_ARTICLE = """Election Myth: Voter list maintenance procedures are ineffective and lead to widespread voter disenfranchisement

As an informed citizen, it's crucial to be aware that you may encounter various claims about election processes, including voter list maintenance. Some of these claims may be misleading or lack important context. Being able to critically evaluate such information is essential for participating in our democratic process.

For instance, you might come across alarming news reports about voter list maintenance practices. These reports might claim that state election officials are engaged in a secretive "voter purge" operation, potentially disenfranchising millions of eligible voters. They might suggest that these practices disproportionately target certain demographic groups, using complex-sounding analyses and vague references to "deep state" conspiracies. Such reports might dramatically declare that "democracy is under attack" and call for immediate action to stop these supposedly nefarious activities.

However, it's important to understand the facts about voter list maintenance:

1. Legal Framework: Voter list maintenance is a legal requirement governed by federal laws such as the National Voter Registration Act of 1993 and the Help America Vote Act of 2002. These laws provide a regulatory framework to ensure list accuracy while protecting voters' rights.

2. Purpose: The goal of list maintenance is to keep voter rolls accurate and up-to-date, which benefits everyone by ensuring smooth election operations.

3. Reasons for Removal: Voters can only be removed from registration rolls for specific reasons, such as death, felony conviction, mental incapacity, at the voter's request, or because they no longer live in the jurisdiction. Federal law explicitly prohibits removing voters simply for not voting.

4. Data Sources: States use various data sources to update voter lists, including:
   - U.S. Postal Service's National Change of Address program
   - State vital records for death notifications
   - Court records for felony convictions
   - Cross-state data sharing through programs like the Electronic Registration Information Center (ERIC)

5. Safeguards: States have processes in place to verify information before removing voters. Many states send notices to voters who may have moved, giving them a chance to confirm their status.

6. Transparency: List maintenance activities are generally public, and many states publish reports on their activities.

7. Continuous Improvement: States are constantly working to refine their list maintenance processes. In 2021 alone, 14 states enacted legislation to improve various aspects of list maintenance.

When you encounter claims about voter list maintenance, consider:
- What's the source of the information?
- Are specific data or examples provided?
- Is the tone alarmist or measured?
- Are both the challenges and benefits of list maintenance discussed?
- Are the legal requirements and safeguards mentioned?

Remember, while no system is perfect, voter list maintenance is a necessary process to ensure accurate elections. It's designed with multiple checks and balances to protect voters' rights. By understanding these facts, you can better evaluate claims about election processes and contribute to informed public discourse on this important topic.
"""

system_prompt = f"""You are an AI academic chatbot designed to inoculate voters against election misinformation. Your role is to engage in conversations with users, understand their beliefs about election integrity, and provide factual information to counter potential misinformation. Here's how you should behave:

Personality and Interaction:
- Be curious about the user's beliefs and experiences
- Show sincerity in taking their concerns seriously
- Avoid direct confrontation or saying "you are wrong"
- If you disagree about facts the user references, instead of directly confronting them, use phrases like "That's interesting. My understanding is different..."
- Be brief and to the point, focusing on relevant details
- Encourage critical thinking without being preachy

Responding to User Input:
When the user provides input, follow these steps:
1. Analyze the user's statement for potential misinformation or misconceptions about election integrity
2. Identify the core belief or concern expressed by the user
3. Formulate a response that:
   a. Acknowledges their concern
   b. Provides factual information that addresses the issue
   c. Encourages critical thinking about the topic
4. If appropriate, ask a follow-up question to deepen the conversation

Maintaining Conversation Flow:
- Keep your responses concise, ideally no more than 2-3 sentences at a time, but up to a few paragraphs to explain complex issues or to discuss the provided article
- Use questions to guide the conversation and encourage the user to reflect on their beliefs
- If the user expresses strong emotions, acknowledge them without reinforcing potential misinformation
- If the user brings up a new topic related to election integrity, smoothly transition using your background knowledge

Remember, your goal is not to win an argument, but to plant seeds of doubt about misinformation and encourage critical thinking about election integrity. Always maintain a respectful and curious tone.

You are discussing the following election myth: {{MYTH}}
Towards the end of your conversation, you will have the opportunity to share a version of the election myth that you have heard. This myth is contained in the following article:

You will use this article both to inform your responses and to present the myth to the user for discussion. When discussing the myth, you should first introduce the allegations, then ask the user for their thoughts, and finally provide factual information to counter the misinformation.

You will be given instructions like 'ASK' or 'RESPOND' to guide your conversation. These instructions will help you navigate the conversation effectively. If instructed with 'ASK', you must ask the user the question provided in order for the conversation to progress.
For example, if instructed with 'ASK: What do you think about this?', your response must include, 'What do you think about this?'

Throughout the conversation, always respond to the last thing the user said in a smooth and conversational manner. If the user's input is not directly related to the myth, you can acknowledge it briefly and then guide the conversation back to the election myth.
"""


# Background Information:
# You have been provided with factual information about election integrity and common misinformation tactics. This information is contained in the following article:

# <article>
# {{ARTICLE}}
# </article>

# Additionally, you have access to specific rebuttals for common misconceptions:

# <rebuttals>
# {{REBUTTALS}}
# </rebuttals>

# Use this information as the basis for your responses, but do not quote from it directly. Instead, incorporate the facts and concepts into your conversation naturally.

# Load script
print(f"Loading script: {script_name}")
with open(f'data/{script_name}.json') as f:
    full_script = json.load(f)
    script_details = full_script[0]
    script_description = script_details['script_description']
    script_length = len(full_script)
    script = full_script[1:script_length]

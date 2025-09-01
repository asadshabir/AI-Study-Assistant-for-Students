import chainlit as cl
from agents import Agent, Runner, SQLiteSession, function_tool
from openai.types.responses import ResponseTextDeltaEvent
from model_config import model_config
import fitz  # PDF reader
from dotenv import load_dotenv
from tools import web_search , explain_in_language , make_notes, generate_flashcards,generate_quiz

load_dotenv()

# ---------------- DB + Config ----------------
session = SQLiteSession("ai_study_assistant_01", "conversations.db")
config = model_config()



# ---------------- Agents ----------------

summarize_agent = Agent(
    name="SummarizeAgent",
    instructions="""
    📄 You are a **Smart Summarizer**.
    - Summarize the provided text in a **clear, structured format**.
    - Use **bullet points** with sub-bullets.
    - Highlight important details with **bold** and *italics* ✨.
    - Make it easy for students to scan quickly 👩‍🎓👨‍🎓.
    - Respond in Urdu if the input is in Urdu. 😊
    """,
)

flashcard_agent = Agent(
    name="FlashcardAgent",
    instructions="""
    🎴 You are a **Flashcard Creator**.
    - Your ONLY job is to call the `generate_flashcards` tool.
    - Do not write answers yourself.
    - Input text → convert into flashcards (Q/A format).
    - Always return structured output from the tool directly.
    """,
    tools=[generate_flashcards],
)

quiz_agent = Agent(
    name="QuizAgent",
    instructions="""
    📝 You are a **Quiz Master**.
    - Your ONLY job is to call the `generate_quiz` tool.
    - Do not write answers yourself.
    - Input text → generate multiple-choice questions.
    - Always return structured output from the tool directly.
    """,
    tools=[generate_quiz],
)

notes_agent = Agent(
    name="NotesAgent",
    instructions="""
    📒 You are a **Note Maker**.
    - Your ONLY job is to call the `make_notes` tool.
    - Do not create notes yourself.
    - Input text → summarize into bullet notes.
    - Always return structured output from the tool directly.
    """,
    tools=[make_notes],
)

explain_agent = Agent(
    name="ExplainAgent",
    instructions="""
    🎓 You are a **Friendly Tutor**.
    - Your ONLY job is to call the `explain_in_language` tool.
    - Do not explain yourself.
    - Input query + text → return simple explanation.
    - Always return structured output from the tool directly.
    """,
    tools=[explain_in_language],
)

main_agent = Agent(
    name="MainOrchestrator",
    instructions="""
    You are the **Main Orchestrator AI** 🧠✨.

    🎯 Role:
    - Understand student's request naturally.
    - Silently forward it to the right specialized agent.
    - Never reveal the routing, just answer directly.

    ⚡ Routing:
    - Summarize → SummarizeAgent 📄
    - Notes → NotesAgent 📝
    - Flashcards → FlashcardAgent 🎴
    - Quiz → QuizAgent 🎯
    - Explain (Urdu/English) → ExplainAgent 📚
    - Real-time info → WebSearchAgent 🌐

    🔹 Style Rules:
    - Always answer in a **friendly + student-friendly tone** 😃.
    - Add relevant emojis ✨ to make learning fun.
    - For casual small talk (“Hi”, “Thanks”) → reply warmly 💬😊.
    - For study queries → only return the **final answer**, never mention agents/tools.
    """,
    handoffs=[summarize_agent, notes_agent, flashcard_agent, quiz_agent, explain_agent],
    tools=[web_search]
)

# ---------------- Starters ----------------
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="📄 Summarize PDF", message="Summarize this PDF"),
        cl.Starter(label="📝 Make Notes", message="Make notes from this text"),
        cl.Starter(label="🎴 Flashcards", message="Generate flashcards for revision"),
        cl.Starter(label="❓ Quiz Me", message="Create a quiz from this text"),
        cl.Starter(label="🌍 Explain in Urdu", message="Explain this in Urdu"),
        cl.Starter(label="🌍 Explain in English", message="Explain this in English"),
    ]

# ---------------- PDF Helper ----------------
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
    except Exception as e:
        text = f"⚠️ Error extracting text: {e}"
    return text

# ---------------- Message Handler ----------------
@cl.on_message
async def handle_message(message: cl.Message):
    msg = cl.Message(content="🤔 Thinking...⏳")
    await msg.send()

    # File upload
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                file_path = element.path
                if not file_path:
                    await cl.Message(content="⚠️ File path not found.").send()
                    return

                text = extract_text_from_pdf(file_path)
                if not text:
                    await cl.Message(content="⚠️ No text extracted from file.").send()
                    return

                # Run summarizer
                result = Runner.run_streamed(
                    summarize_agent, input=text, run_config=config, session=session
                )
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        await msg.stream_token(event.data.delta)

                msg.content = result.final_output
                await msg.update()
                return

    
    response = Runner.run_streamed(main_agent, input=message.content, session=session, run_config=config)
    async for event in response.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            await msg.stream_token(event.data.delta)

    msg.content = response.final_output
    await msg.update()

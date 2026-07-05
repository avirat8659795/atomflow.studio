import os
import re
import base64
import asyncio
import random
import httpx  # pip install httpx
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

app = FastAPI(
    title="ATOM-FLOW Engine",
    description="Context-Aware Multi-Modal Workspace with Live Slides Engine",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    ai_client = genai.Client()
except Exception as e:
    ai_client = None

class ChatRequest(BaseModel):
    message: str
    file_data: Optional[str] = None  
    file_mime: Optional[str] = None  

USER_SESSION_CONTEXT = []

# (HTML_UI and extract_presentation_template functions remain exactly the same as your code)
HTML_UI = """...""" 
def extract_presentation_template(raw_llm_markdown: str) -> Optional[str]:
    # ... (Your existing presentation parsing logic)
    return template

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTML_UI

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global USER_SESSION_CONTEXT
    user_prompt = request.message.strip()
    
    if not ai_client:
        return {"reply": "API Key configuration error: System tracking core initialized incorrectly."}

    content_parts = []
    
    if request.file_data and request.file_mime:
        try:
            raw_bytes = base64.b64decode(request.file_data)
            content_parts.append(
                types.Part.from_bytes(data=raw_bytes, mime_type=request.file_mime)
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Mime payload data processing error.")

    # ✅ FIXED: Using Asynchronous HTTP Client instead of blocking requests
    url_pattern = re.compile(r'https?://[^\s]+')
    found_urls = url_pattern.findall(user_prompt)
    if found_urls:
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(found_urls[0], headers=headers, timeout=10.0)
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup(["script", "style"]): 
                tag.decompose()
            scraped_text = " ".join(soup.get_text().split())[:3000]
            user_prompt = f"Scraped Context Data:\n\"\"\"\n{scraped_text}\n\"\"\"\n\nUser Message: {user_prompt}"
        except Exception:
            pass

    content_parts.append(types.Part.from_text(text=user_prompt))
    is_presentation_request = any(keyword in user_prompt.lower() for keyword in ["presentation", "slide deck", "create a presentation", "slides"])

    system_instruction = (
        "You are ATOM-FLOW, a context-aware multi-modal workspace assistant. "
        "Provide thorough, deep, and beautifully designed markdown responses.\n\n"
        "CRITICAL FOR PRESENTATIONS/SLIDES:\n"
        "If the user wants a slide deck or presentation, explain your design choices in standard markdown chat first. "
        "THEN, provide the presentation block wrapped EXACTLY in a ```slides custom block format. "
        "Use '---' on a brand new line to separate distinct slides."
    )

    temp_context = list(USER_SESSION_CONTEXT)
    temp_context.append(types.Content(role="user", parts=content_parts))

    max_retries = 3
    base_delay = 5.0  
    
    for attempt in range(max_retries + 1):
        try:
            # ✅ FIXED: Using the async Gemini client (.aio) to prevent blocking the event loop
            response = await ai_client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=temp_context,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )
            response_text = response.text

            USER_SESSION_CONTEXT.append(types.Content(role="user", parts=content_parts))
            USER_SESSION_CONTEXT.append(types.Content(role="model", parts=[types.Part.from_text(text=response_text)]))

            return_data = {"reply": response_text}

            if is_presentation_request:
                presentation_html = extract_presentation_template(response_text)
                if presentation_html:
                    return_data["presentation_html"] = presentation_html

            return return_data

        except Exception as e:
            error_msg = str(e)
            
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < max_retries:
                    wait_match = re.search(r"retry in ([\d\.]+)s", error_msg)
                    sleep_time = float(wait_match.group(1)) if wait_match else (base_delay * (2 ** attempt) + random.uniform(0, 1))
                    
                    sleep_time += 0.5 
                    print(f"[429 Quota Alert] Attempt {attempt + 1} exhausted. Backing off for {sleep_time:.2f}s...")
                    await asyncio.sleep(sleep_time)
                    continue
            
            return {"reply": f"Handshake Generation Exception Failure Channel: {error_msg}"}

@app.post("/clear")
async def clear_context():
    global USER_SESSION_CONTEXT
    USER_SESSION_CONTEXT.clear()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
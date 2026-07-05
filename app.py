import os
import re
import base64
import asyncio
import random
import httpx  
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

# --- FULL FIXED USER INTERFACE STRINGS ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATOM-FLOW AI Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        .theme-dark::-webkit-scrollbar-thumb { background: #1f293d; border-radius: 9999px; }
        .theme-light::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 9999px; }
        .prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        .prose th, .prose td { border: 1px solid #334155; padding: 0.5rem; text-align: left; }
        .prose th { background-color: #0f172a; }
    </style>
</head>
<body id="appBody" class="theme-dark bg-[#0b0f19] text-[#e2e8f0] font-sans antialiased h-screen flex overflow-hidden transition-colors duration-300">

    <aside id="sidebar" class="fixed inset-y-0 left-0 z-30 w-[260px] bg-[#070a10] border-r border-[#1e293b]/40 flex flex-col justify-between transition-transform duration-300 transform md:relative md:translate-x-0 -translate-x-full shrink-0">
        <div class="p-3.5 flex flex-col h-full overflow-y-auto">
            <button onclick="clearChatLog()" class="flex items-center justify-between w-full px-4 py-2.5 text-sm font-semibold rounded-xl bg-[#0f172a] border-2 border-[#10b981] text-white shadow-[0_0_15px_rgba(16,185,129,0.15)] mb-6 hover:bg-[#10b981]/10 transition-all">
                <div class="flex items-center gap-2.5"><span class="text-base text-[#10b981]">⚛️</span> New chat</div>
                <span class="text-xs text-[#64748b]">Reset</span>
            </button>
            <div class="space-y-1">
                <p class="px-3 text-xs font-bold text-[#475569] uppercase tracking-wider mb-2.5">Core Chat Logs</p>
                <div id="historyLogs" class="space-y-1"></div>
            </div>
        </div>
        <div class="p-4 border-t border-[#1e293b]/30 flex flex-col gap-3 bg-[#05070b]">
            <div>
                <span class="text-xs font-semibold text-[#475569] uppercase tracking-wider block mb-2 px-1">Console Settings</span>
                <button onclick="toggleThemeConfig()" class="w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg bg-[#0f172a] border border-[#1e293b]/50 text-slate-300 hover:text-white transition-all">
                    <span>Theme Mode</span>
                    <span id="themeBtnLabel" class="text-[#10b981] font-bold">🌙 Dark</span>
                </button>
            </div>
            <div class="flex items-center gap-3 p-2 rounded-xl bg-[#0f172a]/40 border border-[#1e293b]/20">
                <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center shadow-md shrink-0"><span class="text-xs">⚛️</span></div>
                <div class="flex flex-col truncate">
                    <span class="text-sm font-bold text-white tracking-wide">ATOM-FLOW</span>
                    <span class="text-[10px] text-[#10b981] font-mono tracking-widest uppercase">Multi-Modal Core</span>
                </div>
            </div>
        </div>
    </aside>

    <div id="sidebarOverlay" onclick="toggleMobileSidebar()" class="fixed inset-0 bg-black/50 z-20 hidden md:hidden"></div>

    <main class="flex-1 flex flex-col h-full relative overflow-hidden">
        <header id="mainHeader" class="h-14 flex items-center px-4 justify-between border-b border-[#1e293b]/30 z-10 bg-[#0b0f19]/80 backdrop-blur-md transition-colors">
            <button onclick="toggleMobileSidebar()" class="p-2 text-[#64748b] hover:text-white rounded-lg hover:bg-[#1e293b]/40 transition-colors focus:outline-none md:hidden">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
            </button>
            <div class="text-sm font-medium text-[#94a3b8]">Engine: <span id="modelLabel" class="text-white font-bold tracking-wide">ATOM-CORE (Multimodal)</span></div>
            <div class="w-9"></div>
        </header>

        <div id="chatFeed" class="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-3xl w-full mx-auto flex flex-col z-10">
            <div class="flex gap-4 items-start text-base">
                <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0 shadow-md">⚛️</div>
                <div class="space-y-1.5 flex-1 pt-0.5 leading-relaxed">
                    <p class="font-bold text-white text-sm tracking-wide">ATOM-FLOW Core</p>
                    <p class="text-[#cbd5e1] text-[15px]">Multi-modal engine online. Try saying **"Create a presentation on Cyber Security"** to unlock the interactive presentation panel.</p>
                </div>
            </div>
        </div>

        <footer class="p-4 bg-gradient-to-t from-[#0b0f19] via-[#0b0f19] to-transparent z-10" id="mainFooter">
            <div class="max-w-3xl w-full mx-auto relative flex flex-col items-center">
                <div class="flex flex-wrap gap-2 mb-3 justify-start w-full px-1">
                    <button onclick="applyQuickAction('Explain this concept simply with examples: ')" class="px-3 py-1.5 text-xs font-medium rounded-full bg-[#0f172a] border border-[#1e293b]/60 text-[#94a3b8] hover:text-white hover:border-[#10b981] transition-all">📝 Simplify Concept</button>
                    <button onclick="applyQuickAction('Give me a 3-question conceptual quiz on this topic: ')" class="px-3 py-1.5 text-xs font-medium rounded-full bg-[#0f172a] border border-[#1e293b]/60 text-[#94a3b8] hover:text-white hover:border-[#10b981] transition-all">🧪 Quiz Me</button>
                    <button onclick="applyQuickAction('Create a professional presentation on ')" class="px-3 py-1.5 text-xs font-medium rounded-full bg-[#0f172a] border border-[#10b981]/80 text-[#10b981] hover:bg-[#10b981]/10 transition-all">📊 Create Presentation</button>
                </div>

                <div id="filePreviewBar" class="hidden w-full bg-[#0f172a] border-x border-t border-[#1e293b]/60 px-4 py-2 rounded-t-2xl flex items-center justify-between text-xs text-slate-300">
                    <div class="flex items-center gap-2 truncate">
                        <span class="text-[#10b981]">📎</span>
                        <span id="fileNameDisplay" class="truncate font-mono">file.jpg</span>
                    </div>
                    <button onclick="removeAttachedFile()" class="text-rose-400 hover:text-rose-300 font-bold px-1">Remove</button>
                </div>

                <div id="inputContainer" class="w-full relative flex items-center bg-[#0f172a] rounded-2xl border border-[#1e293b]/60 group transition-all">
                    <input type="file" id="filePayloadInput" class="hidden" onchange="handleFilePayloadSelection(event)" accept="image/*,application/pdf">
                    <button onclick="document.getElementById('filePayloadInput').click()" class="absolute left-3 p-2 text-[#475569] hover:text-[#10b981] transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13" /></svg>
                    </button>
                    <textarea id="messageInput" rows="1" placeholder="Message Atom-Flow Matrix..." class="w-full bg-transparent text-white placeholder-[#475569] pl-12 pr-14 py-4 resize-none focus:outline-none text-[15px] max-h-40 overflow-y-auto" onkeydown="handleKeyDown(event)"></textarea>
                    <button onclick="commitMessageToSend()" class="absolute right-3.5 p-2 bg-[#070a10] border border-[#1e293b]/40 hover:bg-white text-white hover:text-black rounded-xl transition-all">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>
                    </button>
                </div>
            </div>
        </footer>
    </main>

    <div id="presentationModal" class="fixed inset-0 bg-black/80 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm">
        <div class="bg-[#0f172a] border border-[#1e293b] rounded-2xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            <div class="px-6 py-4 border-b border-[#1e293b] flex items-center justify-between bg-[#070a10]">
                <div class="flex items-center gap-2">
                    <span class="text-[#10b981] text-lg">📊</span>
                    <h3 class="font-bold text-white tracking-wide">ATOM-FLOW Interactive Presentation Engine</h3>
                </div>
                <div class="flex items-center gap-3">
                    <button onclick="downloadPresentationFile()" class="px-4 py-1.5 text-xs font-bold bg-[#10b981] text-black rounded-lg hover:bg-[#0d9668] transition-all">📥 Download Slide Deck</button>
                    <button onclick="closePresentationWorkspace()" class="text-slate-400 hover:text-white font-bold text-sm bg-slate-800/60 px-3 py-1.5 rounded-lg">Close</button>
                </div>
            </div>
            <div class="flex-1 bg-[#111111] relative">
                <iframe id="presentationFrame" class="w-full h-full border-none"></iframe>
            </div>
        </div>
    </div>

    <script>
        let isDarkMode = true;
        let attachedFileB64 = null;
        let attachedFileMime = null;
        let currentPresentationHtml = "";

        marked.setOptions({ gfm: true, breaks: true });

        function toggleMobileSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('-translate-x-full');
        }

        function toggleThemeConfig() {
            isDarkMode = !isDarkMode;
            const body = document.getElementById('appBody');
            const themeBtnLabel = document.getElementById('themeBtnLabel');
            if (!isDarkMode) {
                body.classList.replace('theme-dark', 'theme-light');
                body.classList.replace('bg-[#0b0f19]', 'bg-[#f8fafc]');
                body.classList.replace('text-[#e2e8f0]', 'text-[#334155]');
                themeBtnLabel.innerHTML = "☀️ Light";
            } else {
                body.classList.replace('theme-light', 'theme-dark');
                body.classList.replace('bg-[#f8fafc]', 'bg-[#0b0f19]');
                body.classList.replace('text-[#334155]', 'text-[#e2e8f0]');
                themeBtnLabel.innerHTML = "🌙 Dark";
            }
        }

        function handleFilePayloadSelection(event) {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                attachedFileB64 = e.target.result.split(',')[1];
                attachedFileMime = file.type;
                document.getElementById('fileNameDisplay').innerText = file.name;
                document.getElementById('filePreviewBar').classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }

        function removeAttachedFile() {
            attachedFileB64 = null; attachedFileMime = null;
            document.getElementById('filePreviewBar').classList.add('hidden');
        }

        function applyQuickAction(prefixText) {
            const input = document.getElementById('messageInput');
            input.value = prefixText;
            input.focus();
        }

        function clearChatLog() {
            fetch('/clear', { method: 'POST' }).then(() => {
                document.getElementById('chatFeed').innerHTML = '';
            });
        }
        
        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                commitMessageToSend();
            }
        }

        function appendMessageRow(text, isUser) {
            const feed = document.getElementById('chatFeed');
            let contentHtml = isUser ? text : marked.parse(text);
            let row = isUser ? 
                `<div class="flex gap-4 items-start text-base self-end justify-end w-full max-w-xl ml-auto"><div class="bg-slate-800 text-white rounded-2xl px-4 py-3 shadow-md">\${contentHtml}</div></div>` :
                `<div class="flex gap-4 items-start text-base"><div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0 shadow-md">⚛️</div><div class="space-y-1.5 flex-1 pt-0.5"><p class="font-bold text-white text-sm">ATOM-FLOW Core</p><div class="prose text-[#cbd5e1] text-[15px]">\${contentHtml}</div></div></div>`;
            feed.insertAdjacentHTML('beforeend', row);
            feed.scrollTop = feed.scrollHeight;
        }

        function openPresentationWorkspace(rawSlideCode) {
            if (!rawSlideCode) return;
            currentPresentationHtml = rawSlideCode;
            document.getElementById('presentationModal').classList.remove('hidden');
            document.getElementById('presentationFrame').srcdoc = rawSlideCode;
        }

        function closePresentationWorkspace() {
            document.getElementById('presentationModal').classList.add('hidden');
        }

        function downloadPresentationFile() {
            if (!currentPresentationHtml) return;
            const blob = new Blob([currentPresentationHtml], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'ATOM-FLOW-Presentation.html';
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
        }

        function commitMessageToSend() {
            const input = document.getElementById('messageInput');
            const messageText = input.value.trim();
            if (!messageText && !attachedFileB64) return;

            appendMessageRow(attachedFileB64 ? "📸 [Attached File] " + messageText : messageText, true);
            input.value = '';

            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText, file_data: attachedFileB64, file_mime: attachedFileMime })
            })
            .then(res => res.json())
            .then(data => {
                appendMessageRow(data.reply, false);
                if (data.presentation_html) openPresentationWorkspace(data.presentation_html);
            })
            .catch(() => appendMessageRow("System connection error.", false));
            removeAttachedFile();
        }
    </script>
</body>
</html>
"""

# --- FIXED: REVEAL.JS PRESENTATION ENGINE COMPILER ---
def extract_presentation_template(raw_llm_markdown: str) -> Optional[str]:
    match = re.search(r'```slides\s*(.*?)\n```', raw_llm_markdown, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
        
    slide_content_markdown = match.group(1)
    raw_slides = slide_content_markdown.split("---")
    slide_sections = ""
    
    for slide in raw_slides:
        if slide.strip():
            clean_slide = slide.strip()
            html_lines = []
            for line in clean_slide.split('\n'):
                line = line.strip()
                if not line: continue
                if line.startswith('### '): html_lines.append(f"<h3>{line[4:]}</h3>")
                elif line.startswith('## '): html_lines.append(f"<h2>{line[3:]}</h2>")
                elif line.startswith('# '): html_lines.append(f"<h1>{line[2:]}</h1>")
                elif line.startswith('* ') or line.startswith('- '): html_lines.append(f"<li>{line[2:]}</li>")
                else: html_lines.append(f"<p>{re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)}</p>")
            
            final_content = ""
            in_list = False
            for item in html_lines:
                if item.startswith('<li>'):
                    if not in_list: final_content += "<ul>"; in_list = True
                    final_content += item
                else:
                    if in_list: final_content += "</ul>"; in_list = False
                    final_content += item
            if in_list: final_content += "</ul>"
            slide_sections += f"<section data-background-color='#0f172a'>\\n{final_content}\\n</section>\\n"

    if not slide_sections:
        return None

    # Embedded completely with robust content delivery network styles for RevealJS
    return f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/theme/black.min.css">
        <style>
            .reveal h1, .reveal h2, .reveal h3 {{ color: #10b981 !important; font-weight: bold; text-transform: none; }}
            .reveal li, .reveal p {{ color: #e2e8f0 !important; font-size: 24px; line-height: 1.5; }}
            .reveal ul {{ display: inline-block; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                {slide_sections}
            </div>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.js"></script>
        <script>
            setTimeout(() => {{
                Reveal.initialize({{ controls: true, progress: true, center: true, embedded: true }});
            }}, 200);
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTML_UI

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global USER_SESSION_CONTEXT
    user_prompt = request.message.strip()
    
    if not ai_client:
        return {"reply": "API Key configuration error."}

    content_parts = []
    if request.file_data and request.file_mime:
        try:
            content_parts.append(types.Part.from_bytes(data=base64.b64decode(request.file_data), mime_type=request.file_mime))
        except Exception:
            raise HTTPException(status_code=400, detail="Mime payload processing error.")

    url_pattern = re.compile(r'https?://[^\s]+')
    found_urls = url_pattern.findall(user_prompt)
    if found_urls:
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(found_urls[0], headers=headers, timeout=10.0)
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup(["script", "style"]): tag.decompose()
            user_prompt = f"Scraped Context:\\n\"\"\"\\n{(' '.join(soup.get_text().split()))[:3000]}\\n\"\"\"\\n\\nUser Message: {user_prompt}"
        except Exception: pass

    content_parts.append(types.Part.from_text(text=user_prompt))
    is_presentation_request = any(k in user_prompt.lower() for k in ["presentation", "slide deck", "slides"])

    system_instruction = (
        "You are ATOM-FLOW, a context-aware multi-modal workspace assistant. Provide beautiful markdown responses.\\n\\n"
        "CRITICAL FOR PRESENTATIONS/SLIDES:\\n"
        "If requested, provide the presentation block wrapped EXACTLY inside a ```slides custom block format. Use '---' to separate slides.\\n"
        "Example:\\n```slides\\n# Slide One\\n## Subtitle\\n* Bullet point\\n---\\n# Slide Two\\n```"
    )

    temp_context = list(USER_SESSION_CONTEXT)
    temp_context.append(types.Content(role="user", parts=content_parts))

    max_retries = 3
    base_delay = 5.0  
    
    for attempt in range(max_retries + 1):
        try:
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
                if presentation_html: return_data["presentation_html"] = presentation_html

            return return_data

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < max_retries:
                    wait_match = re.search(r"retry in ([\d\.]+)s", error_msg)
                    sleep_time = float(wait_match.group(1)) if wait_match else (base_delay * (2 ** attempt) + random.uniform(0, 1))
                    await asyncio.sleep(sleep_time + 0.5)
                    continue
            return {"reply": f"Handshake Generation Exception Failure Channel: {error_msg}"}

@app.post("/clear")
async def clear_context():
    global USER_SESSION_CONTEXT
    USER_SESSION_CONTEXT.clear()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
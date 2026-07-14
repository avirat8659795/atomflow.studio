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
    title="ChatFusion Engine",
    description="Context-Aware Multi-Modal Workspace",
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

# --- FULL EXCLUSIVE CHATFUSION MONOCHROME UI PLATFORM ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatFusion Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        
        /* Premium Dark Theme Scrollbars matching image template */
        .theme-dark ::-webkit-scrollbar-thumb { background: #2A2A32; border-radius: 9999px; }
        .theme-dark ::-webkit-scrollbar-thumb:hover { background: #3F3F4E; }
        
        /* Light Theme Scrollbars */
        .theme-light ::-webkit-scrollbar-thumb { background: #d4d4d4; border-radius: 9999px; }
        .theme-light ::-webkit-scrollbar-thumb:hover { background: #a3a3a3; }

        .prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        .prose th, .prose td { border: 1px solid #2A2A32; padding: 0.6rem; text-align: left; }
        .theme-light .prose th, .theme-light .prose td { border: 1px solid #e5e5e5; }
        .prose th { background-color: #18181C; color: #ffffff; }
        .theme-light .prose th { background-color: #f5f5f5; color: #171717; }
        .prose ul { list-style-type: disc; padding-left: 1.5rem; margin: 0.5rem 0; }
        .prose ol { list-style-type: decimal; padding-left: 1.5rem; margin: 0.5rem 0; }
        
        .theme-transition { transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease; }
    </style>
</head>
<body id="appBody" class="theme-dark bg-[#0E0E11] text-[#E3E3E6] font-sans antialiased h-screen flex overflow-hidden theme-transition">

    <!-- Sidebar Layout Frame -->
    <aside id="sidebar" class="fixed inset-y-0 left-0 z-30 w-[260px] bg-[#18181C] border-r border-[#232329] flex flex-col justify-between transition-transform duration-300 ease-in-out transform md:relative md:translate-x-0 -translate-x-full shrink-0 theme-transition">
        <div class="p-3.5 flex flex-col h-full overflow-y-auto">
            <!-- Header Identity block matching the reference screenshot design layout -->
            <div class="flex items-center justify-between w-full mb-4 px-1.5">
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded-full bg-neutral-400"></div>
                    <span class="text-xs font-semibold tracking-wider text-neutral-400 uppercase select-none">ChatFusion</span>
                </div>
                <button onclick="toggleMobileSidebar()" class="md:hidden p-1 rounded text-neutral-400 hover:text-white transition-all">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                </button>
            </div>

            <!-- Action Block Container -->
            <div class="flex items-center gap-2 w-full">
                <button onclick="clearChatLog()" class="flex items-center justify-between flex-1 px-3 py-2 text-xs font-medium rounded-lg text-neutral-200 dark:text-neutral-800 hover:bg-[#232329] dark:hover:bg-neutral-200 border border-[#2A2A32] dark:border-neutral-300 transition-all group bg-transparent">
                    <div class="flex items-center gap-2">
                        <span>+ New chat</span>
                    </div>
                    <span class="text-[10px] text-neutral-500 opacity-0 group-hover:opacity-100 transition-opacity">Reset</span>
                </button>
            </div>

            <!-- Dynamic Chat History Logs Frame Feed Section -->
            <div class="mt-6 space-y-1">
                <p class="px-1.5 text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">Recent</p>
                <div id="historyLogs" class="space-y-0.5 max-h-[50vh] overflow-y-auto">
                    <!-- Automatically filled dynamically by user text metrics -->
                </div>
            </div>
        </div>
        
        <!-- Bottom Controls / Options Configuration Panel -->
        <div class="p-3 border-t border-[#232329] dark:border-neutral-200 flex flex-col gap-2 bg-[#18181C] dark:bg-[#F9F9F9] theme-transition">
            <button onclick="toggleThemeConfig()" class="w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black hover:bg-[#232329] dark:hover:bg-neutral-200 border border-[#2A2A32] dark:border-neutral-300 transition-all bg-transparent">
                <span>Theme Mode</span>
                <span id="themeBtnLabel" class="px-2 py-0.5 rounded text-[10px] bg-[#2A2A32] dark:bg-neutral-200 text-white dark:text-neutral-900 font-mono font-bold uppercase tracking-wider transition-colors">Dark</span>
            </button>
        </div>
    </aside>

    <!-- Sidebar overlay shadow layer -->
    <div id="sidebarOverlay" onclick="toggleMobileSidebar()" class="fixed inset-0 bg-black/60 z-20 hidden backdrop-blur-xs transition-opacity duration-300"></div>

    <!-- Main Workspace Frame -->
    <main class="flex-1 flex flex-col h-full relative overflow-hidden bg-[#0E0E11] dark:bg-[#F5F5F7] theme-transition">
        
        <!-- Dynamic Header Layer -->
        <header id="mainHeader" class="h-14 flex items-center px-4 justify-between border-b border-[#232329] dark:border-neutral-200 z-10 bg-[#0E0E11]/90 dark:bg-white/90 backdrop-blur-md theme-transition">
            <button onclick="toggleMobileSidebar()" class="p-2 text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black rounded-lg hover:bg-[#232329] dark:hover:bg-neutral-200 transition-colors focus:outline-none md:hidden">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
            </button>
            <div id="hubIndicator" class="text-xs font-semibold tracking-wider text-neutral-500 dark:text-neutral-400 uppercase">Workspace Hub</div>
            <div class="w-9"></div>
        </header>

        <!-- Main Conversational Flow Stream Container -->
        <div id="chatFeed" class="flex-1 overflow-y-auto px-4 py-8 space-y-8 max-w-2xl w-full mx-auto flex flex-col z-10 scroll-smooth">
            <!-- Core Greeting Screen Layout Component matching image reference structure -->
            <div id="defaultWelcomePane" class="my-auto flex flex-col items-center text-center space-y-4">
                <h2 class="text-2xl font-medium tracking-tight text-white dark:text-neutral-900">Good Day Workspace</h2>
                <p class="text-sm text-neutral-500 max-w-sm">How can ChatFusion assist you today? Initialize a concept synthesis or slide generation session down below.</p>
            </div>
        </div>

        <!-- Input Box Execution Footer Grid -->
        <footer class="p-4 bg-gradient-to-t from-[#0E0E11] via-[#0E0E11] to-transparent dark:from-[#FFFFFF] dark:via-[#FFFFFF] z-10 theme-transition" id="mainFooter">
            <div class="max-w-2xl w-full mx-auto relative flex flex-col items-center">
                
                <!-- Prompt Snippet Shortcuts -->
                <div class="flex flex-wrap gap-1.5 mb-3 justify-start w-full px-1">
                    <button onclick="applyQuickAction('Explain this concept simply with examples: ')" class="px-2.5 py-1 text-[11px] font-medium rounded-md bg-[#18181C] dark:bg-white border border-[#232329] dark:border-neutral-300 text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-all">Simplify Concept</button>
                    <button onclick="applyQuickAction('Create a professional presentation on ')" class="px-2.5 py-1 text-[11px] font-medium rounded-md bg-white dark:bg-neutral-900 border border-white dark:border-neutral-900 text-black dark:text-white hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-all shadow-sm">Create Slides</button>
                </div>

                <!-- File Attachment View Ribbon -->
                <div id="filePreviewBar" class="hidden w-full bg-[#18181C] dark:bg-neutral-100 border-x border-t border-[#232329] dark:border-neutral-300 px-4 py-2 rounded-t-xl flex items-center justify-between text-xs text-neutral-300 dark:text-neutral-700">
                    <div class="flex items-center gap-2 truncate">
                        <span class="text-neutral-400 dark:text-neutral-500">📎</span>
                        <span id="fileNameDisplay" class="truncate font-mono">source.data</span>
                    </div>
                    <button onclick="removeAttachedFile()" class="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black underline font-semibold px-1">Discard</button>
                </div>

                <!-- Entry Input Console Structure -->
                <div id="inputContainer" class="w-full relative flex items-center bg-[#18181C] dark:bg-white rounded-xl border border-[#232329] dark:border-neutral-300 group transition-all shadow-xs focus-within:border-neutral-500 dark:focus-within:border-neutral-400">
                    <input type="file" id="filePayloadInput" class="hidden" onchange="handleFilePayloadSelection(event)" accept="image/*,application/pdf">
                    <button onclick="document.getElementById('filePayloadInput').click()" class="absolute left-3.5 p-1.5 text-neutral-500 dark:text-neutral-400 hover:text-white dark:hover:text-black transition-colors" aria-label="Attach File">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13" /></svg>
                    </button>
                    <textarea id="messageInput" rows="1" placeholder="Type a message or paste a link..." class="w-full bg-transparent text-white dark:text-black placeholder-neutral-600 dark:placeholder-neutral-400 pl-12 pr-14 py-3.5 resize-none focus:outline-none text-[14px] max-h-40 overflow-y-auto" onkeydown="handleKeyDown(event)"></textarea>
                    <button onclick="commitMessageToSend()" class="absolute right-3 p-1.5 bg-white dark:bg-neutral-900 text-black dark:text-white border border-transparent dark:border-neutral-700 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-all shadow-xs" aria-label="Send message">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>
                    </button>
                </div>
            </div>
        </footer>
    </main>

    <!-- Presentation View Mode Overlay Modal -->
    <div id="presentationModal" class="fixed inset-0 bg-black/95 z-50 hidden flex items-center justify-center p-4 backdrop-blur-md transition-opacity duration-300">
        <div class="bg-[#18181C] dark:bg-white border border-[#232329] dark:border-neutral-200 rounded-xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden shadow-2xl relative">
            <div class="px-5 py-3 border-b border-[#232329] dark:border-neutral-200 flex items-center justify-between bg-[#0E0E11] dark:bg-neutral-50">
                <h3 class="font-bold text-white dark:text-neutral-800 text-xs tracking-widest uppercase">Presentation Core Preview</h3>
                <div class="flex items-center gap-2">
                    <button onclick="downloadPresentationFile()" class="px-3 py-1 text-xs font-semibold bg-white dark:bg-neutral-900 text-black dark:text-white border dark:border-neutral-700 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-all shadow-sm">Download Deck</button>
                    <button onclick="closePresentationWorkspace()" class="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black text-xs bg-[#2A2A32] dark:bg-neutral-200 px-3 py-1 rounded-md transition-all font-medium">Close Deck</button>
                </div>
            </div>
            <div class="flex-1 bg-black relative">
                <iframe id="presentationFrame" class="w-full h-full border-none"></iframe>
            </div>
        </div>
    </div>

    <script>
        let isDarkMode = true;
        let attachedFileB64 = null;
        let attachedFileMime = null;
        let currentPresentationHtml = "";
        let chatHistoryList = [];

        marked.setOptions({ gfm: true, breaks: true });

        function toggleMobileSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            if (sidebar.classList.contains('-translate-x-full')) {
                sidebar.classList.remove('-translate-x-full');
                overlay.classList.remove('hidden');
            } else {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            }
        }

        // --- THEME SWITCH MATRIX FIX ---
        function toggleThemeConfig() {
            isDarkMode = !isDarkMode;
            const body = document.getElementById('appBody');
            const themeBtnLabel = document.getElementById('themeBtnLabel');
            const mainHeader = document.getElementById('mainHeader');
            
            if (!isDarkMode) {
                body.classList.replace('theme-dark', 'theme-light');
                body.classList.replace('bg-[#0E0E11]', 'bg-[#FFFFFF]');
                body.classList.replace('text-[#E3E3E6]', 'text-[#171717]');
                mainHeader.classList.replace('bg-[#0E0E11]/90', 'bg-white/90');
                mainHeader.classList.replace('border-[#232329]', 'border-neutral-200');
                themeBtnLabel.innerHTML = "Light";
                themeBtnLabel.classList.replace('bg-[#2A2A32]', 'bg-neutral-200');
                themeBtnLabel.classList.replace('text-white', 'text-neutral-900');
                
                document.querySelectorAll('.user-bubble').forEach(el => {
                    if (el) {
                        el.classList.remove('bg-[#18181C]', 'text-neutral-100', 'border-[#2A2A32]');
                        el.classList.add('bg-neutral-100', 'text-neutral-900', 'border-neutral-200');
                    }
                });
                document.querySelectorAll('.model-text-container').forEach(el => {
                    if (el) {
                        el.classList.remove('text-neutral-400');
                        el.classList.add('text-neutral-800');
                    }
                });
            } else {
                body.classList.replace('theme-light', 'theme-dark');
                body.classList.replace('bg-[#FFFFFF]', 'bg-[#0E0E11]');
                body.classList.replace('text-[#171717]', 'text-[#E3E3E6]');
                mainHeader.classList.replace('bg-white/90', 'bg-[#0E0E11]/90');
                mainHeader.classList.replace('border-neutral-200', 'border-[#232329]');
                themeBtnLabel.innerHTML = "Dark";
                themeBtnLabel.classList.replace('bg-neutral-200', 'bg-[#2A2A32]');
                themeBtnLabel.classList.replace('text-neutral-900', 'text-white');
                
                document.querySelectorAll('.user-bubble').forEach(el => {
                    if (el) {
                        el.classList.remove('bg-neutral-100', 'text-neutral-900', 'border-neutral-200');
                        el.classList.add('bg-[#18181C]', 'text-neutral-100', 'border-[#2A2A32]');
                    }
                });
                document.querySelectorAll('.model-text-container').forEach(el => {
                    if (el) {
                        el.classList.remove('text-neutral-800');
                        el.classList.add('text-neutral-400');
                    }
                });
            }
        }

        // --- WORKING CHAT HISTORY CONTROLLER MANAGEMENT LAYER ---
        function addHistoryItem(messageText) {
            const historyLogs = document.getElementById('historyLogs');
            const truncatedText = messageText.length > 28 ? messageText.substring(0, 25) + "..." : messageText;
            const elementId = "hist-" + Date.now();
            
            chatHistoryList.push({ id: elementId, text: messageText });
            
            const itemHtml = `
                <button onclick="jumpToHistoryAnchor('${elementId}')" class="w-full text-left px-2 py-1.5 text-xs rounded text-neutral-400 hover:text-white hover:bg-[#232329] transition-all truncate block font-sans">
                    🗪 ${truncatedText}
                </button>
            `;
            historyLogs.insertAdjacentHTML('afterbegin', itemHtml);
        }

        function jumpToHistoryAnchor(id) {
            const targetElement = document.getElementById(id);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                targetElement.classList.add('ring-1', 'ring-neutral-500');
                setTimeout(() => targetElement.classList.remove('ring-1', 'ring-neutral-500'), 2000);
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
            document.getElementById('filePayloadInput').value = "";
            document.getElementById('filePreviewBar').classList.add('hidden');
        }

        function applyQuickAction(prefixText) {
            const input = document.getElementById('messageInput');
            input.value = prefixText;
            input.focus();
        }

        function clearChatLog() {
            fetch('/clear', { method: 'POST' }).then(() => {
                document.getElementById('chatFeed').innerHTML = `
                    <div id="defaultWelcomePane" class="my-auto flex flex-col items-center text-center space-y-4">
                        <h2 class="text-2xl font-medium tracking-tight text-white dark:text-neutral-900">Good Day Workspace</h2>
                        <p class="text-sm text-neutral-500 max-w-sm">How can ChatFusion assist you today? Initialize a concept synthesis or slide generation session down below.</p>
                    </div>
                `;
                document.getElementById('historyLogs').innerHTML = '';
                chatHistoryList = [];
            });
        }
        
        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                commitMessageToSend();
            }
        }

        function appendMessageRow(text, isUser, anchorId = null) {
            const feed = document.getElementById('chatFeed');
            const welcomePane = document.getElementById('defaultWelcomePane');
            if (welcomePane) welcomePane.remove();

            let contentHtml = isUser ? text : marked.parse(text);
            let userBg = isDarkMode ? "bg-[#18181C] text-neutral-100 border-[#2A2A32]" : "bg-neutral-100 text-neutral-900 border-neutral-200";
            let modelColor = isDarkMode ? "text-neutral-400" : "text-neutral-800";
            
            let rowIdAttr = anchorId ? `id="${anchorId}"` : '';
            
            let row = isUser ? 
                `<div ${rowIdAttr} class="flex gap-4 items-start text-base self-end justify-end w-full max-w-xl ml-auto transition-all duration-300 rounded-lg"><div class="user-bubble border rounded-xl px-4 py-2.5 text-[14px] shadow-xs theme-transition ${userBg}">${contentHtml}</div></div>` :
                `<div class="flex gap-4 items-start text-base border-t border-neutral-800/10 dark:border-neutral-200/40 pt-6"><div class="w-7 h-7 rounded-md bg-white dark:bg-neutral-950 flex items-center justify-center shrink-0 border border-neutral-800"><span class="text-[10px] text-black dark:text-white font-bold">CF</span></div><div class="space-y-1 flex-1 pt-0.5"><p class="font-bold text-[10px] tracking-widest uppercase text-neutral-500">ChatFusion</p><div class="model-text-container prose text-[14px] leading-relaxed theme-transition ${modelColor}">${contentHtml}</div></div></div>`;
            
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
            document.getElementById('presentationFrame').srcdoc = "";
        }

        function downloadPresentationFile() {
            if (!currentPresentationHtml) return;
            const blob = new Blob([currentPresentationHtml], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'ChatFusion-Presentation.html';
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
        }

        function commitMessageToSend() {
            const input = document.getElementById('messageInput');
            const messageText = input.value.trim();
            if (!messageText && !attachedFileB64) return;

            const trackingId = "hist-" + Date.now();
            appendMessageRow(attachedFileB64 ? "📸 [Attached File] " + messageText : messageText, true, trackingId);
            addHistoryItem(messageText || "[Attached Media]");
            
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
            .catch(() => appendMessageRow("System connection execution variant error.", false));
            removeAttachedFile();
        }
    </script>
</body>
</html>
"""

# --- REVEAL.JS PRESENTATION COMPILER LAYER ---
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
                else:
                    processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
                    html_lines.append("<p>" + processed_line + "</p>")
            
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
            slide_sections += f"<section data-background-color='#0E0E11'>\n{final_content}\n</section>\n"

    if not slide_sections:
        return None

    presentation_base = """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/theme/black.min.css">
        <style>
            .reveal h1, .reveal h2, .reveal h3 { color: #FFFFFF !important; font-weight: bold; text-transform: none; }
            .reveal li, .reveal p { color: #A3A3A3 !important; font-size: 24px; line-height: 1.5; }
            .reveal ul { display: inline-block; text-align: left; }
        </style>
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                __SLIDE_PLACEHOLDER__
            </div>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.js"></script>
        <script>
            setTimeout(() => {
                Reveal.initialize({ controls: true, progress: true, center: true, embedded: true });
            }, 200);
        </script>
    </body>
    </html>
    """
    return presentation_base.replace("__SLIDE_PLACEHOLDER__", slide_sections)

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
            user_prompt = f"Scraped Context:\n\"\"\"\n{(' '.join(soup.get_text().split()))[:3000]}\n\"\"\"\n\nUser Message: {user_prompt}"
        except Exception: pass

    content_parts.append(types.Part.from_text(text=user_prompt))
    is_presentation_request = any(k in user_prompt.lower() for k in ["presentation", "slide deck", "slides"])

    system_instruction = (
        "You are ChatFusion, a context-aware workspace assistant. Provide beautiful clear markdown responses.\n\n"
        "CRITICAL FOR PRESENTATIONS/SLIDES:\n"
        "If requested, provide the presentation block wrapped EXACTLY inside a ```slides custom block format. Use '---' to separate slides.\n"
        "Example:\n```slides\n# Slide One\n## Subtitle\n* Bullet point\n---\n# Slide Two\n```"
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
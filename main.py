import os
import time
import datetime
import re
import threading
import asyncio
import edge_tts
import json
import uuid
import queue
import chromadb
import subprocess
import atexit
import requests
from textblob import TextBlob
from groq import Groq
from flask import Flask, request, Response

# --- CONFIGURATION ---
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"  # <-- Paste your Groq key here
NEWS_API_KEY = "YOUR_NEWSAPI_KEY_HERE"  # <-- Paste your NewsAPI key here
LOOPHOLE_HOSTNAME = "YOUR_LOOPHOLE_HOSTNAME_HERE"  # <-- If using Loophole, put your hostname here (e.g. "myapp.loophole.site")


SARA_BIRTH = datetime.datetime(2008, 4, 21)
DB_PATH = "./sara_group_vault"


AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

for f in os.listdir(AUDIO_DIR):
    if f.endswith(".mp3"): os.remove(os.path.join(AUDIO_DIR, f))

app = Flask(__name__, static_folder="static")

sse_clients = []

def broadcast_to_clients(data_dict):
    msg_str = json.dumps(data_dict)
    for q in sse_clients.copy():
        try:
            q.put_nowait(msg_str)
        except queue.Full:
            sse_clients.remove(q)

# ==========================================
# 1. HTML / JS FRONTEND 
# ==========================================
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Sara - Group Study Hub</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    
    <script type="importmap">
    {
        "imports": {
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/",
            "@pixiv/three-vrm": "https://cdn.jsdelivr.net/npm/@pixiv/three-vrm@2.1.0/lib/three-vrm.module.min.js"
        }
    }
    </script>
    <style>
        :root {
            --info: #0dcaf0; --danger: #dc3545; --success: #198754; --warning: #ffc107;
            --dark: #212529; --secondary: #6c757d; --light: #f8f9fa;
        }
        * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
        
        html, body { 
            width: 100vw; 
            height: 100vh; 
            margin: 0; 
            padding: 0;
            background-color: #05050a; 
            background-image: radial-gradient(circle at 50% 40%, #1a1a2e 0%, #05050a 80%); 
            overflow: hidden; 
            touch-action: pan-y; 
            color: var(--light); 
        }
        
        .text-light { color: var(--light) !important; }
        .text-info { color: var(--info) !important; }
        .text-danger { color: var(--danger) !important; }
        .text-success { color: var(--success) !important; }
        .text-warning { color: var(--warning) !important; }
        
        .bg-dark { background-color: var(--dark) !important; }
        .bg-opacity-75 { background-color: rgba(33, 37, 41, 0.75) !important; }
        .bg-info-subtle { background-color: rgba(13, 202, 240, 0.1) !important; }
        
        .d-flex { display: flex !important; }
        .flex-column { flex-direction: column !important; }
        .justify-content-center { justify-content: center !important; }
        .align-items-center { align-items: center !important; }
        .flex-grow-1 { flex-grow: 1 !important; }
        .gap-3 { gap: 1rem !important; }
        
        .top-0 { top: 0 !important; } .start-0 { left: 0 !important; }
        .w-100 { width: 100% !important; } .h-100 { height: 100% !important; }
        .w-75 { width: 75% !important; }
        
        .p-2 { padding: 0.5rem !important; } .p-3 { padding: 1rem !important; } 
        .p-4 { padding: 1.5rem !important; } .p-5 { padding: 3rem !important; }
        .px-4 { padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .px-5 { padding-left: 3rem !important; padding-right: 3rem !important; }
        .mt-3 { margin-top: 1rem !important; } .mb-1 { margin-bottom: 0.25rem !important; } .mb-4 { margin-bottom: 1.5rem !important; }
        
        .text-center { text-align: center !important; }
        .text-break { word-wrap: break-word !important; word-break: break-word !important; }
        
        .fw-bold { font-weight: 700 !important; }
        .display-5 { font-size: 3rem !important; font-weight: 300 !important; line-height: 1.2 !important; }
        .lead { font-size: 1.25rem !important; font-weight: 300 !important; }
        .fs-3 { font-size: 1.75rem !important; } .fs-4 { font-size: 1.5rem !important; } .fs-6 { font-size: 1rem !important; }
        .small { font-size: 0.875em !important; }
        
        .border { border: 1px solid #495057 !important; }
        .border-info { border: 1px solid var(--info) !important; }
        .border-secondary { border: 1px solid var(--secondary) !important; }
        .border-bottom { border-bottom: 1px solid var(--secondary) !important; }
        
        .rounded-3 { border-radius: 0.3rem !important; } .rounded-4 { border-radius: 0.5rem !important; } .rounded-pill { border-radius: 50rem !important; }
        
        .shadow-sm { box-shadow: 0 .125rem .25rem rgba(0,0,0,.075) !important; }
        .shadow { box-shadow: 0 .5rem 1rem rgba(0,0,0,.15) !important; }
        .shadow-lg { box-shadow: 0 1rem 3rem rgba(0,0,0,.175) !important; }
        
        .card { display: flex; flex-direction: column; word-wrap: break-word; background-clip: border-box; }
        .badge { display: inline-block; padding: .35em .65em; font-size: .75em; font-weight: 700; line-height: 1; text-align: center; white-space: nowrap; vertical-align: baseline; border-radius: .25rem; }
        
        .form-control { display: block; width: 100%; padding: .375rem .75rem; font-size: 1rem; font-weight: 400; line-height: 1.5; color: var(--light); background-color: transparent; border: 1px solid #ced4da; transition: border-color .15s ease-in-out,box-shadow .15s ease-in-out; }
        .form-control-lg { min-height: calc(1.5em + 1rem + 2px); padding: .5rem 1rem; font-size: 1.25rem; }
        
        .btn { display: inline-block; font-weight: 400; line-height: 1.5; text-align: center; text-decoration: none; vertical-align: middle; cursor: pointer; user-select: none; border: 1px solid transparent; padding: .375rem .75rem; font-size: 1rem; transition: all .15s ease-in-out; }
        .btn-lg { padding: .5rem 1rem; font-size: 1.25rem; }
        .btn-outline-info { color: var(--info); border-color: var(--info); background: transparent; }
        .btn-outline-info:hover { color: #000; background-color: var(--info); box-shadow: 0 0 15px var(--info); }

        .glass-panel {
            background: rgba(15, 15, 25, 0.7) !important;
            backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        canvas { position: fixed; top: 0; left: 0; z-index: 0; }
        
        #welcome-screen { position: fixed; z-index: 1000; transition: opacity 0.5s ease; }
        #status-bar { position: fixed; top: 20px; right: 20px; z-index: 200; pointer-events: none; }
        
        #chat-log-container { 
            position: fixed; top: 20px; left: 20px; bottom: 100px; 
            width: 380px; z-index: 150; pointer-events: auto; 
        }

        #chat-messages { 
            flex: 1 1 auto; 
            overflow-y: auto !important; 
            min-height: 0; 
            pointer-events: auto;
        }
        
        #speech-wrapper { 
            position: fixed; bottom: 120px; left: 0; width: 100%;
            z-index: 100; pointer-events: none; display: none; justify-content: center;
        }
        #speech-bubble { pointer-events: auto; }
        
        #ui-container { 
            position: fixed; bottom: 30px; left: 0; width: 100%;
            z-index: 200; pointer-events: none; display: flex; justify-content: center; 
        }
        #chat-input { pointer-events: auto; }
        
        .cursor::after { content: '|'; animation: blink 1s step-end infinite; color: var(--info); }
        @keyframes blink { 50% { opacity: 0; } }
        
        .msg-user { border-left: 4px solid var(--info); background: rgba(13, 202, 240, 0.1); }
        .msg-sara { border-left: 4px solid #d63384; background: rgba(214, 51, 132, 0.1); }
        
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #495057; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #6c757d; }

        #chat-input:focus, #welcome-username:focus {
            background-color: rgba(5, 5, 15, 0.9) !important; 
            color: #ffffff !important; 
            border-color: var(--info) !important; 
            outline: none !important; 
            box-shadow: 0 0 20px rgba(0, 239, 255, 0.6), inset 0 0 10px rgba(0, 239, 255, 0.2) !important; 
            caret-color: var(--info) !important; 
        }

        @media (max-width: 768px) {
            #chat-log-container { width: 90%; left: 5%; top: 60px; height: 35vh; bottom: auto; background: rgba(5, 5, 15, 0.3); }
            #speech-wrapper { bottom: 90px; }
            #speech-bubble { width: 90% !important; }
            #ui-container { bottom: 20px; }
            #chat-input { width: 90% !important; }
        }
    </style>
</head>
<body class="text-light">

    <div id="welcome-screen" class="top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center glass-panel">
        <div class="card bg-dark bg-opacity-75 border-info shadow-lg p-5 text-center" style="max-width: 600px;">
            <h1 class="text-info display-5 fw-bold mb-4">SARA'S HUB</h1>
            <p class="lead fs-6 text-light mb-4">
                Welcome to the live group study session.<br><br>
                <strong>About Sara:</strong> She is a highly advanced, slightly tsundere AI mentor specializing in Physics and Mathematics. Currently a <b class="text-info">[[SARA_STAGE]]</b> ([[SARA_AGE]] years old), she won't hesitate to call out your mistakes, but she genuinely wants you to succeed.
            </p>
            <div class="d-flex flex-column align-items-center gap-3">
                <input type="text" id="welcome-username" class="form-control form-control-lg bg-dark text-info border-info text-center w-75 rounded-pill" placeholder="Enter your display name..." autocomplete="off">
                <button class="btn btn-outline-info btn-lg rounded-pill px-5 fw-bold" onclick="enterHub()">JOIN SESSION</button>
            </div>
        </div>
    </div>

    <div id="status-bar" class="badge border border-info glass-panel p-2 fs-6">
        NETWORK: <span id="conn-status" class="text-danger fw-bold">WAITING...</span>
    </div>
    
    <div id="chat-log-container" class="glass-panel rounded-4 shadow d-flex flex-column">
        <div class="bg-info-subtle text-info fw-bold text-center p-3 border-bottom border-secondary" style="letter-spacing: 1px;">
            GROUP STUDY CHAT
        </div>
        <div id="chat-messages" class="p-3 d-flex flex-column gap-3"></div>
    </div>

    <div id="speech-wrapper">
        <div id="speech-bubble" class="glass-panel rounded-4 p-4 text-center shadow-lg border-info" style="width: 75%;">
            <div id="text" class="fs-4 cursor"></div>
            <div id="latex" class="text-info mt-3 fs-3"></div>
        </div>
    </div>
    
    <div id="ui-container">
        <input type="text" id="chat-input" class="form-control form-control-lg glass-panel text-white border-secondary rounded-pill px-4 shadow-lg" style="width: 75%;" placeholder="Ask Sara a question..." autocomplete="off" disabled>
    </div>

    <audio id="sara-audio"></audio>

    <script type="module">
        import * as THREE from 'three';
        import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
        import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

        let globalUsername = "";
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 800;
        
        const eyeDartMultiplier = isMobile ? 0.2 : 1.5;
        const eyeVerticalRange = isMobile ? 0.2 : 0.8;
        const eyeDartDelayMin = isMobile ? 2.5 : 0.5;
        const eyeDartDelayMax = isMobile ? 4.0 : 2.5;
        const fingerSpeed = isMobile ? 0.5 : 2.0; 
        const fingerAmplitude = isMobile ? 0.005 : 0.03; 

        document.addEventListener('click', (e) => {
            const welcomeScreen = document.getElementById('welcome-screen');
            const chatInput = document.getElementById('chat-input');
            if (welcomeScreen.style.display === 'none') {
                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
                    if (window.getSelection().toString() === "") {
                        chatInput.focus();
                    }
                }
            }
        });

        window.enterHub = function() {
            const nameInput = document.getElementById('welcome-username').value.trim();
            if(nameInput === "") { alert("Please enter a name to join the session."); return; }
            globalUsername = nameInput;
            
            const welcomeScreen = document.getElementById('welcome-screen');
            welcomeScreen.style.opacity = '0';
            setTimeout(() => {
                welcomeScreen.style.display = 'none';
                const chatInput = document.getElementById('chat-input');
                chatInput.disabled = false;
                chatInput.focus();
                initNetwork();
            }, 500);
        };

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(30, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 1.4, 2.6);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        
        // --- UPGRADED MOBILE GRAPHICS (Pixel Ratio Fix) ---
        // Prevents ultra-high density displays from rendering too many pixels, 
        // keeping the framerate buttery smooth while maintaining sharpness.
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        document.body.appendChild(renderer.domElement);

        // --- UPGRADED CINEMATIC LIGHTING ---
        // 1. Key Light (Main bright light from top-right)
        const light = new THREE.DirectionalLight(0xffffff, 1.2); 
        light.position.set(1, 2, 1).normalize();
        scene.add(light); 
        
        // 2. Hemisphere Light (Adds realistic volume and 3D depth by simulating sky/ground ambient bounce)
        const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.8);
        hemiLight.position.set(0, 5, 0);
        scene.add(hemiLight);

        // 3. Rim Light (A subtle cyan light from behind to make her pop out from the dark background)
        const rimLight = new THREE.DirectionalLight(0x0dcaf0, 0.6);
        rimLight.position.set(-1, 0.5, -2).normalize();
        scene.add(rimLight);

        let currentVrm = null; let isTalking = false; const clock = new THREE.Clock();
        const lookAtTarget = new THREE.Object3D(); scene.add(lookAtTarget); 
        
        let blinkTimer = 0; let blinkDuration = 0.15; let nextBlink = 2.0; 
        let eyeTimer = 0; let nextEyeMove = 1.0; let targetEyeX = 0; let targetEyeY = 1.4; 
        
        const poses = {
            'neutral': { LUAz: 1.25, RUAz: -1.25, LUAx: 0, RUAx: 0, LLAz: 0.05, RLAz: -0.05, LClench: 0.1, RClench: 0.1, HeadX: 0 },
            'lecturing': { LUAz: 1.25, RUAz: -0.6, LUAx: 0, RUAx: 0.2, LLAz: 0.05, RLAz: -1.0, LClench: 0.1, RClench: 0.8, HeadX: -0.05 },
            'thinking': { LUAz: 1.25, RUAz: -0.2, LUAx: 0, RUAx: 0.1, LLAz: 0.05, RLAz: -2.1, LClench: 0.1, RClench: 0.8, HeadX: 0.08 },
            'smug': { LUAz: 1.0, RUAz: -1.0, LUAx: 0.2, RUAx: 0.2, LLAz: 1.1, RLAz: -1.1, LClench: 0.2, RClench: 0.2, HeadX: -0.08 },
            'sad': { LUAz: 1.35, RUAz: -1.35, LUAx: 0.1, RUAx: 0.1, LLAz: 0.02, RLAz: -0.02, LClench: 0.3, RClench: 0.3, HeadX: 0.2 },
            'happy': { LUAz: 1.1, RUAz: -1.1, LUAx: -0.2, RUAx: -0.2, LLAz: 0.5, RLAz: -0.5, LClench: 0.0, RClench: 0.0, HeadX: -0.1 }, 
            'angry': { LUAz: 1.2, RUAz: -1.2, LUAx: 0.2, RUAx: 0.2, LLAz: 1.2, RLAz: -1.2, LClench: 1.0, RClench: 1.0, HeadX: 0.1 },
            'surprised': { LUAz: 1.1, RUAz: -1.1, LUAx: -0.1, RUAx: -0.1, LLAz: 1.8, RLAz: -1.8, LClench: 0.5, RClench: 0.5, HeadX: -0.15 }
        };
        let currentPose = 'neutral';

        const loader = new GLTFLoader(); loader.register((parser) => new VRMLoaderPlugin(parser));
        loader.load('/static/sara.vrm', (gltf) => {
            const vrm = gltf.userData.vrm; VRMUtils.removeUnnecessaryJoints(gltf.scene);
            scene.add(vrm.scene); currentVrm = vrm; vrm.scene.rotation.y = Math.PI;
            if (vrm.lookAt) vrm.lookAt.target = lookAtTarget;
            if(vrm.humanoid) {
                vrm.humanoid.getNormalizedBoneNode('leftUpperArm').rotation.z = 1.25;
                vrm.humanoid.getNormalizedBoneNode('rightUpperArm').rotation.z = -1.25;
            }
        });

        function lerpBone(boneName, axis, targetValue, delta, speed = 6.0) {
            if (!currentVrm || !currentVrm.humanoid) return;
            const bone = currentVrm.humanoid.getNormalizedBoneNode(boneName);
            if (bone) {
                const safeAlpha = Math.min(delta * speed, 1.0);
                bone.rotation[axis] = THREE.MathUtils.lerp(bone.rotation[axis], targetValue, safeAlpha);
            }
        }

        function animate() {
            requestAnimationFrame(animate);
            let delta = clock.getDelta();
            if (delta > 0.1) delta = 0.1; 
            const t = clock.elapsedTime;
            
            const newAspect = window.innerWidth / window.innerHeight;
            if (Math.abs(camera.aspect - newAspect) > 0.05) {
                camera.aspect = newAspect;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }

            if (currentVrm && currentVrm.humanoid) {
                currentVrm.update(delta); 

                eyeTimer += delta;
                if (eyeTimer > nextEyeMove) {
                    if (Math.random() > (isMobile ? 0.7 : 0.6)) { 
                        targetEyeX = (Math.random() - 0.5) * eyeDartMultiplier; 
                        targetEyeY = 1.4 + (Math.random() - 0.5) * eyeVerticalRange; 
                    } 
                    else { targetEyeX = 0.0; targetEyeY = 1.4; }
                    eyeTimer = 0; nextEyeMove = Math.random() * eyeDartDelayMax + eyeDartDelayMin; 
                }
                
                if (currentPose === 'thinking') { targetEyeX = isMobile ? 0.4 : 1.0; targetEyeY = isMobile ? 1.6 : 2.0; } 
                else if (currentPose === 'sad') { targetEyeX = 0.0; targetEyeY = isMobile ? 1.0 : 0.2; }
                
                targetEyeX = THREE.MathUtils.clamp(targetEyeX, -0.5, 0.5);
                targetEyeY = THREE.MathUtils.clamp(targetEyeY, 1.0, 1.8);

                const safeEyeAlpha = Math.min(delta * 10.0, 1.0);
                lookAtTarget.position.x = THREE.MathUtils.lerp(lookAtTarget.position.x, targetEyeX, safeEyeAlpha);
                lookAtTarget.position.y = THREE.MathUtils.lerp(lookAtTarget.position.y, targetEyeY, safeEyeAlpha);

                blinkTimer += delta;
                if (blinkTimer > nextBlink) {
                    let blinkValue = 0; let timeInBlink = blinkTimer - nextBlink;
                    if (timeInBlink < blinkDuration / 2) blinkValue = timeInBlink / (blinkDuration / 2); 
                    else if (timeInBlink < blinkDuration) blinkValue = 1.0 - ((timeInBlink - blinkDuration / 2) / (blinkDuration / 2)); 
                    else { blinkTimer = 0; nextBlink = Math.random() * 4 + 1.5; blinkValue = 0; }
                    if (currentVrm.expressionManager) currentVrm.expressionManager.setValue('blink', blinkValue);
                }

                if (isTalking && currentVrm.expressionManager) currentVrm.expressionManager.setValue('aa', (Math.sin(t * 25) + 1) / 2 * 0.7);
                else if (currentVrm.expressionManager) currentVrm.expressionManager.setValue('aa', 0);

                const target = poses[currentPose] || poses['neutral'];
                lerpBone('leftUpperArm', 'z', target.LUAz, delta); lerpBone('rightUpperArm', 'z', target.RUAz, delta);
                lerpBone('leftUpperArm', 'x', target.LUAx, delta); lerpBone('rightUpperArm', 'x', target.RUAx, delta);
                lerpBone('leftLowerArm', 'z', target.LLAz, delta); lerpBone('rightLowerArm', 'z', target.RLAz, delta);
                lerpBone('head', 'x', target.HeadX, delta);

                ['Index', 'Middle', 'Ring', 'Little'].forEach((finger, index) => {
                    const fingerPulse = Math.sin(t * fingerSpeed + index * (isMobile ? 0.2 : 0.3)) * fingerAmplitude; 
                    ['Proximal', 'Intermediate'].forEach(joint => {
                        lerpBone('left' + finger + joint, 'z', target.LClench + fingerPulse, delta, 8.0);
                        lerpBone('right' + finger + joint, 'z', -(target.RClench + fingerPulse), delta, 8.0);
                    });
                });

                const chest = currentVrm.humanoid.getNormalizedBoneNode('chest'); if (chest) chest.rotation.x = Math.sin(t * 1.5) * 0.02; 
                const head = currentVrm.humanoid.getNormalizedBoneNode('head'); if (head) head.rotation.z = Math.sin(t * 0.8) * 0.02;
                const hips = currentVrm.humanoid.getNormalizedBoneNode('hips');
                if (hips) { hips.position.x = Math.sin(t * 0.6) * 0.03; hips.rotation.y = Math.sin(t * 0.4) * 0.02; }
            }
            renderer.render(scene, camera);
        }
        animate();

        function appendToChatLog(sender, text, isSara) {
            const chatBox = document.getElementById('chat-messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = `p-2 rounded-3 text-break shadow-sm ${isSara ? 'msg-sara' : 'msg-user'}`;
            
            const nameDiv = document.createElement('div');
            nameDiv.className = `fw-bold small mb-1 ${isSara ? 'text-danger' : 'text-info'}`;
            nameDiv.innerText = sender;
            
            const textDiv = document.createElement('div');
            textDiv.className = 'text-light small';
            textDiv.innerText = text;
            
            msgDiv.appendChild(nameDiv); 
            msgDiv.appendChild(textDiv); 
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        let typeInterval; let fullText = "";

        function resetUIState() {
            isTalking = false;
            setExpression('neutral');
            document.getElementById('speech-wrapper').style.display = 'none';
            const chatInput = document.getElementById('chat-input');
            chatInput.disabled = false;
            chatInput.placeholder = "Ask Sara a question...";
            chatInput.focus();
        }

        function initNetwork() {
            fetch('/history')
                .then(response => response.json())
                .then(data => {
                    data.history.forEach(msg => {
                        appendToChatLog(msg.sender, msg.text, msg.isSara);
                    });
                });

            const evtSource = new EventSource("/stream");
            const statusEl = document.getElementById('conn-status');
            
            evtSource.onopen = () => { 
                statusEl.innerText = 'LIVE'; 
                statusEl.className = 'text-success fw-bold'; 
            };
            evtSource.onerror = () => { 
                statusEl.innerText = 'RECONNECTING...'; 
                statusEl.className = 'text-warning fw-bold'; 
            };
            
            evtSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.action === "chat_update") {
                    appendToChatLog(data.username, data.text, false);
                }
                else if (data.action === "think") {
                    setExpression('thinking');
                } 
                else if (data.action === "speak") {
                    setExpression(data.emotion);
                    appendToChatLog("Sara", data.text, true);
                    
                    document.getElementById('speech-wrapper').style.display = 'flex';
                    const textEl = document.getElementById('text');
                    const latexEl = document.getElementById('latex');
                    fullText = data.text; textEl.innerText = ""; clearInterval(typeInterval);
                    
                    if (data.latex) katex.render(data.latex, latexEl, { throwOnError: false }); 
                    else latexEl.innerHTML = "";
                    
                    const audioObj = document.getElementById('sara-audio');
                    audioObj.src = data.audio_url;
                    
                    audioObj.onerror = function() {
                        console.error("Audio failed to load. Falling back to text mode.");
                        textEl.innerText = fullText;
                        textEl.classList.remove('cursor');
                        
                        // --- UPGRADED TEXT READING TIME ---
                        // Gives you plenty of time to read long text blocks if the audio fails.
                        setTimeout(resetUIState, fullText.length * 70 + 4000); 
                    };

                    audioObj.onloadedmetadata = function() {
                        isTalking = true;
                        let charDelay = ((audioObj.duration - 0.1) * 1000) / fullText.length;
                        if (charDelay < 10) charDelay = 10; 
                        
                        let i = 0;
                        typeInterval = setInterval(() => {
                            textEl.innerText += fullText.charAt(i); i++;
                            if (i >= fullText.length) { clearInterval(typeInterval); textEl.classList.remove('cursor'); } 
                            else textEl.classList.add('cursor');
                        }, charDelay);
                        
                        audioObj.play().catch(e => {
                            console.error("Audio playback blocked:", e);
                            setTimeout(resetUIState, fullText.length * 70 + 4000);
                        });
                    };
                    
                    audioObj.onended = function() {
                        // --- UPGRADED TEXT READING TIME ---
                        // Leaves the text bubble visibly on screen for 4 full seconds after she finishes speaking.
                        setTimeout(resetUIState, 4000);
                    };
                }
            };
        }

        function setExpression(emotion) {
            if (!currentVrm || !currentVrm.expressionManager) return;
            
            const expressions = ['happy', 'angry', 'sad', 'relaxed', 'surprised', 'neutral', 'blink'];
            expressions.forEach(exp => {
                if (currentVrm.expressionManager.getExpression(exp)) {
                    currentVrm.expressionManager.setValue(exp, 0.0);
                }
            });

            const logicMap = {
                'happy': { face: 'happy', pose: 'happy' }, 
                'angry': { face: 'angry', pose: 'angry' },
                'surprised': { face: 'surprised', pose: 'surprised' },
                'lecturing': { face: 'neutral', pose: 'lecturing' }, 
                'smug': { face: 'relaxed', pose: 'smug' },
                'sad': { face: 'sad', pose: 'sad' }, 
                'thinking': { face: 'neutral', pose: 'thinking' },
                'blush': { face: 'happy', pose: 'smug' },
                'neutral': { face: 'neutral', pose: 'neutral' }
            };
            
            const current = logicMap[emotion] || logicMap['neutral'];
            
            if (current.face !== 'neutral' && currentVrm.expressionManager.getExpression(current.face)) {
                currentVrm.expressionManager.setValue(current.face, 1.0);
            }
            
            currentPose = current.pose;
        }

        document.getElementById('chat-input').addEventListener('keypress', function (e) {
            if (e.key === 'Enter' && this.value.trim() !== '') {
                fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ username: globalUsername, text: this.value.trim() })
                });
                
                this.value = ''; this.disabled = true; this.placeholder = "Broadcasting to Sara...";
            }
        });
    </script>
</body>
</html>
"""

# ==========================================
# 2. GROUP STUDY BRAIN (SaraCore)
# ==========================================
class SaraCore:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.db = chromadb.PersistentClient(path=DB_PATH)
        self.memory = self.db.get_or_create_collection(name="long_term_chat")
        self.trust_db = self.db.get_or_create_collection(name="trust_scores")
        self.chat_history = [] 
        self.max_history_length = 15 
        
        self.news_cache = "Quiet day globally."
        self.last_news_fetch = 0
        self.user_contexts = {}

    def get_life_state(self):
        now = datetime.datetime.now()
        age = now.year - SARA_BIRTH.year - ((now.month, now.day) < (SARA_BIRTH.month, SARA_BIRTH.day))
        
        if now < datetime.datetime(2026, 4, 20): return "Sara", age, "JEE Aspirant", "PCM."
        elif now < datetime.datetime(2026, 6, 1): return "Sara", age, "JEE Advanced Aspirant", "Physics & Maths."
        elif now < datetime.datetime(2030, 3, 19): return "Sara", age, "IIT Kanpur Undergrad (EE)", "Control Systems."
        elif now < datetime.datetime(2032, 6, 1): return "Sara", age, "IISc Bangalore MTech (ESE)", "Microelectronics, VLSI."
        elif now < datetime.datetime(2036, 6, 1): return "Sara", age, "Integrated PhD Researcher (IISc)", "System Packaging."
        else: return "Dr. Sara", age, "PhD / Research Lead", "Full Professional Knowledge."

    def process_trust(self, username, text):
        sentiment = TextBlob(text).sentiment.polarity
        self.trust_db.add(documents=[str(sentiment)], metadatas=[{"user": username}], ids=[f"t_{time.time()}"])
        results = self.trust_db.get(where={"user": username})
        scores = results['documents'] if results else []
        return sum(float(s) for s in scores) / len(scores) if scores else 0.0

    def get_long_term_memory(self, text):
        try:
            count = self.memory.count()
            if count == 0: return ""
            n_res = min(3, count)
            results = self.memory.query(query_texts=[text], n_results=n_res)
            if results and results['documents'] and results['documents'][0]:
                memories = "\n".join(results['documents'][0])
                return f"\nRECALLED PAST MEMORIES:\n{memories}\n"
        except: pass
        return ""

    def update_global_news(self):
        now = time.time()
        if now - self.last_news_fetch > 3600:
            try:
                url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=3&apiKey={NEWS_API_KEY}"
                data = requests.get(url, timeout=5).json()
                if data.get('articles'):
                    headlines = [art['title'] for art in data['articles']]
                    self.news_cache = " | ".join(headlines)
                self.last_news_fetch = now
            except Exception:
                pass
        return self.news_cache

    def get_user_context(self, username, ip_address):
        now = time.time()
        if username in self.user_contexts and now - self.user_contexts[username]['last_update'] < 1800:
            return self.user_contexts[username]

        location = "Unknown"
        weather = "Unknown"

        if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
            try:
                ip_address = requests.get("https://api.ipify.org", timeout=3).text
            except Exception:
                pass

        if ip_address and ip_address not in ['127.0.0.1', 'localhost', '::1']:
            try:
                # 1. Fast Geolocation
                ip_data = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=4).json()
                if ip_data.get('status') == 'success':
                    city = ip_data['city']
                    country = ip_data['country']
                    lat = ip_data['lat']
                    lon = ip_data['lon']
                    location = f"{city}, {country}"

                    # 2. Fast Open-Meteo Weather
                    try:
                        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                        weather_req = requests.get(weather_url, timeout=4).json()
                        
                        if 'current_weather' in weather_req:
                            temp_c = weather_req['current_weather']['temperature']
                            w_code = weather_req['current_weather']['weathercode']
                            conditions = "Clear" if w_code <= 1 else "Partly Cloudy" if w_code <= 3 else "Foggy" if w_code <= 48 else "Raining" if w_code <= 67 else "Snowing" if w_code <= 79 else "Stormy"
                            weather = f"{conditions}, {temp_c}°C"
                    except Exception as e:
                        print(f"[Context Engine] Open-Meteo failed: {e}")
                            
            except Exception as e:
                print(f"[Warning] Context gathering failed for {ip_address}: {e}")

        print(f"\n[Context Engine] Updated context for {username} - IP: {ip_address} | Location: {location} | Weather: {weather}")

        self.user_contexts[username] = {'location': location, 'weather': weather, 'last_update': now}
        return self.user_contexts[username]

    def process_message(self, username, user_text, user_ip):
        broadcast_to_clients({
            "action": "chat_update",
            "username": username,
            "text": user_text
        })
        broadcast_to_clients({"action": "think"})

        name, age, stage, knowledge = self.get_life_state()
        user_trust = self.process_trust(username, user_text)
        memory_string = self.get_long_term_memory(user_text)
        
        world_news = self.update_global_news()
        user_context = self.get_user_context(username, user_ip)

        active_users = set()
        for msg in self.chat_history:
            if msg['role'] == 'user':
                try:
                    active_users.add(msg['content'].split(':')[0])
                except:
                    pass
        active_users.add(username) 
        active_users_str = ", ".join(active_users)

        system_prompt = f"""
        Identity: {name} ({age}y/o). Stage: {stage}. Knowledge: {knowledge}.
        Context: You are hosting a group study session. 
        Active students in the room right now: {active_users_str}.
        Current Speaker: {username}. 
        Their Location: {user_context['location']}. Local Weather: {user_context['weather']}.
        Your trust level with {username}: {user_trust:.2f}/1.0. 
        
        World News Summary: {world_news}
        
        {memory_string}
        
        CRITICAL FORMATTING & BEHAVIOR INSTRUCTIONS:
        1. You MUST begin your very first word with ONE emotion tag enclosed in asterisks. You MUST choose exactly ONE from this list: *happy*, *angry*, *sad*, *surprised*, *smug*, *lecturing*, *thinking*, *blush*, *neutral*. 
           Example: *lecturing* Let's get back to work.
        2. Keep spoken text concise (1-3 sentences).
        3. If a student directly asks about the weather, news, or their location, you MUST use the context provided above to answer them accurately, and then smoothly pivot back to the study session.
        4. ALL math equations MUST be wrapped in double dollar signs. Example: $$ E=mc^2 $$
        5. NEVER use \\[ \\] or \\( \\) for math.
        6. DO NOT invent fake students, names, or ongoing topics that are not in the current chat history. Only interact with the active students listed above.
        """

        messages_to_send = [{"role": "system", "content": system_prompt}]
        messages_to_send.extend(self.chat_history)  
        messages_to_send.append({"role": "user", "content": f"{username}: {user_text}"})

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=250
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"*sad* I lost connection to the Groq servers. Error: {e}"

        self.chat_history.append({"role": "user", "content": f"{username}: {user_text}"})
        self.chat_history.append({"role": "assistant", "content": reply})
        if len(self.chat_history) > self.max_history_length:
            self.chat_history = self.chat_history[-self.max_history_length:]

        try: self.memory.add(documents=[f"{username}: {user_text} | Sara: {reply}"], ids=[str(time.time())])
        except: pass

        emotion = "neutral"
        match = re.search(r"^\s*\*([a-zA-Z]+)\*", reply)
        if not match: 
            match = re.search(r"\*([a-zA-Z]+)\*", reply)
            
        if match: 
            emotion = match.group(1).strip().lower()
            
        latex_blocks = re.findall(r"\$\$(.*?)\$\$", reply, re.DOTALL)
        latex_blocks += re.findall(r"\\\[(.*?)\\\]", reply, re.DOTALL)
        latex = " \\\\ ".join([block.strip() for block in latex_blocks])
            
        clean_text = re.sub(r"\$\$.*?\$\$", "", reply, flags=re.DOTALL)
        clean_text = re.sub(r"\\\[.*?\\\]", "", clean_text, flags=re.DOTALL) 
        clean_text = re.sub(r"\\\(.*?\\\)", "", clean_text, flags=re.DOTALL) 
        clean_text = re.sub(r"\*.*?\*", "", clean_text).strip()
        if not clean_text: clean_text = "Here is the calculation."

        fname = f"tts_{uuid.uuid4().hex[:6]}.mp3"
        filepath = os.path.join(AUDIO_DIR, fname)
        
        try:
            asyncio.run(edge_tts.Communicate(clean_text, "en-GB-SoniaNeural").save(filepath))
        except Exception as e:
            print(f"[Warning] Audio generation failed: {e}")
        
        broadcast_to_clients({
            "action": "speak",
            "text": clean_text,
            "latex": latex,
            "emotion": emotion,
            "audio_url": f"/static/audio/{fname}"
        })

# ==========================================
# 3. FLASK SERVER & LOOPHOLE CLI
# ==========================================
sara_core = SaraCore()
request_queue = queue.Queue()
loophole_process = None

def llm_worker():
    while True:
        try:
            req = request_queue.get()
            sara_core.process_message(req['username'], req['text'], req.get('ip'))
        except Exception as e:
            print(f"[Worker Error] Unhandled Exception in Processing: {e}")
        finally:
            request_queue.task_done()

threading.Thread(target=llm_worker, daemon=True).start()

def cleanup_loophole():
    global loophole_process
    if loophole_process:
        print("\n[Tunnel] Shutting down Loophole tunnel...")
        loophole_process.terminate()
        loophole_process.wait()
        print("[Tunnel] Loophole tunnel successfully closed.")

atexit.register(cleanup_loophole)

def start_loophole():
    global loophole_process
    print(f"\n[Tunnel] Attempting to start Loophole on hostname: {LOOPHOLE_HOSTNAME}")
    try:
        cmd = ["loophole", "http", "5000", "--hostname", LOOPHOLE_HOSTNAME]
        loophole_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[Tunnel] SUCCESS! Your friends can connect at: https://{LOOPHOLE_HOSTNAME}.loophole.site")
    except FileNotFoundError:
        print("[Tunnel ERROR] Loophole CLI is not installed or not in PATH.")
    except Exception as e:
        print(f"[Tunnel ERROR] Failed to start Loophole: {e}")

@app.route('/')
def index():
    _, age, stage, _ = sara_core.get_life_state()
    dynamic_html = html_content.replace("[[SARA_STAGE]]", stage).replace("[[SARA_AGE]]", str(age))
    return dynamic_html

@app.route('/history', methods=['GET'])
def get_history():
    formatted_history = []
    for msg in sara_core.chat_history:
        if msg['role'] == 'user':
            parts = msg['content'].split(': ', 1)
            if len(parts) == 2:
                formatted_history.append({'sender': parts[0], 'text': parts[1], 'isSara': False})
        elif msg['role'] == 'assistant':
            clean_text = re.sub(r"\*.*?\*", "", msg['content'])
            clean_text = re.sub(r"\$\$.*?\$\$", "[Shared a calculation]", clean_text, flags=re.DOTALL)
            clean_text = re.sub(r"\\\[.*?\\\]", "[Shared a calculation]", clean_text, flags=re.DOTALL)
            formatted_history.append({'sender': 'Sara', 'text': clean_text.strip(), 'isSara': True})
            
    return {"history": formatted_history}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if user_ip: 
        user_ip = user_ip.split(',')[0].strip()
        
    request_queue.put({"username": data['username'], "text": data['text'], "ip": user_ip})
    return {"status": "queued"}

@app.route('/stream')
def stream():
    def event_stream():
        q = queue.Queue(maxsize=20)
        sse_clients.append(q)
        try:
            yield ":" + (" " * 2048) + "\n\n"
            while True:
                msg = q.get()
                yield f"data: {msg}\n\n"
        finally:
            if q in sse_clients:
                sse_clients.remove(q)
                
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

if __name__ == "__main__":
    print("\n==========================================")
    print(" SARA MULTI-USER GROUP STUDY ONLINE")
    print(" 1. Model must be at static/sara.vrm")
    print(" 2. Starting local server and Tunnel...")
    print("==========================================\n")
    
    threading.Thread(target=start_loophole, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
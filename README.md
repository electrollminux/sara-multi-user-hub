# Sara - 3D AI Group Study Hub

Sara is a real-time, multi-user 3D AI mentor designed to host group study sessions. Built with Flask, Three.js, and Llama 3, she acts as a slightly strict, tsundere physics and mathematics tutor. 

She features real-time voice synthesis, dynamic 3D facial expressions and body kinematics, long-term vector memory, and live environment awareness (location, weather, and world news).

## Features
* **Multiplayer Sync:** Multiple users can join the session simultaneously via Loophole tunneling. State is synced using Server-Sent Events (SSE).
* **Dynamic 3D Kinematics:** Sara renders in the browser using `@pixiv/three-vrm`. Her eye darts, breathing, finger curling, and emotional poses adapt dynamically to mobile vs. desktop screens.
* **Context-Aware Brain:** Powered by Groq (Llama-3.1-8b), she dynamically tracks active users in the room, fetches their local weather (via Open-Meteo), reads global news, and pulls past conversations from a ChromaDB vector database.
* **Low-Latency Voice:** Utilizes Microsoft `edge-tts` for high-quality, real-time voice responses mapped to 3D lip-sync blendshapes.

## Setup & Installation

### 1. Prerequisites
* Python 3.8+
* A Groq API Key (Free)
* A NewsAPI Key (Free)
* [Loophole CLI](https://loophole.cloud/) installed for network tunneling.

### 2. Clone & Install
```bash
git clone [https://github.com/YOUR_USERNAME/sara-group-hub.git](https://github.com/YOUR_USERNAME/sara-group-hub.git)
cd sara-group-hub
pip install -r requirements.txt
```
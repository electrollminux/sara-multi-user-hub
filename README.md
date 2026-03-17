# Sara - 3D AI Group Study Hub

![Mobile View] (assets\mobile_view.jpeg)
![Chat Overview] (assets\chat_overview.png)
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
git clone https://github.com/electrollminux/sara-multi-user-hub.git
cd sara-group-hub
pip install -r requirements.txt
```
## 3. How to Invite Your Friends

You don't need to host this on an expensive cloud server! Because it has integrated **Loophole**, the Python script automatically creates a secure, public tunnel to your local machine the moment you run it.

1. **Start the server:** Run `python sara_multi_user.py` on your computer.
2. **Find the link:** Look at your terminal output. You will see a success message that looks like this:
   `[Tunnel] SUCCESS! Your friends can connect at: https://<YOUR_LOOPHOLE_HOSTNAME_HERE>.loophole.site`
3. **Share it:** Copy that URL and send it to your friends on Discord, WhatsApp, etc. 
4. **Join the Hub:** They just need to click the link on their phone or PC. They don't need to install Python, download the 3D model, or configure any API keys. Everything runs off your machine!

*Note: Because this is a live group chat, everyone will see the same messages, and Sara will interact with whoever speaks, keeping track of different users seamlessly.*
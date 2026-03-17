# Sara - 3D AI Group Study Hub

![Mobile_View](https://github.com/electrollminux/sara-multi-user-hub/blob/main/assets/mobile_view.jpeg?raw=true)
![Chat_Overview](https://github.com/electrollminux/sara-multi-user-hub/blob/main/assets/chat_overview.png?raw=true)

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

## 4. License & Customization

This project uses a split-licensing model to protect both the open-source code and the original 3D artist's rights.

**1. The Source Code (MIT License)**
All Python, JavaScript, and HTML code in this repository is completely open-source and licensed under the [MIT License](LICENSE). You are free to modify, distribute, and commercialize the *codebase itself*.

**2. The Default 3D Asset (`sara.vrm`)**
The default 3D avatar included in this project (`static/sara.vrm`) is subject to its original creator's terms of use and is **NOT** covered by the MIT License. As long as you are using this default model, you must adhere to these rules:
* **Attribution:** Required (Original Creator: [imslowash](https://hub.vroid.com/en/users/73989979))
* **Commercial Use:** Strictly Prohibited (No individual or corporate commercial use).
* **Alterations & Redistribution:** Allowed, provided these exact non-commercial and attribution conditions are maintained.

**3. Want to commercialize this project? Just swap the model!**
The AI and 3D engine are completely modular. If you want to use this project for a commercial product, SaaS, or corporate tool, simply delete `static/sara.vrm` and replace it with your own `.vrm` avatar (one that you made or have commercial rights to). Name your new file `your_new_model.vrm`, drop it in the `static` folder, and the non-commercial restriction is lifted!

1. Drop your new `.vrm` file into the `static/` folder.
2. Open `sara_multi_user.py` and locate the `GLTFLoader` in the JavaScript section (around line [344](https://github.com/electrollminux/sara-multi-user-hub/blob/78ff072eeb591a40501c372f033d00603eea56d0/main.py#L344)).
3. Change the file path from `'/static/sara.vrm'` to the name of your new file:
   ```javascript
   loader.load('/static/your_new_model.vrm', (gltf) => {...}
   ```
4. Save the file and restart your server. The new avatar will automatically inherit the procedural blinking, breathing, and lip-sync animations! 
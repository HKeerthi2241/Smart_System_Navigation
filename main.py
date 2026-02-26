import numpy as np
import matplotlib.pyplot as plt
import math
import json
import requests
import tempfile
from gtts import gTTS
import pygame
from collections import defaultdict
import heapq

# =========================
# LLM CONFIGURATION
# =========================
CONFIG = {
    "lm_url": "http://127.0.0.1:1234/v1/chat/completions",
    "model": "mistralai/mistral-7b-instruct-v0.3",
    "node_radius": 3.0   # 🔔 narration trigger distance
}

# =========================
# CAMPUS NODES
# =========================
nodes = np.array([
    [22.5, 57.5],   # Admin Block (0)
    [29.2, 43.2],   # Library (1)
    [15.6, 15.6],   # CSE (2)
    [6.0, 2.7],     # Mechanical (3)
    [52.5, 30.1],   # Cafeteria (4)
    [58.5, 45.1]    # Auditorium (5)
])

building_names = [
    "Admin Block",
    "Library",
    "Computer Science Department",
    "Mechanical Workshop",
    "Cafeteria",
    "Auditorium"
]

# Corridor connections
adjacent_pairs = [
    (0, 1), (1, 2), (2, 3),
    (2, 4), (4, 5), (5, 0)
]

block_labels = {
    (2, 3): "Block A",
    (4, 5): "Block B"
}

# =========================
# LOAD NODE DESCRIPTIONS
# =========================
with open("nodes_data.json", "r", encoding="utf-8") as f:
    NODE_INFO = json.load(f)

# =========================
# GRAPH BUILD
# =========================
graph = defaultdict(list)
for a, b in adjacent_pairs:
    graph[a].append(b)
    graph[b].append(a)

# =========================
# HELPER FUNCTIONS
# =========================
def nearest_node_index(x, y):
    return int(np.argmin([math.hypot(x - nx, y - ny) for nx, ny in nodes]))

def distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

# =========================
# DIJKSTRA PATH PLANNER
# =========================
def dijkstra_path(start, goal):
    pq = [(0, start, [start])]
    visited = set()

    while pq:
        dist, node, path = heapq.heappop(pq)

        if node == goal:
            return path

        if node in visited:
            continue

        visited.add(node)

        for neighbor in graph[node]:
            if neighbor not in visited:
                x1, y1 = nodes[node]
                x2, y2 = nodes[neighbor]
                weight = math.hypot(x2 - x1, y2 - y1)

                heapq.heappush(
                    pq,
                    (dist + weight, neighbor, path + [neighbor])
                )

    return []

# =========================
# DRAW MAP
# =========================
def draw_map():
    plt.ion()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title("Smart Campus Navigation System")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True)

    for i, (x, y) in enumerate(nodes):
        ax.plot(x, y, "ko")
        ax.text(x + 0.6, y + 0.6, building_names[i], fontsize=9)

    corridor_width = 2.0
    for a, b in adjacent_pairs:
        x1, y1 = nodes[a]
        x2, y2 = nodes[b]

        angle = math.atan2(y2 - y1, x2 - x1)
        nx, ny = -math.sin(angle), math.cos(angle)
        ox, oy = nx * corridor_width / 2, ny * corridor_width / 2

        px = [x1 + ox, x1 - ox, x2 - ox, x2 + ox, x1 + ox]
        py = [y1 + oy, y1 - oy, y2 - oy, y2 + oy, y1 + oy]

        ax.plot(px, py, "r", lw=2)
        ax.plot([x1, x2], [y1, y2], "g--")

        if (a, b) in block_labels:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2,
                    block_labels[(a, b)],
                    color="blue", fontsize=12, fontweight="bold")

    cursor, = ax.plot([5], [5], "bo", markersize=10)
    plt.show()
    return cursor

# =========================
# LLM QUERY
# =========================
def query_llm(node_name):
    key = node_name.lower().replace(" ", "_")
    node = NODE_INFO.get(key)

    if not node:
        return f"You are approaching {node_name}."

    prompt = f"""
You are an AI campus tour guide for GITAM University Bangalore.
Generate a natural spoken narration lasting 30 to 60 seconds.

Building Name: {node["display_name"]}

Base Description:
{node["base_description"]}

Key Points:
{chr(10).join("- " + p for p in node["extra_points"])}
"""

    payload = {
        "model": CONFIG["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 300
    }

    try:
        r = requests.post(CONFIG["lm_url"], json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ LLM error:", e)
        return f"You are approaching {node_name}."

# =========================
# VOICE OUTPUT
# =========================
def stop_audio():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except:
        pass

def speak(text):
    stop_audio()

    tts = gTTS(text=text, lang="en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        path = f.name

    tts.save(path)

    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# =========================
# MAIN LOOP
# =========================
cursor = draw_map()
current_x, current_y = 5.0, 5.0
narrated_nodes = set()

print("🎙 Smart Campus Navigation Started (Dijkstra Enabled)")

while True:
    x = input("\nEnter X (q to quit): ")
    if x.lower() == "q":
        stop_audio()
        break

    y = input("Enter Y: ")
    yaw = input("Enter Yaw (degrees): ")

    try:
        x, y, yaw = float(x), float(y), float(yaw)
    except:
        print("❌ Invalid input")
        continue

    if abs(yaw) > 10:
        speak("You are facing slightly to the right" if yaw > 0
              else "You are facing slightly to the left")

    start = nearest_node_index(current_x, current_y)
    end = nearest_node_index(x, y)

    path = dijkstra_path(start, end)
    print("🧭 Path:", " → ".join(building_names[i] for i in path))

    for idx in path[1:]:
        tx, ty = nodes[idx]
        node_name = building_names[idx]

        for t in np.linspace(0, 1, 40):
            nx = current_x + t * (tx - current_x)
            ny = current_y + t * (ty - current_y)

            cursor.set_data([nx], [ny])
            plt.pause(0.03)

            # 🔔 Proximity-based description trigger
            if distance(nx, ny, tx, ty) <= CONFIG["node_radius"] and idx not in narrated_nodes:
                print(f"🔊 Approaching: {node_name}")
                narrated_nodes.add(idx)
                speak(query_llm(node_name))

        current_x, current_y = tx, ty

print("🛑 Navigation stopped")
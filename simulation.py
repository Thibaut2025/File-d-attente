import pygame
import numpy as np
import time
import sys
import ctypes
import matplotlib.pyplot as plt

# Initialisation
pygame.init()
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)
# WIDTH, HEIGHT = 1000, 700
win = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Simulation - File d'attente MTN (Interactive)")

# Couleurs
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 102, 204)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)

# Paramètres de base
ARRIVAL_RATE_NORMAL = 1 / 5 # 1 client toutes les 5 secondes
SERVICE_RATE = 1 / 20 # 1 client toutes les 20 secondes
MAX_CLIENTS = 10 # Nombre maximum de clients à générer
SPEED = 90  # Vitesse de la simulation (FPS)
Temps_simulation = 60  # Durée de la simulation en secondes
# Génération dynamique
def generate_clients(arrival_rate, service_rate, n_clients):
    U = np.random.uniform(0, 1, size=n_clients)
    inter_arrival_times = [ -1 / arrival_rate * np.log(u) for u in U ]  # méthode d'inversion
    arrival_times = np.cumsum(inter_arrival_times)
    V = np.random.uniform(0, 1, size=n_clients)
    service_times = [ -1 / service_rate * np.log(v) for v in V ]  # méthode d'inversion
    # inter_arrival_times = np.random.exponential(scale=1 / arrival_rate, size=n_clients) #Methode directe
    return [Client(i, arrival_times[i], service_times[i]) for i in range(n_clients)]

class Client:
    def __init__(self, id, arrival_time, service_time):
        self.id = id
        self.arrival_time = arrival_time
        self.service_time = service_time
        self.start_service_time = None
        self.end_service_time = None
        self.in_service = False
        self.finished = False
        self.x = 50  # Départ à gauche de l'écran
        self.y = 500
        self.target_x = 40 + id * 20
        self.target_y = 600
        self.color = BLUE

    def update_position(self):
        if self.x < self.target_x:
            self.x += 2
        elif self.x > self.target_x:
            self.x -= 2
        if self.y < self.target_y:
            self.y += 2
        elif self.y > self.target_y:
            self.y -= 2

    def draw(self, win):
        if not self.finished:
            pygame.draw.circle(win, self.color, (int(self.x), int(self.y)), 10)

class Agent:
    def __init__(self, id):
        self.id = id
        self.busy = False
        self.client = None
        self.x = 700
        self.y = 100 + id * 100

    def draw(self, win):
        color = RED if self.busy else GREEN
        pygame.draw.rect(win, color, (self.x, self.y, 60, 40))
        font = pygame.font.SysFont("Arial", 14)
        status = "OCC." if self.busy else "LIBRE"
        status_color = BLACK
        text = font.render(status, True, status_color)
        win.blit(text, (self.x + 5, self.y + 10))
        # if self.client:
        #     pygame.draw.circle(win, self.client.color, (self.x + 30, self.y + 60), 10)

def run_simulation(n_agents=3):
    clients = generate_clients(ARRIVAL_RATE_NORMAL, SERVICE_RATE, MAX_CLIENTS)
    agents = [Agent(i) for i in range(n_agents)]
    queue = []
    clock = pygame.time.Clock()
    start_time = time.time()
    running = True
    current_client_index = 0
    stats_wait_times = []
    wait_time_over_time = []

    while running:
        clock.tick(SPEED)
        win.fill(WHITE)
        current_time = time.time() - start_time
        font = pygame.font.SysFont("Arial", 18)
        info_lines = [
            f"Temps: {int(current_time)}s",
            f"Agents: {n_agents} (+/- avec ↑/↓)",
            f"En file: {len(queue)}",
            f"Servis: {len([c for c in clients if c.finished])}", 
            "Appuyer sur R pour relancer la simulation",
            "Appuyer sur T pour tester automatiquement"
        ]
        for i, line in enumerate(info_lines):
            win.blit(font.render(line, True, BLACK), (20, 20 + i * 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    n_agents += 1
                    agents.append(Agent(n_agents - 1))
                elif event.key == pygame.K_DOWN and n_agents > 1:
                    n_agents -= 1
                    agents.pop()
                elif event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_t:
                    test_multiple_agents()
                    return False

        # --- ARRIVÉE PROGRESSIVE DES CLIENTS ---
        # On ajoute un client à la file QUE si son temps d'arrivée est atteint
        if current_client_index < MAX_CLIENTS and current_time >= clients[current_client_index].arrival_time:
            # On positionne le client dans la file (en fonction de la taille de la file)
            clients[current_client_index].target_x = 300 - len(queue) * 20  # Décalage horizontal pour chaque client
            clients[current_client_index].target_y = 500
            queue.append(clients[current_client_index])
            current_client_index += 1

        # --- ATTRIBUTION DES CLIENTS AUX AGENTS ---
        for agent in agents:
            # client_out = queue.pop(0)
            if not agent.busy and queue:
                next_client = queue.pop(0)
                next_client.in_service = True
                next_client.start_service_time = current_time
                next_client.end_service_time = current_time + next_client.service_time
                next_client.target_x = agent.x + 30
                next_client.target_y = agent.y + 60
                agent.client = next_client
                time.sleep(2)
                agent.busy = True
                stats_wait_times.append(next_client.start_service_time - next_client.arrival_time)

            elif agent.busy:
                if current_time >= agent.client.end_service_time:
                    agent.busy = False
                    agent.client.finished = True
                    agent.client = None

        # --- AFFICHAGE DES CLIENTS DANS LA FILE ---
        # On ne dessine que les clients présents dans la file (queue)
        for idx, client in enumerate(queue):
            # On met à jour la position pour bien aligner les clients dans la file
            client.target_x = 300 - idx * 30
            client.target_y = 500
            client.update_position()
            client.draw(win)

        # --- AFFICHAGE DES CLIENTS EN SERVICE ---
        # On dessine les clients qui sont en service (chez un agent)
        for agent in agents:
            if agent.busy and agent.client:
                agent.client.update_position()
                agent.client.draw(win)

        # --- AFFICHAGE DES AGENTS ---
        for agent in agents:
            agent.draw(win)

        if stats_wait_times:
            wait_time_over_time.append(np.mean(stats_wait_times))
            
        pygame.display.update()

        if (current_client_index >= MAX_CLIENTS and all(c.finished for c in clients)) or current_time >= Temps_simulation:
            running = False
            
    if stats_wait_times:
        moyenne = np.mean(stats_wait_times)
        plus_1_min = np.mean([t > 5 for t in stats_wait_times]) * 100
        print("\n--- Résultats ---")
        print(f"Temps d'attente moyen : {moyenne:.2f} s")
        print(f"% ayant attendu > 5 s : {plus_1_min:.1f}%")

        plt.figure(figsize=(10, 4))
        plt.plot(wait_time_over_time)
        plt.title("Évolution du temps d'attente moyen")
        plt.xlabel("Itérations")
        plt.ylabel("Temps d'attente (s)")
        plt.grid(True)
        plt.show()

    return False



def test_multiple_agents():
    results = []
    for agents in range(1, 10):
        wait_times = []
        for _ in range(5):
            clients = generate_clients(ARRIVAL_RATE_NORMAL, SERVICE_RATE, MAX_CLIENTS)
            queue = []
            agent_list = [None] * agents
            current_time = 0
            next_arrival_index = 0

            while next_arrival_index < MAX_CLIENTS or any(agent_list):
                while next_arrival_index < MAX_CLIENTS and clients[next_arrival_index].arrival_time <= current_time:
                    queue.append(clients[next_arrival_index])
                    next_arrival_index += 1

                for i in range(agents):
                    if not agent_list[i] and queue:
                        c = queue.pop(0)
                        c.start_service_time = current_time
                        c.end_service_time = current_time + c.service_time
                        agent_list[i] = c
                        wait_times.append(c.start_service_time - c.arrival_time)
                    elif agent_list[i] and current_time >= agent_list[i].end_service_time:
                        agent_list[i] = None

                current_time += 1

        results.append(np.mean(wait_times))

    plt.figure(figsize=(8, 5))
    plt.plot(range(1, 10), results, marker='o')
    plt.title("Temps d'attente moyen selon le nombre d'agents")
    plt.xlabel("Nombre d'agents")
    plt.ylabel("Temps d'attente moyen (s)")
    plt.grid(True)
    plt.show()
    
    
# Boucle de redémarrage
while True:
    relancer = run_simulation()
    if not relancer:
        break

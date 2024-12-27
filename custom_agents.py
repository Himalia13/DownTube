import random

def load_user_agents(file_path):
    """Carga una lista de User-Agents desde un archivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            user_agents = [line.strip() for line in f if line.strip()]
        return user_agents
    except Exception as e:
        return []

def get_random_headers(file_path='user_agents.txt'):
    """Genera headers aleatorios pero realistas"""
    user_agents = load_user_agents(file_path)
    user_agent = random.choice(user_agents)
    
    # Lista de idiomas comunes
    languages = [
        'es-ES,es;q=0.9,en;q=0.8',
        'en-US,en;q=0.9,es;q=0.8',
        'en-GB,en;q=0.9,es;q=0.8',
        'fr-FR,fr;q=0.9,en;q=0.8',
        'de-DE,de;q=0.9,en;q=0.8'
    ]

    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': random.choice(languages),
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'Pragma': 'no-cache'
    }
    
    return headers
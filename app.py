from flask import Flask, render_template, request, Response
import instaloader
import requests
import time
import random

app = Flask(__name__)

# Função para fazer login no Instagram
def login_instagram(username, password):
    L = instaloader.Instaloader()
    try:
        L.login(username, password)
        return L, "Login realizado com sucesso!"
    except instaloader.exceptions.InstaloaderException as e:
        return None, f"Falha no login: {e}"

# Função para obter seguidores e seguidos
def get_followers_and_followees(L, username):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        followers = list(profile.get_followers())
        followees = list(profile.get_followees())
        return followers, followees
    except instaloader.exceptions.InstaloaderException as e:
        return [], []

# Função para encontrar usuários que você segue, mas que não te seguem de volta
def find_non_followers(followers, followees):
    follower_usernames = {follower.username for follower in followers}
    non_followers = [followee for followee in followees if followee.username not in follower_usernames]
    return non_followers

# Função para deixar de seguir usuários que não te seguem de volta
def unfollow_non_followers(L, non_followers, limit=15):
    session = requests.Session()
    
    # Definindo o User-Agent para simular um iPhone
    MOBILE_USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
    cookies = {cookie.name: cookie.value for cookie in L.context._session.cookies}

    # Atualize os cabeçalhos para simular um dispositivo móvel
    session.headers.update({
        'User-Agent': MOBILE_USER_AGENT,
        'Referer': 'https://www.instagram.com/',
        'x-csrftoken': cookies['csrftoken'],
        'Origin': 'https://www.instagram.com',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    })
    session.cookies.update(cookies)

    # Configurando o proxy
    proxy = {
        'http': 'http://93.171.164.251:8080',
        'https': 'http://93.171.164.251:8080',
    }
    
    session.proxies.update(proxy)  # Adicionando o proxy à sessão

    count = 0
    unfollowed_users = []
    for user in non_followers:
        if count >= limit:
            break
        try:
            response = session.post(f'https://www.instagram.com/web/friendships/{user.userid}/unfollow/')
            if response.status_code == 200:
                unfollowed_users.append(user.username)
                count += 1
                time.sleep(random.uniform(3, 6))  # Delay aleatório para simular comportamento humano
            else:
                print(f"Erro ao deixar de seguir {user.username}: {response.status_code}")
        except Exception as e:
            print(f"Erro ao deixar de seguir {user.username}: {e}")

    return unfollowed_users

# Função para enviar atualizações de status para o frontend
def generate_status_updates(username, password, limit):
    yield f"data: Entrando no perfil de {username}...\n\n"
    
    # Fazer login no Instagram
    L, message = login_instagram(username, password)
    if not L:
        yield f"data: {message}\n\n"
        return

    yield "data: Capturando número de seguidores e seguidos...\n\n"
    
    # Obter seguidores e seguidos
    followers, followees = get_followers_and_followees(L, username)
    if not followers or not followees:
        yield "data: Falha ao capturar seguidores ou seguidos.\n\n"
        return

    yield f"data: Número de seguidores: {len(followers)}, seguidos: {len(followees)}\n\n"

    # Encontrar quem não te segue de volta
    non_followers = find_non_followers(followers, followees)
    yield f"data: Encontrados {len(non_followers)} usuários que não te seguem de volta.\n\n"

    # Deixar de seguir os não seguidores
    unfollowed_users = unfollow_non_followers(L, non_followers, limit)
    yield f"data: Processo concluído! Você deixou de seguir {len(unfollowed_users)} usuários.\n\n"
    
    for user in unfollowed_users:
        yield f"data: Deixou de seguir {user}.\n\n"
    
    yield "data: Fim do processo.\n\n"

# Endpoint para enviar status em tempo real
@app.route('/status')
def status():
    username = request.args.get('username')
    password = request.args.get('password')
    limit = int(request.args.get('limit', 15))

    return Response(generate_status_updates(username, password, limit), content_type='text/event-stream')

# Página inicial
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

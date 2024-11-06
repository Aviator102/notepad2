from flask import Flask, render_template_string, request, jsonify
import psycopg2
from psycopg2 import sql

app = Flask(__name__)

# URL de conexão com o banco de dados PostgreSQL
DATABASE_URL = "postgres://default:qKhdIMjs9xi3@ep-square-fog-a4qzqbtz.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require"

# Função para obter a conexão com o banco de dados PostgreSQL
def get_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Função para inicializar o banco de dados, caso ainda não exista
def init_db():
    conn = get_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notepads (
                username TEXT PRIMARY KEY,
                content TEXT
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

# Página principal (formulário para criar bloco de notas)
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="apple-mobile-web-app-title" content="Notepad Online">
        <meta name="theme-color" content="#ffffff">
        <meta name="description" content="Ferramenta de Notepad Online. Salve seu texto na nuvem e o utilize em qualquer lugar ou plataforma com este bloco de notas online.">
        <meta property="og:title" content="Notepad Online">
        <title>Notepad Online</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                color: #333;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            h1 {
                font-size: 2em;
                margin-bottom: 1em;
                color: #4CAF50;
            }
            .container {
                text-align: center;
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 600px;
            }
            input {
                padding: 10px;
                font-size: 1em;
                border: 1px solid #ddd;
                border-radius: 5px;
                width: 100%;
                box-sizing: border-box;
            }
            button {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 1em;
                cursor: pointer;
                border-radius: 5px;
                margin-top: 10px;
            }
            button:hover {
                background-color: #45a049;
            }
            #alerta {
                margin-top: 10px;
                color: red;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Notepad Online</h1>
            <label for="slug">Escolha um nome de usuário:</label>
            <input type="text" id="slug" placeholder="Nome de usuário" />
            <button onclick="createNotepad()">OK</button>
            <div id="alerta"></div>
        </div>
        <script>
            function createNotepad() {
                var username = document.getElementById('slug').value;
                if (!username) {
                    alert('Por favor, insira um nome de usuário');
                    return;
                }
                
                fetch('/create_notepad', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: username})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status == 'ok') {
                        window.location.href = '/edit/' + username;
                    } else {
                        document.getElementById('alerta').textContent = data.status;
                    }
                });
            }
        </script>
    </body>
    </html>
    """)

# Rota para criar o bloco de notas
@app.route('/create_notepad', methods=['POST'])
def create_notepad():
    data = request.get_json()
    username = data.get('username')

    conn = get_db()
    if conn:
        cursor = conn.cursor()
        
        # Verificar se o nome de usuário já existe
        cursor.execute('SELECT * FROM notepads WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "Nome de usuário já existe"})

        # Criar o bloco de notas com conteúdo vazio
        cursor.execute('INSERT INTO notepads (username, content) VALUES (%s, %s)', (username, ''))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "Erro ao conectar ao banco de dados"})


# Página de edição do bloco de notas
@app.route('/edit/<username>', methods=['GET', 'POST'])
def edit_notepad(username):
    conn = get_db()

    if request.method == 'POST':
        # Recebe o conteúdo do bloco de notas e salva no banco de dados
        content = request.form['content']
        
        if not conn:
            return "Erro ao conectar ao banco de dados", 500
        
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE notepads SET content = %s WHERE username = %s', (content, username))
            conn.commit()
            cursor.close()
            return render_template_string("""
            <h1>Notepad - {{ username }}</h1>
            <form method="POST">
                <textarea name="content" rows="10" cols="50">{{ content }}</textarea><br><br>
                <button type="submit">Salvar</button>
            </form>
            <div style="color: green;">Conteúdo salvo com sucesso!</div>
            """, username=username, content=content)
        except Exception as e:
            cursor.close()
            conn.close()
            return f"Erro ao salvar: {e}", 500

    # Carregar o conteúdo atual do bloco de notas
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM notepads WHERE username = %s', (username,))
        row = cursor.fetchone()
        if row:
            content = row[0]
        else:
            content = ''
        cursor.close()
        conn.close()

        return render_template_string("""
        <h1>Notepad - {{ username }}</h1>
        <form method="POST">
            <textarea name="content" style="width: 100%; height: 400px; font-size: 16px; padding: 10px;" placeholder="Escreva seu conteúdo aqui...">{{ content }}</textarea><br><br>
            <button type="submit">Salvar</button>
        </form>
        <br>
        <a href="/">Criar novo bloco de notas</a>
        """, username=username, content=content)
    else:
        return "Erro ao conectar ao banco de dados", 500

# Inicializar o banco de dados ao iniciar a aplicação
init_db()

# Iniciar o servidor
if __name__ == '__main__':
    app.run(debug=True)

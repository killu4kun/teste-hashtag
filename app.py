from flask import Flask, request,jsonify
import json
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Conexão com o banco de dados PostgreSQL
conn = psycopg2.connect(
    host="drona.db.elephantsql.com",
    database="osvgxikl",
    user="osvgxikl",
    password="sdw0eNRVRDr4QWt0hpYK5X4ucIvabZPr"
)


# Rota para receber os webhooks de pagamento
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()  # Obtém os dados do webhook
    
    print(data)

    # Registra o webhook recebido no banco de dados
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO webhooks (payload) VALUES (jsonb_build_object('payload', %s))",
        (str(data),)
    )
    conn.commit()
    cursor.close()

    # Obtém os dados relevantes do webhook
    status = data.get('status')
    email = data.get('email')

    # Verifica o status do pagamento e realiza as tratativas apropriadas
    if status == 'aprovado':
        print(f"Liberar acesso do e-mail: {email}")
        print(f"Enviar mensagem de boas vindas para o e-mail: {email}")
        # Registra a tratativa no banco de dados
        register_treatment('liberar acesso', email)
        register_treatment('enviar mensagem de boas vindas', email)
    elif status == 'recusado':
        print(f"Enviar mensagem de pagamento recusado para o e-mail: {email}")
        # Registra a tratativa no banco de dados
        register_treatment('enviar mensagem de pagamento recusado', email)
    elif status == 'reembolsado':
        print(f"Remover acesso do e-mail: {email}")
        # Registra a tratativa no banco de dados
        register_treatment('remover acesso', email)

    socketio.emit('webhook', data , broadcast=True)
    
    return 'Webhook received'

# Função para registrar as tratativas no banco de dados
def register_treatment(action, email):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tratativas (acao, cliente_email) VALUES (%s, %s)",
        (action, email)
    )
    conn.commit()
    cursor.close()

# Rota para visualizar os registros de webhooks e tratativas
@app.route('/webhooks', methods=['GET'])
def view_webhooks():
    cursor = conn.cursor()
    cursor.execute("SELECT payload FROM webhooks")
    webhooks = cursor.fetchall()
    cursor.close()
    return str(webhooks)

@app.route('/api/webhooks', methods=['GET'])
def get_webhooks():
    # Consulte o banco de dados para obter todos os webhooks
    cursor = conn.cursor()
    cursor.execute("SELECT payload->'payload' FROM webhooks")
    rows = cursor.fetchall()
    cursor.close()

    # Transforme os resultados em uma lista de dicionários
    webhook_data = []
    for row in rows:
        payload = json.loads(row[0].replace("'", "\""))  # Substitui as aspas simples por aspas duplas
        webhook_dict = {
            'nome': payload.get('nome'),
            'email': payload.get('email'),
            'status': payload.get('status'),
            'valor': str(payload.get('valor')),  # Converta para string
            'forma_pagamento': payload.get('forma_pagamento'),
            'parcelas': payload.get('parcelas')
        }
        webhook_data.append(webhook_dict)

    # Retorne os dados como uma resposta JSON
    return jsonify(webhook_data), 200


# Rota para pesquisar tratativas de um usuário específico
@app.route('/user/<email>', methods=['GET'])
def view_user(email):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT acao FROM tratativas WHERE cliente_email = %s",
        (email,)
    )
    user_treatments = cursor.fetchall()
    cursor.close()
    return str(user_treatments)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()  # Obtém os dados do formulário de login
    email = data.get('email')
    senha = data.get('senha')

    # Verifica se o usuário existe no banco de dados
    if not is_user_registered(email):
        return jsonify({'message': 'Usuário não encontrado'}), 404

    # Obtém os dados do usuário
    user = get_user(email)

    # Verifica se os dados de e-mail e senha estão corretos
    if user['senha'] != senha:
        return jsonify({'message': 'Credenciais inválidas'}), 401

    # Verifica se o token é válido
    if user['token'] != 'uhdfaAADF123':
        return jsonify({'message': 'Token inválido'}), 401

    # Usuário válido, realizar o login
    return jsonify({'message': 'Login bem-sucedido','status':'200'})

# Função para obter os dados do usuário pelo e-mail
def get_user(email):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()
    cursor.close()

    # Transforma os dados do usuário em um dicionário
    user_data = {
        'email': user[1],
        'senha': user[2],
        'token': user[3]
    }

    return user_data

# Função para verificar se o token é válido
def is_valid_token(token):
    # Implemente sua lógica para validar o token
    # Por exemplo, você pode comparar o token recebido com um valor fixo
    # ou consultar o banco de dados para verificar se o token é válido  
    return token == 'uhdfaAADF123'

# Função para verificar se as informações de login são válidas no banco de dados
def is_valid_user(email, senha):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = %s AND senha = %s",
        (email, senha)
    )
    user = cursor.fetchone()
    cursor.close()
    return user is not None

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()  # Obtém os dados do formulário de cadastro
    email = data.get('email')
    senha = data.get('senha')
    token = data.get('token')


    # Verifica se o usuário já está cadastrado
    if is_user_registered(email):
        return jsonify({'message': 'Usuário já cadastrado',"status":'400'}), 400

    # Insere o novo usuário no banco de dados
    insert_user(email, senha,token)

    # Retorna uma mensagem de sucesso
    return jsonify({'message': 'Usuário cadastrado com sucesso'})

# Função para verificar se o usuário já está cadastrado
def is_user_registered(email):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()
    cursor.close()
    return user is not None

# Função para inserir um novo usuário no banco de dados
def insert_user(email, senha, token):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (email, senha, token) VALUES (%s, %s, %s)",
        (email, senha, token)
    )
    conn.commit()
    cursor.close()
    
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado ao WebSocket')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado do WebSocket')    

if __name__ == '__main__':
    socketio.run()

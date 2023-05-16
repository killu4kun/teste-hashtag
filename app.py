from flask import Flask, request
import psycopg2

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run()

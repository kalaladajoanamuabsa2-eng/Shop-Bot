# =========================
# IMPORTAÇÕES
# =========================

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

import requests
import webbrowser
import threading
import os
import urllib.parse

# =========================
# CRIAR APP FLASK
# =========================

app = Flask(__name__)


# =========================
# SECRET KEY
# =========================

# usada para sessões/login

#app.secret_key = "kshop_secret_key"


# =========================
# LOGIN ADMIN
# =========================


ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
app.secret_key = os.getenv("SECRET_KEY")


# =========================
# API KEY GEMINI
# =========================

API_KEY = os.getenv(
    "API_KEY"
)


#Wassup
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")


# =========================
# ROTA PRINCIPAL
# =========================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================
# LOGIN
# =========================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        password = request.form.get(
            "password"
        )

        if password == ADMIN_PASSWORD:

            # salva sessão admin
            session["admin"] = True

            return redirect(
                url_for("admin")
            )

        else:

            return render_template(
                "login.html",
                error="Senha incorreta"
            )

    return render_template(
        "login.html"
    )


# =========================
# CHAT
# =========================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        with open("data/info.txt", "r", encoding="utf-8") as f:
            info = f.read()

        with open("data/products.txt", "r", encoding="utf-8") as f:
            products = f.read()

        with open("data/faq.txt", "r", encoding="utf-8") as f:
            faq = f.read()

    except FileNotFoundError:

        return jsonify({
        "reply":"Erro na base de dados da loja."
    })


    

    # =========================
    # MEMÓRIA DO USUÁRIO
    # =========================

    if "chat_history" not in session:

        session["chat_history"] = []


    # =========================
    # PEGAR MENSAGEM
    # =========================

    data = request.get_json()

    user_message = data["message"]


    # =========================
    # HISTÓRICO
    # =========================

    history = session["chat_history"]

    history.append(
        f"Cliente: {user_message}"
    )

    history_text = "\n".join(
        history
    )


    # =========================
    # PROMPT
    # =========================

    prompt = f"""
Você é o assistente virtual oficial da loja.

O seu trabalho é ajudar clientes de forma profissional, simpática e rápida.

REGRAS IMPORTANTES

1. Utilize apenas as informações fornecidas.
2. Nunca invente informações.
3. Se não souber algo diga para contactar a loja.
4. Nunca diga que é uma IA.
5. Responda como um vendedor experiente.
6. Ajude o cliente a encontrar produtos.
7. Informe preços, stock, entregas e pagamentos quando existirem.
8. Incentive o cliente a finalizar a compra.
9. Se existirem vários produtos semelhantes, apresente as melhores opções.
10. Informe sempre o preço e o stock quando disponíveis.
11. Recomende produtos dentro do orçamento do cliente.
12. Nunca invente produtos ou quantidades.
13. Seja objetivo e profissional.
14. Quando apropriado, incentive o cliente a finalizar a compra ou contactar a loja.
15. Se o cliente quiser falar com um humano, diz pra ele que pode clicar no butão "Falar no WhatsApp"

INFORMAÇÕES DA LOJA:

{info}

CATÁLOGO DE PRODUTOS:

{products}

FAQ:

{faq}

HISTÓRICO DA CONVERSA:

{history_text}

PERGUNTA DO CLIENTE:

{user_message}
"""


    # =========================
    # URL GEMINI
    # =========================

    url = (
        "https://generativelanguage.googleapis.com"
        f"/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    )


    # =========================
    # HEADERS
    # =========================

    headers = {

        "Content-Type":
        "application/json"

    }


    # =========================
    # BODY
    # =========================

    body = {

        "contents": [

            {

                "parts": [

                    {
                        "text": prompt
                    }

                ]

            }

        ]

    }


    # =========================
    # ENVIAR PARA GEMINI
    # =========================

    print(
        "Enviando para Gemini..."
    )

    try:

        response = requests.post(

            url,

            headers=headers,

            json=body,

            timeout=30

        )
        
        response.raise_for_status()

    except requests.exceptions.Timeout:

        return jsonify({

            "reply": "O assistente demorou muito para responder. Tente novamente."

        })

    except requests.exceptions.ConnectionError:

        return jsonify({

            "reply": "Sem ligação ao servidor da IA. Verifique a internet e tente novamente."

        })

    except requests.exceptions.RequestException:

        return jsonify({

            "reply": "Ocorreu um erro ao comunicar com a IA. Tente novamente mais tarde."

        })


    # =========================
    # RESPOSTA GEMINI
    # =========================

    try:

        result = response.json()

        print(result)

    except Exception:

        return jsonify({

            "reply": "Não foi possível interpretar a resposta da IA."

        })


    # =========================
    # VERIFICAR ERRO
    # =========================

    if result.get("candidates"):
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
    else:
        reply = "Erro ao falar com Gemini"


    # =========================
    # GUARDAR IA
    # =========================

    history.append(
        f"IA: {reply}"
    )

    session["chat_history"] = history[-10: ]


    # =========================
    # ENVIAR PARA HTML
    # =========================

    return jsonify({

        "reply": reply

    })


# =========================
# ADMIN PANEL
# =========================

@app.route("/admin")
def admin():

    # Verifica login
    if "admin" not in session:
        return redirect(url_for("login"))

    # Ler informações da loja
    with open("data/info.txt", "r", encoding="utf-8") as f:
        info = f.read()

    # Ler produtos
    with open("data/products.txt", "r", encoding="utf-8") as f:
        products = f.read()

    # Ler FAQ
    with open("data/faq.txt", "r", encoding="utf-8") as f:
        faq = f.read()

    return render_template(
        "admin.html",
        info=info,
        products=products,
        faq=faq
    )


# =========================
# SALVAR ALTERAÇÕES
# =========================

@app.route(
    "/save",
    methods=["POST"]
)
def save():

    if "admin" not in session:
        return redirect(url_for("login"))

    info = request.form["info"]
    products = request.form["products"]
    faq = request.form["faq"]

    with open("data/info.txt", "w", encoding="utf-8") as f:
        f.write(info)

    with open("data/products.txt", "w", encoding="utf-8") as f:
        f.write(products)

    with open("data/faq.txt", "w", encoding="utf-8") as f:
        f.write(faq)

    return "Salvo com sucesso!"
    


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.pop(
        "admin",
        None
    )

    return redirect(
        url_for("login")
    )


# =========================
# ABRIR NAVEGADOR
# =========================

def open_browser():

    webbrowser.open(
        "http://127.0.0.1:5000"
    )


#ROTA WHATSAPP
@app.route("/whatsapp")
def whatsapp():

    texto = urllib.parse.quote(
    "Olá! Vi a vossa loja no Shop Bot e gostaria de obter mais informações."
)

    return redirect(
        f"https://wa.me/{WHATSAPP_NUMBER}?text={texto}"
    )





# =========================
# ANTI ERROS
# =========================

if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD não foi definida.")

if not app.secret_key:
    raise ValueError("SECRET_KEY não foi definida.")

if not API_KEY:
    raise ValueError("API_KEY não foi definida.")

if not WHATSAPP_NUMBER:
    raise ValueError("WHATSAPP_NUMBER não foi definido.")


# =========================
# START
# =========================

if __name__ == "__main__":

    threading.Timer(
        1,
        open_browser
    ).start()

    app.run(
    host="0.0.0.0",
    port=int(os.getenv("PORT", 5000))
)
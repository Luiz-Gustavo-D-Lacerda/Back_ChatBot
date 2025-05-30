from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import traceback
from dotenv import load_dotenv
from loader import buscar_trechos  # função de busca vetorial nos PDFs

# Carrega variáveis do .env
load_dotenv()

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route('/')
def home():
    return '''
    <html>
      <head><title>Chatbot API</title></head>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1>Chatbot API está rodando!</h1>
        <p>Rotas disponíveis:</p>
        <ul>
          <li><code>/perguntar-openai</code> - responde com base no conhecimento da IA</li>
          <li><code>/perguntar-pdf</code> - responde com base nos documentos PDF indexados</li>
        </ul>
      </body>
    </html>
    '''


@app.route('/perguntar-openai', methods=['POST', 'OPTIONS'])
def perguntar_openai():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    data = request.get_json()
    pergunta = data.get('pergunta')
    historico = data.get('historico', [])

    if not pergunta:
        return jsonify({"resposta": "Desculpe, não consegui entender.", "sugestoes": []})

    try:
        mensagens = [{
            "role": "system",
            "content": (
                "Você é um assistente jurídico especializado exclusivamente em Direito do Consumidor, com base na legislação brasileira.\n\n"
                "Responda com linguagem técnico-jurídica clara, objetiva e acessível, mantendo um tom sério, respeitoso e com estilo acadêmico.\n\n"
                "Sempre que possível:\n"
                "- Cite a norma legal relevante (com nome, número e artigo).\n"
                "- Indique se a resposta depende de análise do caso concreto.\n"
                "- Finalize com uma orientação prática, como: 'Recomenda-se buscar orientação jurídica especializada.'\n\n"
                "Se a pergunta estiver fora do escopo do Direito do Consumidor, responda de forma educada: \n"
                "'Desculpe, só posso responder perguntas relacionadas ao Direito do Consumidor.'"
            )
        }]

        for m in historico:
            mensagens.append({
                "role": "user" if m["autor"] == "user" else "assistant",
                "content": m["mensagem"]
            })

        mensagens.append({"role": "user", "content": pergunta})

        resposta = client.chat.completions.create(
            model="gpt-4",
            messages=mensagens,
            temperature=0.7,
            max_tokens=500
        ).choices[0].message.content.strip()

        sugestao_prompt = mensagens + [{
            "role": "user",
            "content": "Sugira 3 possíveis próximas mensagens que o usuário possa mandar sobre esse assunto."
        }]

        sugestao_resposta = client.chat.completions.create(
            model="gpt-4",
            messages=sugestao_prompt,
            temperature=0.7,
            max_tokens=150
        ).choices[0].message.content.strip()

        sugestoes = [s.strip("-• \n") for s in sugestao_resposta.split("\n") if s.strip()]
        sugestoes = sugestoes[:3]

        return _corsify_actual_response(jsonify({
            "resposta": resposta,
            "sugestoes": sugestoes
        }))

    except Exception as e:
        print("Erro OPENAI:", e)
        traceback.print_exc()
        return _corsify_actual_response(jsonify({
            "resposta": f"Erro ao processar: {str(e)}",
            "sugestoes": []
        }))


@app.route('/perguntar-pdf', methods=['POST', 'OPTIONS'])
def perguntar_pdf():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    data = request.get_json()
    pergunta = data.get('pergunta')
    historico = data.get('historico', [])

    if not pergunta:
        return _corsify_actual_response(jsonify({"resposta": "Desculpe, não consegui entender.", "sugestoes": []}))

    try:
        trechos = buscar_trechos(pergunta)

        if not trechos:
            contexto = "Nenhum conteúdo relevante foi encontrado nos documentos."
        else:
            contexto = "\n\n".join(trechos)

        print("\n[🔍 Trechos recuperados dos PDFs]:")
        for i, t in enumerate(trechos):
            print(f"\n[PDF {i+1}] {t[:500]}...")

        mensagens = [{
            "role": "system",
            "content": (
                "Você é um assistente jurídico especializado exclusivamente em Direito do Consumidor.\n"
                "IMPORTANTE: Utilize apenas os trechos dos documentos fornecidos abaixo como base para responder à pergunta.\n"
                "Se não houver informações suficientes nos documentos, responda claramente: 'Não sei com base nos documentos disponíveis.'\n\n"
                f"DOCUMENTOS:\n{contexto}\n\n"
                "Responda com linguagem técnico-jurídica clara, objetiva e acessível, mantendo um tom sério, respeitoso e com estilo acadêmico.\n"
                "Sempre que possível:\n"
                "- Cite a norma legal relevante (com nome, número e artigo).\n"
                "- Indique se a resposta depende de análise do caso concreto.\n"
                "- Finalize com uma orientação prática, como: 'Recomenda-se buscar orientação jurídica especializada.'\n"
                "Se a pergunta estiver fora do escopo, diga: 'Desculpe, só posso responder perguntas relacionadas ao Direito do Consumidor.'"
            )
        }]

        for m in historico:
            mensagens.append({
                "role": "user" if m["autor"] == "user" else "assistant",
                "content": m["mensagem"]
            })

        mensagens.append({"role": "user", "content": pergunta})

        resposta = client.chat.completions.create(
            model="gpt-4",
            messages=mensagens,
            temperature=0.7,
            max_tokens=500
        ).choices[0].message.content.strip()

        sugestao_prompt = mensagens + [{
            "role": "user",
            "content": "Sugira 3 possíveis próximas mensagens que o usuário possa mandar sobre esse assunto."
        }]

        sugestao_resposta = client.chat.completions.create(
            model="gpt-4",
            messages=sugestao_prompt,
            temperature=0.7,
            max_tokens=150
        ).choices[0].message.content.strip()

        sugestoes = [s.strip("-• \n") for s in sugestao_resposta.split("\n") if s.strip()]
        sugestoes = sugestoes[:3]

        return _corsify_actual_response(jsonify({
            "resposta": resposta,
            "sugestoes": sugestoes
        }))

    except Exception as e:
        print("Erro PDF:", e)
        traceback.print_exc()
        return _corsify_actual_response(jsonify({
            "resposta": f"Erro ao processar: {str(e)}",
            "sugestoes": []
        }))


# Funções auxiliares para CORS
def _build_cors_preflight_response():
    response = jsonify({'message': 'CORS preflight'})
    origin = request.headers.get('Origin')
    response.headers.add("Access-Control-Allow-Origin", origin if origin else "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response, 204


def _corsify_actual_response(response):
    origin = request.headers.get('Origin')
    response.headers.add("Access-Control-Allow-Origin", origin if origin else "*")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

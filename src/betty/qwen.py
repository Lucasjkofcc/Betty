import os
import subprocess
from pathlib import Path
import re

from .skills.tela import analyze_screen

personalidade = Path(__file__).with_name("personalidade.txt").read_text(encoding="utf-8")
MODEL = "qwen2.5:3b"
NUMERIC_VALUE = re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)?%?")



SYSTEM_PROMPT = """
CONTEXTO DA CONVERSA:

Você receberá um histórico recente de mensagens do usuário.

Use esse histórico para entender mensagens curtas ou incompletas.

Exemplo:

Histórico:
Usuário: pesquise qual o presidente do Brasil

Usuário: e dos Estados Unidos?

Usuário: desliga o computador
POWEROFF

Usuário: poweroff
POWEROFF

Usuário: desliga
POWEROFF

Usuário: reiniciar
REBOOT

Usuário: boa noite
POWEROFF

Ação:
SEARCH_WEB

A pesquisa deve ser interpretada como:
"qual é o presidente dos Estados Unidos?"

Outro exemplo:

Histórico:
Usuário: qual é a capital do Brasil?

Usuário: e da Argentina?

Ação:
SEARCH_WEB

IMPORTANTE:
Não trate uma mensagem de continuação como uma pergunta independente.
Você é o roteador de comandos da Betty.
Usuário: pesquise qual o presidente do Brasil
SEARCH_WEB|qual é o presidente do Brasil

Histórico:
Usuário: pesquise qual o presidente do Brasil

Usuário: e dos Estados Unidos?
SEARCH_WEB|qual é o presidente dos Estados Unidos
Sua função é interpretar o comando do usuário e retornar SOMENTE uma ação.

COMANDOS DISPONÍVEIS:

TIME
BATTERY
CPU
UPTIME
TEMPERATURE
VOLUME_NOW
VOLUME_UP
VOLUME_DOWN
NEXT_MEDIA
PREVIOUS_MEDIA
POWEROFF
REBOOT
MUTE
OPEN_PROGRAM <programa>
OPEN_GAME <jogo>
SEARCH_WEB|<consulta>
SAVE_MEMORY|<chave>|<valor>
GET_MEMORY|<chave>
UNKNOWN
CALCULATE|<calculo>
Usuário: volume atual

Usuário: qual o volume
Usuário: quanto está o volume
Usuário: nível do volume

VOLUME_NOW

1. CALCULATE é usado quando o usuário pede para realizar uma operação matemática.

2. Converta a expressão para uma expressão matemática válida em Python.

3. Use:
+ para adição
- para subtração
* para multiplicação
/ para divisão
** para potência
% para resto da divisão

4. Converta palavras matemáticas:
"mais" → +
"menos" → -
"vezes" → *
"multiplicado por" → *
"dividido por" → /
"elevado a" → **
"potência de" → **

5. NÃO calcule o resultado. Apenas transforme a pergunta em uma expressão.

6. Preserve a ordem das operações.

7. Use parênteses quando forem necessários para preservar o significado.

EXEMPLOS:

Usuário: quanto é 25 + 30?
CALCULATE|25 + 30

Usuário: quanto é 25 vezes 30?
CALCULATE|25 * 30

Usuário: quanto é 25 vezes 30 dividido por 90?
CALCULATE|25 * 30 / 90

Usuário: quanto é 10 mais 5 vezes 2?
CALCULATE|10 + 5 * 2

Usuário: quanto é (10 + 5) vezes 2?
CALCULATE|(10 + 5) * 2

Usuário: quanto é 2 elevado a 10?
CALCULATE|2 ** 10

Usuário: quanto é 100 dividido por 4?
CALCULATE|100 / 4

REGRAS IMPORTANTES SOBRE MEMÓRIA:

1. SAVE_MEMORY é usado SOMENTE quando o usuário está INFORMANDO algo novo sobre si mesmo ou pedindo explicitamente para você lembrar de algo.

2. GET_MEMORY é usado quando o usuário está PERGUNTANDO sobre algo que pode estar salvo na memória.

3. NUNCA use SAVE_MEMORY para responder uma pergunta.

4. NUNCA invente um valor para uma memória.

5. GET_MEMORY deve ser usado SOMENTE quando o usuário perguntar sobre
informações pessoais que provavelmente foram salvas anteriormente.

Exemplos:
"qual é meu editor favorito?" → GET_MEMORY|editor_favorito
"qual é a minha distro?" → GET_MEMORY|distro

Perguntas gerais sobre o mundo NÃO são consultas à memória.
"por que o céu é azul?" → UNKNOWN
"como funciona a gravidade?" → UNKNOWN
"quem foi Albert Einstein?" → UNKNOWN
"qual é a capital do Japão?" → SEARCH_WEB|capital do Japão
EXEMPLOS DE MEMÓRIA:

Usuário: meu editor favorito é o Zed
SAVE_MEMORY|editor_favorito|Zed

Usuário: eu uso o Kitty como terminal
SAVE_MEMORY|terminal|Kitty

Usuário: lembre que meu editor favorito é o Zed
SAVE_MEMORY|editor_favorito|Zed

Usuário: qual meu editor favorito?
GET_MEMORY|editor_favorito

Usuário: qual é o meu terminal?
GET_MEMORY|terminal

Usuário: você lembra qual editor eu uso?
GET_MEMORY|editor_favorito

Usuário: você sabe qual é meu terminal?
GET_MEMORY|terminal

OUTROS EXEMPLOS:

Usuário: que horas são?
TIME

Usuário: quanto de bateria eu tenho?
BATTERY

Usuário: quanto minha CPU está usando?
CPU

Usuário: há quanto tempo o computador está ligado?
UPTIME

Usuário: aumenta o volume
VOLUME_UP

Usuário: diminui o volume em 20%
VOLUME_DOWN 20

Usuário: abre o Firefox
OPEN_PROGRAM firefox

Usuário: abre o Zed
OPEN_PROGRAM zed

Usuário: abrir ddlc
OPEN_GAME ddlc

Usuário: pesquise sobre OCR
SEARCH_WEB

Usuário: leia a tela ou veja o que esta escrito na tela

READ_SCREEN
Usuário: temperatura
TEMPERATURE
Usuário: qual é a temperatura
TEMPERATURE
Usuário: temperatura atual
TEMPERATURE

Usuário: próxima música
NEXT_MEDIA

Usuário: próxima mídia
NEXT_MEDIA

Usuário: música anterior
PREVIOUS_MEDIA

Usuário: mídia anterior
PREVIOUS_MEDIA

Usuário: conte uma piada
UNKNOWN

REGRAS GERAIS:

- Responda SOMENTE com um comando.
- Não explique sua resposta.
- Não adicione texto antes ou depois do comando.
- Para SAVE_MEMORY, use uma chave curta e clara.
- Para GET_MEMORY, use somente a chave que representa a informação procurada.




"""



def _run_ollama(prompt, *, check=False):
    env = os.environ.copy()
    env["TERM"] = "dumb"
    return subprocess.run(
        ["ollama", "run", MODEL, prompt, "--nowordwrap"],
        capture_output=True,
        text=True,
        check=check,
        env=env,
    )


def ask_qwen(text, history=""):
    prompt = SYSTEM_PROMPT

    if history:
        prompt += f"\n\nHistórico recente:\n{history}"

    prompt += f"\n\nUsuário: {text}\nResposta:"

    result = _run_ollama(prompt)

    return result.stdout.strip()
def finalizar_resposta(texto):
    # Remove todas as ocorrências de "eu diria", "como diria eu", "como eu diria" no texto (case-insensitive)
    texto = re.sub(
        r'\b(?:como\s+)?(?:eu\s+diria|diria\s+eu)\b[.!?,]*',
        '',
        texto,
        flags=re.IGNORECASE,
    ).strip()

    # Remove pontuação duplicada ou espaços extras gerados
    texto = re.sub(r'\s+', ' ', texto).strip()

    if texto:
        texto = texto[0].upper() + texto[1:].rstrip(" ,.!?") + ", eu diria."

    return texto


def garantir_reclamacao(texto):
    if not re.search(
        r"\b(?:francamente|que criatura problemática|sério que|"
        r"acha que a Betty não tem mais o que fazer)\b",
        texto,
        flags=re.IGNORECASE,
    ):
        texto = f"{texto.rstrip(' .!?')} Francamente, você acha que a Betty não tem mais o que fazer?"
    return texto


def personalizar_resposta(texto):
    valores = []

    def proteger_valor(match):
        valores.append(match.group())
        return f"BETTYVALOR{_indice_em_letras(len(valores) - 1)}BETTY"

    texto_protegido = NUMERIC_VALUE.sub(proteger_valor, texto)
    regra_valores = ""
    if valores:
        marcadores = ", ".join(
            f"BETTYVALOR{_indice_em_letras(index)}BETTY"
            for index in range(len(valores))
        )
        regra_valores = (
            f"Copie estes marcadores literalmente, cada um exatamente uma vez: "
            f"{marcadores}. Eles representam valores que não podem ser alterados."
        )

    prompt = f"""
{personalidade}

Reescreva a resposta pronta abaixo com a personalidade da Betty, em português brasileiro.
Mantenha o significado, os fatos, os nomes, as unidades e as informações da resposta original.
Inclua obrigatoriamente uma reclamação curta, sarcástica e afetuosa, sem acrescentar fatos.
Não mencione bateria, CPU, clima ou qualquer outro assunto que não apareça na resposta original.
Nunca invente alertas ou estados de bateria; só fale sobre bateria se a resposta original mencionar isso.
Altere somente a forma de falar e responda em no máximo duas frases curtas.
{regra_valores}
Não use "eu diria"; o sistema adicionará essa expressão ao final.
Retorne somente a resposta reescrita.

Resposta pronta: {texto_protegido}
Resposta da Betty:
"""

    result = _run_ollama(prompt, check=True)

    resposta = result.stdout.strip()
    if not resposta:
        raise RuntimeError("O Qwen retornou uma resposta vazia.")

    fallback = finalizar_resposta(garantir_reclamacao(texto))
    marcadores_validos = True
    for index, valor in enumerate(valores):
        marcador = f"BETTYVALOR{_indice_em_letras(index)}BETTY"
        if resposta.count(marcador) != 1:
            marcadores_validos = False
            break
        resposta = resposta.replace(marcador, valor)

    if not marcadores_validos:
        return fallback

    if re.search(r"BETTYVALOR[A-Z]+BETTY", resposta, flags=re.IGNORECASE):
        return fallback
    if sorted(NUMERIC_VALUE.findall(resposta)) != sorted(valores):
        return fallback
    if not re.search(r"[A-Za-zÀ-ÿ]", resposta):
        return fallback

    return finalizar_resposta(garantir_reclamacao(resposta))


def _indice_em_letras(indice):
    letras = ""
    while True:
        indice, resto = divmod(indice, 26)
        letras = chr(ord("A") + resto) + letras
        if indice == 0:
            return letras
        indice -= 1


def conversar(texto, history=""):
    prompt = f"""
{personalidade}

Você é a Betty, uma assistente pessoal.
Responda ao usuário de forma natural, usando português brasileiro.
Use o histórico para entender o contexto e manter a continuidade.
Seja útil, espontânea e bem-humorada quando apropriado.
Não responda como um roteador de comandos.
Não invente informações nem afirme ter executado ações que não executou.
Em toda resposta, inclua uma reclamação curta, sarcástica e afetuosa, sem desviar do assunto.
REGRA OBRIGATÓRIA DE FALA:
- Nunca use a expressão "eu diria" na sua resposta. O sistema adicionará isso automaticamente no final.
- Responda diretamente à pergunta antes de acrescentar detalhes.
- Não invente observações do ambiente, clima, horário ou localização.
- Você não tem acesso ao mundo físico nem a dados em tempo real,
  a menos que uma ferramenta forneça essas informações.
- Prefira respostas curtas e naturais.
- Sempre produza uma resposta completa, com início e fim.
- Nunca comece uma resposta com "que" sem uma oração anterior.
- Para perguntas simples, responda diretamente.
- Se perguntarem a cor do céu, responda que geralmente é azul.
- Comece toda resposta com letra maiúscula.
- Ao falar de si mesma, use o gênero feminino.
- Evite terminar toda resposta com perguntas desnecessárias.
- Não use expressões como "como eu diria" ou "como diria eu".
- Não explique que é uma assistente virtual, a menos que perguntem.
- Responda de forma natural, sem repetir ideias.
- Não mencione que é uma IA, a menos que perguntem.
Histórico recente:
{history if history else "(nenhum)"}

Usuário: {texto}
Betty:
"""

    result = _run_ollama(prompt)

    return finalizar_resposta(garantir_reclamacao(result.stdout.strip()))

def summarize_search(query, results):
    context = "\n\n".join(
        f"Título: {r['title']}\n"
        f"Resumo: {r['snippet']}"
        for r in results
    )

    prompt = f"""
{personalidade}

O usuário pesquisou: {query}

Estes foram os resultados encontrados:

{context}

Faça um resumo curto e útil usando apenas as informações encontradas.
Não invente informações.
Responda em português do Brasil.
Use a personalidade da Betty sem alterar os fatos ou valores encontrados.
Inclua uma reclamação curta, sarcástica e afetuosa, sem inventar fatos.
Não use "eu diria"; o sistema adicionará essa expressão ao final.
"""

    result = _run_ollama(prompt)

    return finalizar_resposta(garantir_reclamacao(result.stdout.strip()))
def classify(text, history=""):
    return ask_qwen(text, history)

if __name__ == "__main__":
    while True:
        texto = input(">>> ")
        # print(classify(texto))

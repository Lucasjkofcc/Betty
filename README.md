# Betty

Assistente virtual em Python para controle de sistema, voz, pesquisa, automação e interação com IA local via Ollama.

## Requisitos

- Python 3.14+
- uv
- Ollama
- Modelos instalados no Ollama:
  - `qwen2.5:3b`
  - `moondream:latest`

## Estrutura principal

- `src/betty/main.py` — orquestração principal da assistente
- `src/betty/qwen.py` — roteamento de comandos e respostas com Ollama
- `src/betty/memory.py` — memória persistente em JSON
- `src/betty/skills/` — funções de sistema, voz, mídia, tela e automação

## Funções da Betty

### 1. Monitoramento e segurança

- `facial_check()`
  - Detecta rostos com OpenCV
  - Se não houver rosto por 15 segundos, pausa todos os players e bloqueia a tela com `hyprlock`

- `monitor()`
  - Checa bateria e CPU periodicamente
  - Emite alertas via voz quando necessário

- `monitor_screen()`
  - Analisa a tela em intervalos aleatórios e responde com descrição do conteúdo

- Sistema de atenção (`skills/attention.py`)
  - Mantém estados de atenção e aumenta a irritação conforme o tempo sem interação
  - Escolhe aleatoriamente entre várias frases em cada nível: 5, 15 e 30 minutos; 1, 3, 6, 12 e 24 horas
  - Depois de 24 horas, continua falando a cada 3 horas com frases do nível máximo
  - Ao receber uma nova interação após 15 minutos, escolhe uma reação aleatória compatível com o tempo de ausência
  - Reclama progressivamente do uptime após 8, 12, 24, 36, 48 e 60 horas
  - Ao completar 3 dias de uptime, recomenda reiniciar o PC sem fazê-lo automaticamente
  - Da meia-noite às 3h59, reclama em níveis crescentes se detectar movimento recente do mouse
  - Entre 4h e 5h59, dá uma última fala de desistência e não repete durante a manhã
  - Adia as falas de atenção enquanto a Betty está falando ou executando uma tarefa
- Monitor de mouse (`skills/mouse_activity.py`)
  - `monitor_mouse_activity()` consulta a posição do cursor via `hyprctl`
  - `mouse_active_within()` considera o PC ativo se o mouse se moveu nos últimos 5 minutos

### 2. Interação com o usuário

- `responder(texto, *, personalizar=True, fala=None)`
  - Formata a resposta, personaliza o texto e fala em voz

- `processar_comando(comando)`
  - Interpreta texto do usuário, classifica a intenção e executa a ação correta

- `main()`
  - Loop principal, lendo comandos por teclado ou voz

- `run()`
  - Inicializa os monitores e mantém a Betty ativa

### 3. IA e classificação de comandos

- `classify(text, history="")`
  - Decide qual ação a Betty deve executar com base no comando e no histórico

- `conversar(texto, history="")`
  - Mantém conversa natural usando o modelo local

- `personalizar_resposta(texto)`
  - Ajusta a resposta para o estilo da Betty

- `summarize_search(query, results)`
  - Resumiza resultados de busca para resposta em voz/texto

- `_run_ollama(prompt, *, check=False)`
  - Executa o modelo Ollama local

- `ask_qwen(text, history="")`
  - Faz perguntas diretamente ao modelo

- `finalizar_resposta(texto)`
  - Finaliza e organiza resposta para o usuário

- `garantir_reclamacao(texto)`
  - Garante uma resposta no tom da Betty

- `_indice_em_letras(indice)`
  - Utilitário para conversão de índices em letras

### 4. Memória

- `load_memory()`
  - Carrega a memória salva em `memory.json`

- `save_memory(key, value)`
  - Salva informações pessoais do usuário para uso posterior

- `get_memory(key)`
  - Recupera um valor da memória

### 5. Sistema e hardware

- `get_time()`
  - Retorna a hora atual

- `battery_check()`
  - Verifica se a bateria está baixa ou em estado crítico

- `get_battery()`
  - Retorna o percentual da bateria

- `get_plugged()`
  - Informa se o dispositivo está conectado à energia

- `cpu_info()`
  - Dados do processador

- `cpu_check()`
  - Checklist rápido de uso da CPU

- `cpu_percent()`
  - Percentual atual de uso da CPU

- `cpu_freq()`
  - Frequência do processador

- `ram_percent()`
  - Uso de memória RAM

- `ram_info()`
  - Detalhes da memória RAM

- `disk_info()`
  - Informações de disco

- `temperatures()`
  - Temperaturas do sistema

- `uptime_info()`
  - Tempo desde o último boot

- `get_uptime_seconds()`
  - Retorna o uptime em segundos para verificações de duração

- `get_temperature()`
  - Temperatura atual do sistema

### 6. Áudio e voz

- `speak(texto)`
  - Converte texto em fala

- `listen(filename="input.wav", duration=5, fs=44100)`
  - Captura áudio por microfone e transforma em texto/entrada

- `audio_worker()`
  - Thread responsável por tocar a fila de áudio

- `clean_text(text)`
  - Limpa o texto antes de gerar fala

- `split_sentences(text)`
  - Divide o texto em frases para falas mais naturais

- `silence(seconds)`
  - Gera silêncio em áudio para encaixe de fala

- `generate_audio(text)`
  - Gera áudio a partir do texto

- `play_audio(file_path)`
  - Reproduz arquivo de áudio gerado

### 7. Volume, mídia e reprodução

- `volume_now()`
  - Retorna o volume atual

- `volume_up(amount=5)`
  - Aumenta o volume

- `volume_down(amount=5)`
  - Diminui o volume

- `mute()`
  - Silencia o sistema

- `pausar_midias()`
  - Pausa todos os players ativos

- `retomar_midias(players)`
  - Retoma reprodução dos players pausados

- `pausar_temporario()`
  - Pausa temporariamente a fala para não sobrepor áudio

- `retomar_temporario()`
  - Retoma a reprodução de áudio após pausa temporária

- `musica(comando)`
  - Comandos simples para controle de mídia via `playerctl`
  - Ações: `proxima`, `anterior`, `pausar`, `continuar`

### 8. Programas, jogos e desktop

- `open_program(program)`
  - Abre um programa ou aplicativo

- `open_steam_game(game)`
  - Abre um jogo pela Steam

- `poweroff()`
  - Desliga o computador

- `reboot()`
  - Reinicia o computador

### 9. Pesquisa na web

- `search_web(query: str, max_results: int = 5)`
  - Pesquisa na web via DuckDuckGo
  - Retorna título, URL e snippet dos resultados

### 10. Tela e OCR

- `screenshot()`
  - Captura a tela

- `ocr()`
  - Extrai texto da imagem da tela

- `analyze_screen()`
  - Analisa o conteúdo da tela, útil para descrição contextual da interface

- `ler_arquivo(caminho)`
  - Lê conteúdo de um arquivo

- `escrever_arquivo(caminho, conteudo)`
  - Escreve conteúdo em um arquivo

### 11. Matemática e cálculos

- `calcular(expressao)`
  - Resolve expressões matemáticas em Python

### 12. Comandos que a Betty entende

A Betty classifica comandos em ações como:

- `TIME`
- `BATTERY`
- `CPU`
- `UPTIME`
- `TEMPERATURE`
- `VOLUME_NOW`
- `VOLUME_UP`
- `VOLUME_DOWN`
- `POWEROFF`
- `REBOOT`
- `MUTE`
- `OPEN_PROGRAM <programa>`
- `OPEN_GAME <jogo>`
- `SEARCH_WEB|<consulta>`
- `SAVE_MEMORY|<chave>|<valor>`
- `GET_MEMORY|<chave>`
- `CALCULATE|<expressao>`
- `READ_SCREEN`
- `UNKNOWN`

## Exemplo de uso

```bash
uv run betty
```

Depois, a Betty pode receber comandos por teclado ou voz, como:

- "que horas são?"
- "qual a temperatura?"
- "abre o firefox"
- "pesquise sobre inteligência artificial"
- "aumenta o volume"
- "desliga o computador"
- "leia a tela"
- "me lembra que meu editor favorito é o Vs code"

## Observação

Este projeto é uma continuação indireta do projeto Jarvis, com foco em automação doméstica, IA local e interação de voz com personalidade própria.

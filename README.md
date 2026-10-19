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
- Corretor ortográfico (`skills/spelling.py`)
  - Monitora campos de texto editáveis expostos pelo AT-SPI, em sessões Wayland e X11
  - Verifica português brasileiro com um servidor LanguageTool local (`http://127.0.0.1:8081`)
  - Exibe uma notificação discreta com comentário da Betty e ações para aceitar ou ignorar a correção
  - Só altera o campo se o texto continuar igual ao que foi verificado; campos sem suporte de acessibilidade e campos de senha são ignorados
  - O servidor LanguageTool precisa estar instalado e em execução localmente. A URL pode ser alterada com `BETTY_LANGUAGETOOL_URL`, mas deve continuar apontando para um IP loopback (`127.0.0.1` ou `::1`); texto digitado não é enviado a serviços remotos
  - A captura depende de o aplicativo expor texto editável pelo AT-SPI e de a acessibilidade estar habilitada no ambiente gráfico. Em alguns desktops, é necessário habilitar a acessibilidade nas configurações do sistema; a cobertura pode variar entre aplicativos

### 2. Interação com o usuário

- `responder(texto, *, personalizar=True, fala=None)`
  - Formata a resposta, personaliza o texto e fala em voz

- `processar_comando(comando)`
  - Interpreta texto do usuário, classifica a intenção e executa a ação correta

- `main()`
  - Loop principal que processa comandos por teclado e voz simultaneamente

- Entrada de texto
  - Uma thread independente mantém o prompt de teclado ativo enquanto o wake word aguarda no microfone; comandos digitados e falados usam o mesmo interpretador

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

- `listen_for_command()`
  - Monitora o microfone localmente com um modelo português do Vosk, restringindo o vocabulário de ativação a “Betty”; o Whisper só transcreve após a ativação

- `listen(filename="input.wav", duration=5, fs=16000)`
  - Captura uma entrada curta e a transcreve em português com Whisper

- `audio_worker()`
  - Thread responsável por tocar a fila de áudio


```bash
uv sync
uv run betty
```
### Wake Word
Depois de detectar “Betty”, a escuta aguarda até quatro segundos pelo início do comando e encerra a captura após 0,8 segundo de silêncio. Assim, uma pausa breve entre a ativação e o comando não é confundida com o fim da fala. O Whisper recebe um contexto curto de comandos em português, e a transcrição alternativa “Batch” para a ativação é descartada. Respostas curtas como “horário” também são interpretadas como pedido da hora.

No Linux, instale o PortAudio do sistema (por exemplo, `sudo apt install libportaudio2`) e permita acesso ao microfone. No Windows, habilite o acesso ao microfone nas configurações de privacidade. Você pode digitar comandos no prompt enquanto a Betty aguarda “Betty” no microfone; ambos passam pela mesma interpretação de intenções. Diga “Betty, pare” ou “Betty, desativar” para interromper a escuta por voz sem desativar a entrada de texto. `Ctrl+C` encerra o processo.

O Whisper usa o modelo `small` em CPU por padrão; defina `BETTY_WHISPER_MODEL=base` se preferir reduzir o consumo de recursos, com possível redução de precisão.

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

- `proxima_media()`
  - Avança para a próxima mídia em reprodução

- `anterior_media()`
  - Volta para a mídia anterior

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
- `NEXT_MEDIA`
- `PREVIOUS_MEDIA`
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

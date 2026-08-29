# PixelFenda v0.3.0 — Layer Mutation Studio

PixelFenda é um processador autoral de vídeo/glitch art. A v0.3.0 preserva a base validada da v0.2.1 (VRAM virtual persistente, 20 efeitos originais, 19 filtros, OpenGL/RTX, FFT/optical-flow e NVENC) e transforma o programa em uma **estação de mutação em camadas**.

## Destaques da v0.3.0

- **Layer Stack** com até 12 camadas na interface.
- Camadas de **Efeito**, **Filtro** e **LUT `.cube`** na mesma pilha.
- Intensidade e opacidade independentes por camada.
- 9 modos de blend: Normal, Screen, Multiply, Add, Difference, Overlay, Soft Light, Lighten e Darken.
- Modulação por camada: áudio, graves, médios, agudos, beat, movimento, corte de cena ou LFO.
- **Auto Scene Mutator**: cria variações determinísticas de intensidade a cada corte.
- Modo de **reset de memória temporal** nos cortes, útil para VRAM/feedback.
- Detecção de cortes interna, sem dependência obrigatória adicional.
- Projetos `.pixelfenda.json`: salve e recupere toda a pilha e configurações.
- Fila de render para múltiplos vídeos usando a mesma pilha.
- Prévia comparativa **ANTES / DEPOIS** em qualquer posição do vídeo.
- Importação de LUTs 1D/3D no formato `.cube`.
- 3 LUTs autorais incluídos: Cobalt Noir, Amber Crypt e Chrome Ice.
- Integração opcional com **Demucs** para separar voz e instrumental localmente.
- Áudio: original, sem áudio, substituir, mixar, somente voz ou somente instrumental.
- Cinco novos efeitos autorais, também com rota GPU quando ModernGL estiver ativo:
  - Cyber Wire
  - Liquid Chrome
  - PSX Dither
  - Gothic Halo
  - Signal Grid
- Total da v0.3.0: **25 efeitos + 19 filtros + LUTs customizáveis**.

## Requisitos base

- Windows 10/11 recomendado.
- Python 3.11+; a bancada principal da v0.2.1 foi validada em Python 3.13 no computador do usuário.
- NVIDIA RTX é opcional, mas recomendada.
- FFmpeg.

Dependências Python básicas:

```text
numpy>=2.0,<3
opencv-python>=4.10,<5
Pillow>=10.4,<13
imageio-ffmpeg>=0.6,<1
moderngl>=5.12,<6
glcontext>=3.0,<4
```

Demucs/PyTorch **não** fazem parte das dependências básicas.

## Instalação rápida no Windows

Extraia a pasta e execute:

```text
install_windows.bat
```

Depois:

```text
run_windows.bat
```

Ou manualmente:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\pixelfenda.py
```

## Autoteste v0.3.0

Antes do primeiro render grande:

```powershell
python .\teste_v030.py
```

O autoteste verifica:

- projeto JSON;
- LUT `.cube` 3D;
- detecção de corte;
- Layer Stack CPU;
- rota gráfica OpenGL quando disponível;
- todos os 25 efeitos;
- todos os 19 filtros;
- H.264/HEVC/AV1 NVENC.

A v0.3.0 foi validada fisicamente em uma RTX 4060: o autoteste retornou renderer `NVIDIA GeForce RTX 4060/PCIe/SSE2`, Layer Stack GPU OK e `h264_nvenc`, `hevc_nvenc` e `av1_nvenc` como `OK`.

## Como usar a pilha de camadas

A aba **Camadas** é processada de cima para baixo. Exemplo:

1. `VRAM Corrupted Memory` — 55%
2. `Cyber Wire` — Screen, 42%
3. `Cold Archive` — 65%
4. LUT `Cobalt Noir` — 35%

Cada camada possui:

- `Ativa`;
- tipo;
- preset/LUT;
- intensidade;
- opacidade/mix;
- blend;
- fonte de modulação;
- força da modulação;
- opção de reset de memória em cortes;
- nome opcional.

### Intensidade x Opacidade

**Intensidade** altera a força interna do efeito/filtro. **Opacidade** define quanto o resultado daquela camada entra na composição final. Isso permite, por exemplo, um efeito internamente agressivo com apenas 20% de presença na imagem final.

## Modulação por camada

Fontes disponíveis:

- Sem modulação
- Energia do áudio
- Graves
- Médios
- Agudos
- Batida/transiente
- Movimento da cena
- Pulso de corte de cena
- LFO lento

A análise necessária é ativada automaticamente quando uma camada pede determinada fonte. Assim, mesmo que a reatividade global esteja em `Livre`, uma camada configurada como `Beat` continuará recebendo análise FFT.

## Automação por cena

Quatro modos:

- **Desligado** — nenhuma automação global de cena.
- **Pulso nos cortes** — reforço curto da intensidade ao detectar corte.
- **Resetar memória/feedback** — reinicia estados temporais nos cortes.
- **Auto Scene Mutator** — cria novos ganhos determinísticos por camada a cada cena, preservando a ordem da pilha.

A aba Automação também permite executar uma análise prévia e listar os tempos dos cortes detectados.

## LUT `.cube`

A v0.3.0 aceita:

- `LUT_1D_SIZE`
- `LUT_3D_SIZE`
- `DOMAIN_MIN`
- `DOMAIN_MAX`

LUTs 3D usam interpolação trilinear em blocos de linhas para controlar o uso de memória. Na v0.3.0, LUTs customizadas usam uma rota CPU compatível; os demais efeitos/filtros continuam podendo usar OpenGL/RTX.

LUTs autorais da distribuição (a distribuição pode incluir os `.cube`; o código-fonte também os reconstrói deterministicamente na primeira utilização):

- `PixelFenda_CobaltNoir.cube`
- `PixelFenda_AmberCrypt.cube`
- `PixelFenda_ChromeIce.cube`

## Áudio e separação de stems

Os modos normais continuam disponíveis:

- Manter áudio original
- Vídeo sem áudio
- Substituir por música/áudio
- Misturar original + nova música

A v0.3.0 adiciona:

- Somente voz
- Sem voz / instrumental

Esses dois modos dependem de stems gerados previamente com Demucs.

### Demucs opcional

Execute:

```text
install_demucs_optional.bat
```

Esse instalador cria `.venv_demucs` separado da instalação principal. Isso evita tornar o PixelFenda dependente de PyTorch para quem não usa separação de áudio.

Depois verifique:

```powershell
python .\demucs_status.py
```

A interface chama o Demucs localmente. Nenhuma API paga é usada. A disponibilidade de CUDA depende da versão do PyTorch instalada no ambiente Demucs.

## Fila de render

A aba **Fila** permite:

- adicionar o trabalho atual;
- selecionar vários vídeos de uma vez;
- escolher uma pasta de saída;
- renderizar todos sequencialmente usando o projeto/pilha atual.

Por segurança, os modos `Somente voz` e `Instrumental` não são aplicados automaticamente à fila multi-vídeo, pois cada vídeo exige seus próprios stems.

## Projeto `.pixelfenda.json`

O projeto salva:

- resolução/enquadramento;
- encoder;
- modo GPU;
- seed;
- reatividade;
- automação de cena;
- áudio;
- caminhos de stems;
- todas as camadas e sua ordem.

Há um exemplo em:

```text
presets/Projeto_Gothic_Layered.pixelfenda.json
```

## Linha de comando

### Projeto completo

```powershell
python .\pixelfenda.py --cli --project .\meu_projeto.pixelfenda.json -i entrada.mp4 -o saida.mp4
```

### Compatibilidade simples estilo v0.2

```powershell
python .\pixelfenda.py --cli -i entrada.mp4 -o saida.mp4 --effect cyber_wire --filter cold_archive --reactive both --scene-mode mutate
```

### Detectar cenas

```powershell
python .\pixelfenda.py --cli -i entrada.mp4 --analyze-scenes --scene-threshold 0.22
```

## Compatibilidade v0.2.1

A v0.3.0 preserva:

- VRAM 1024×512×16-bit;
- seis efeitos VRAM originais;
- efeitos CPU/OpenGL da v0.2;
- 19 filtros;
- optical flow Farneback;
- FFT de áudio;
- H.264/HEVC/AV1 NVENC;
- fallback CPU;
- scroll e interface ajustável;
- correção de uniforms GLSL otimizados;
- diagnóstico GPU/NVENC.

## Observações sobre GPU

A RTX é usada em duas áreas independentes:

1. **OpenGL/ModernGL** para shaders de efeitos/filtros.
2. **NVENC** para codificação de vídeo.

LUT customizada e alguns efeitos estruturais/VRAM continuam usando CPU por desenho. Em uma pilha mista, o programa combina os dois backends.

## Pesquisa técnica da v0.3.0

Veja:

```text
docs/research/PESQUISA_v0.3.0.md
```

## Licença

MIT. Consulte `LICENSE`.

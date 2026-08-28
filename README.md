# PixelFenda v0.1.0

**PixelFenda** é um processador de vídeo autoral para glitch art. A primeira versão é dedicada a um núcleo **VRAM Corruption**, inspirado em falhas de memória gráfica de consoles 32-bit: tiles copiados para endereços errados, tearing por linhas/colunas, stride incorreto, persistência de framebuffer e corrupção de bitplanes em uma representação RGB555 de 15 bits.

> Importante: PixelFenda não executa nem modifica ROM de PlayStation e não é uma cópia do Corrupted Souls Engine. Ele recebe vídeo comum e simula, sobre os dados de cada quadro, famílias de artefatos visualmente relacionadas a corrupção de VRAM.

## Recursos da v0.1.0

- Entrada: MP4, MOV, MKV, AVI, WEBM e outros formatos aceitos pelo OpenCV/FFmpeg.
- Saída MP4 H.264 com áudio original opcional.
- NVIDIA NVENC quando funcional; fallback automático para CPU/libx264.
- Seed reproduzível.
- Intensidade 0–100.
- Modos de enquadramento: crop, fit ou stretch.
- Presets de efeito:
  - Corrupted Memory
  - Tile Storm
  - Palette Collapse
  - Address Shift
  - Controlled Glitch
  - Full Corruption
- Prévia de um quadro antes da renderização.

## Resoluções

- Original do vídeo
- TikTok / Shorts / Reels: 1080×1920 (9:16)
- YouTube: 1920×1080 (16:9)
- Instagram Reels/Stories: 1080×1920
- Instagram Feed quadrado: 1080×1080 (1:1)
- Instagram Feed retrato: 1080×1350 (4:5)
- Instagram / horizontal: 1920×1080 (16:9)
- Instagram Feed paisagem: 1080×566 (1.91:1)
- Personalizada

## Instalação no Windows

1. Instale Python 3.11 ou 3.12 (marque a opção de adicionar Python ao PATH).
2. Extraia a pasta PixelFenda.
3. Dê dois cliques em `install_windows.bat`.
4. Depois, execute `run_windows.bat`.
5. Escolha o vídeo de entrada, preset, intensidade, seed e clique em **GERAR VÍDEO**.

O pacote instala `imageio-ffmpeg`, então normalmente não é necessário configurar FFmpeg manualmente.

## Uso por linha de comando

```powershell
python pixelfenda.py --cli -i entrada.mp4 -o saida.mp4 --resolution original --effect corrupted_memory --intensity 78 --seed 2026
```

Exemplo para Reels/TikTok:

```powershell
python pixelfenda.py --cli -i entrada.mp4 -o saida_vertical.mp4 --resolution instagram_reels --resize crop --effect full_corruption --intensity 85 --seed 1977
```

Teste rápido de 5 segundos:

```powershell
python pixelfenda.py --cli -i entrada.mp4 -o teste.mp4 --max-seconds 5 --encoder cpu
```

## Como o núcleo funciona

1. O quadro é redimensionado para um framebuffer virtual de baixa resolução.
2. A imagem é quantizada para **RGB555 (15 bits)**, aproximando a granularidade cromática de hardware 32-bit clássico.
3. O programa altera os valores do framebuffer diretamente por operações de memória:
   - rectangle blits e tiles repetidos;
   - deslocamento horizontal/vertical de bandas;
   - reinterpretação de faixas como vetor linear e novo offset de endereço;
   - XOR/OR/AND e rotações em bitplanes;
   - linhas/colunas periódicas danificadas;
   - reaproveitamento de fragmentos do quadro anterior.
4. O framebuffer é convertido de volta para BGR/RGB e ampliado por **nearest-neighbour**, preservando os pixels duros.
5. O áudio é muxado ao vídeo final pelo FFmpeg.

A combinação muda em eventos de vários quadros; por isso o efeito não parece apenas ruído independente a cada frame.

## Estrutura para versões futuras

O programa separa presets, motor e interface. Novos filtros podem ser adicionados como novos processadores sem alterar o fluxo de entrada/saída. Exemplos planejáveis: CRT/scanline, VHS, datamosh, feedback analógico, dithering temporal, chromatic aberration e filtros cinematográficos.

# PixelFenda v0.2.1 — Video Mutation Studio

**PixelFenda** é um processador de vídeo autoral para glitch art, estética analógica/digital, filtros cinematográficos e mutação visual reativa. A v0.2.1 preserva todos os seis efeitos da v0.1.0 e transforma o programa em uma arquitetura com **Efeitos** e **Filtros** independentes.

> PixelFenda não executa ROMs, não modifica jogos e não é uma cópia de Corrupted Souls. A família VRAM simula, sobre quadros de vídeo comuns, comportamentos estruturais inspirados em memória gráfica: framebuffer, páginas de textura, histórico temporal, erros de endereço, bitplanes e blits.

## Novidades principais

- **VRAM virtual persistente real dentro do programa: 1024×512×16-bit**.
- Áreas persistentes para framebuffer, texture page e history page; corrupções podem vazar de uma região para outra.
- **20 efeitos**: seis preservados da v0.1.0 + 14 novos.
- **19 filtros** incluindo Vintage, Cinematic, filme antigo frio, cinza/P&B e `Odisseia 70`.
- Efeito e filtro podem ser ligados independentemente: efeito apenas, filtro apenas, ambos ou nenhum.
- Reatividade: livre, movimento da cena, música/áudio ou ambos.
- Análise de movimento por optical flow em baixa resolução.
- Análise de áudio por FFT sem API paga e sem serviço online.
- Áudio final: original, silencioso, substituir por música ou misturar música + original.
- GPU opcional por **ModernGL/OpenGL fragment shaders**; fallback automático para CPU.
- NVIDIA NVENC: H.264, H.265/HEVC e AV1 quando o FFmpeg/GPU suportarem.
- Interface minimalista fria, redimensionável, com barra vertical e scroll do mouse.
- Seed reproduzível.
- Presets para TikTok, YouTube, Instagram/Reels/Feed e resolução personalizada.

## Efeitos

### VRAM / legado preservado
1. VRAM Corrupted Memory
2. VRAM Tile Storm
3. VRAM Palette Collapse
4. VRAM Address Shift
5. VRAM Controlled Glitch
6. VRAM Full Corruption

### Novos
7. ASCII Terminal
8. Digital Rain
9. Gothic Crimson
10. Spectral Echo
11. Pixel Sort
12. Scanline Melt
13. Chromatic VHS
14. CRT Terminal
15. Void Bloom
16. Neon Noir
17. Retro Space PC
18. Datamosh Flow
19. Recursive Feedback
20. Brutalist Collage

As referências enviadas em `efeitos.rar` foram tratadas como linguagem visual, não como material a ser embutido no software. O programa gera os efeitos proceduralmente.

## Filtros

- Vintage 70
- Vintage 90
- Cinematic Teal & Amber
- Cold Archive
- Silver Gray
- Noir
- **Odisseia 70 — inspirado em 65/70mm fotoquímico**
- Bleach Bypass
- Terminal Green
- Gothic Iron
- Y2K Chrome
- Dream White
- Neon Night
- Space Blue
- Antique Sepia
- Social Cool
- Muted Linen
- Soft B&W
- Infrared Ice

`Odisseia 70` é uma interpretação autoral, não um LUT oficial do filme. A pesquisa da v0.2.0 usa como referência técnica o fato de *The Odyssey* (2026) ter sido fotografado integralmente em 15-perf IMAX 65mm, com KODAK VISION3 250D 5207 para dia e 500T 5219 para baixa luz/noite, e acabamento orientado por color timing fotoquímico. O preset traduz essas ideias em saturação contida, microgrão fino, highlights levemente quentes, sombras neutras/frias e bloom discreto.

## Reatividade

- **Livre:** o efeito segue sua própria dinâmica procedural.
- **Movimento:** optical flow mede magnitude e direção aparente entre quadros; deslocamento, feedback e corrupção recebem esses valores.
- **Áudio:** o áudio é decodificado pelo FFmpeg e analisado por FFT. São extraídas energia global, graves, médios, agudos e transientes/beat.
- **Movimento + áudio:** combina os dois sinais.

Quando uma nova música é escolhida, ela também pode ser a fonte da reatividade.

## Áudio

- **Manter áudio original**
- **Vídeo sem áudio**
- **Substituir por outra música/áudio** — a nova faixa é repetida se necessário e cortada na duração do vídeo.
- **Misturar áudio original + nova música** — a faixa adicional entra com ganho reduzido.

A v0.2.0 não faz separação neural de stems; portanto, “remover música preservando diálogo” não é prometido como recurso desta versão. O modo silencioso remove todo o áudio original.

## GPU / RTX 4060

A arquitetura possui dois usos diferentes da GPU:

1. **Shaders OpenGL via ModernGL:** efeitos e color grading compatíveis são executados em fragment shaders. Isso usa a GPU gráfica diretamente, sem exigir uma compilação customizada do OpenCV CUDA.
2. **NVENC via FFmpeg:** codificação de saída H.264, HEVC ou AV1 quando disponível.

Efeitos que dependem de operações de memória específicas ou algoritmos particulares podem continuar na CPU (por exemplo VRAM procedural, Pixel Sort e Datamosh Flow), enquanto o filtro pode ser executado na GPU no mesmo pipeline.

Execute `diagnostico_gpu.py` para verificar OpenGL e os encoders NVENC.

## Instalação Windows

1. Instale Python 3.11 ou superior.
2. Extraia o pacote.
3. Execute `install_windows.bat` uma vez.
4. Execute `run_windows.bat`.
5. Selecione o vídeo, resolução, efeito/filtro, reatividade, áudio e encoder.
6. Use **Prévia** antes do render completo.
7. Clique em **GERAR VÍDEO**.

Recomenda-se driver NVIDIA Studio atualizado para trabalhos longos de criação.

## CLI

VRAM + filtro frio + movimento:

```powershell
python pixelfenda.py --cli -i entrada.mp4 -o saida.mp4 --effect corrupted_memory --effect-intensity 78 --filter cold_archive --filter-intensity 65 --reactive motion
```

Apenas filtro Odisseia 70, sem efeito:

```powershell
python pixelfenda.py --cli -i entrada.mp4 --no-effect --filter odyssey_70 --filter-intensity 90
```

Efeito reativo a uma música substituta:

```powershell
python pixelfenda.py --cli -i entrada.mp4 --effect spectral_echo --reactive audio --audio-mode replace --music musica.wav
```

AV1 NVENC em uma RTX 40:

```powershell
python pixelfenda.py --cli -i entrada.mp4 --effect neon_noir --encoder av1_nvenc --gpu gpu
```

## Resoluções

- Original
- TikTok / Shorts / Reels: 1080×1920
- YouTube: 1920×1080
- Instagram Reels/Stories: 1080×1920
- Instagram Feed 1:1: 1080×1080
- Instagram Feed 4:5: 1080×1350
- Instagram horizontal 16:9: 1920×1080
- Instagram Feed 1.91:1: 1080×566
- Personalizada

## Documentação incluída

- `ANALISE_ANEXOS_v0.2.0.md` — leitura das referências enviadas.
- `PESQUISA_EFEITOS_FILTROS_v0.2.0.md` — pesquisa técnica e decisões de arquitetura.
- `ANALISE_REFERENCIA.md` — documentação da referência inicial da v0.1.0.
- `VALIDACAO_v0.2.0.md` — testes executados e limitações conhecidas da bancada.
- `TESTE_VISUAL_EFEITOS_v0.2.0.jpg` e `TESTE_VISUAL_FILTROS_v0.2.0.jpg` — matrizes visuais autorais de validação.
- `CHANGELOG.md` — evolução do programa.

## Licença

MIT. Consulte `LICENSE`.

## Validação de hardware — v0.2.1

A v0.2.1 foi validada em hardware real com **NVIDIA GeForce RTX 4060 8 GB / Windows 10**. O autoteste confirmou:

- ModernGL/OpenGL na RTX 4060;
- VRAM Corrupted Memory + filtro simultaneamente;
- shader GPU + filtro simultaneamente;
- H.264 NVENC;
- HEVC/H.265 NVENC;
- AV1 NVENC.

Além do autoteste, um render completo com **efeito + filtro** foi concluído com sucesso. Para reproduzir a bancada, execute `python .\\teste_hotfix_v021.py` dentro do ambiente virtual.

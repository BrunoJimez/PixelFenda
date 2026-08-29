# Changelog

## v0.3.0 — Layer Mutation Studio

### Arquitetura
- Introduz Layer Stack com camadas de efeito, filtro e LUT.
- Até 12 camadas na interface.
- Estado temporal independente por camada.
- Preserva a VRAM virtual persistente 1024×512×16-bit.
- Mantém a correção v0.2.1 para uniforms GLSL otimizados e NVENC.

### Composição
- Intensidade e opacidade independentes.
- 9 blend modes: Normal, Screen, Multiply, Add, Difference, Overlay, Soft Light, Lighten, Darken.
- Reordenação, duplicação e nome customizado de camadas.

### Modulação
- Modulação por camada via áudio, bass, mids, treble, beat, motion, scene pulse ou LFO.
- Análises FFT/optical flow são habilitadas automaticamente quando alguma camada exige a fonte.

### Cena
- Detector interno de cortes baseado em diferença HSV.
- Lista de cortes e tempos na interface.
- Scene Pulse.
- Reset de memória/feedback em cortes.
- Auto Scene Mutator determinístico por seed.

### Efeitos
- Preserva os 20 efeitos da v0.2.1.
- Adiciona 5 efeitos autorais:
  - Cyber Wire
  - Liquid Chrome
  - PSX Dither
  - Gothic Halo
  - Signal Grid
- Total: 25 efeitos.

### Filtros e LUT
- Preserva 19 filtros.
- Suporte a LUT `.cube` 1D/3D.
- Interpolação trilinear para LUT 3D.
- Inclui 3 LUTs autorais: Cobalt Noir, Amber Crypt, Chrome Ice.

### Áudio
- Preserva original/silent/replace/mix.
- Integração opcional com Demucs para gerar voz e instrumental.
- Modos de saída: somente voz e instrumental.
- Demucs isolado em ambiente opcional `.venv_demucs`.

### Workflow
- Projeto `.pixelfenda.json`.
- Fila multi-vídeo.
- Prévia lado a lado Antes/Depois com posição ajustável.
- CLI pode renderizar um projeto completo.
- Novo `teste_v030.py`.

### Validação de desenvolvimento
- Todos os módulos compilados com sucesso.
- 25/25 efeitos passaram pelo preview CPU.
- 19/19 filtros passaram pelo preview CPU.
- LUT 3D e projeto JSON validados.
- Detector de corte validado com corte sintético.
- Render real de 60 quadros com 3 camadas, LUT, motion-reactive e Auto Scene Mutator concluído em bancada CPU/libx264.
- **Hardware validated:** RTX 4060/ModernGL OK; Layer Stack GPU com novos shaders + feedback + filtro OK; H.264/HEVC/AV1 NVENC OK.

## v0.2.1 — Hotfix GPU + NVENC
- Corrige uniform GLSL otimizado (`u_treble`) ao combinar efeito + filtro.
- Corrige callback de exceção do Tkinter.
- Corrige falso negativo NVENC com probe real 1280×720.
- Validada em Windows 10 + RTX 4060: ModernGL, H.264/HEVC/AV1 NVENC e render efeito+filtro.

## v0.2.0 — Video Mutation Studio
- VRAM virtual persistente 1024×512×16-bit.
- 20 efeitos e 19 filtros.
- Reatividade por movimento/áudio.
- OpenGL/ModernGL + NVENC.

## v0.1.0
- Primeira engine VRAM-inspired.

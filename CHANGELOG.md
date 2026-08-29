# Changelog

## v0.2.1 — Hotfix GPU + NVENC

- Corrige uniform GLSL otimizado (`u_treble`) que quebrava filtros na rota OpenGL.
- Uniforms reativos passam a ser definidos de forma tolerante a otimizações do driver.
- `u_treble` agora participa do shader Digital Rain.
- Corrige callback de erro do Tkinter para preservar a exceção real do worker.
- Gera `pixelfenda_error.log` com traceback completo em caso de falha.
- Substitui o probe NVENC 64×64 por encode real 1280×720 e adiciona cache.
- H.264, HEVC e AV1 NVENC podem ser detectados corretamente em RTX 40.

### Validação de hardware da v0.2.1

- Validada em Windows 10 com NVIDIA GeForce RTX 4060 8 GB.
- ModernGL/OpenGL: OK.
- Combinação VRAM Corrupted Memory + filtro na GPU: OK.
- Combinação shader + filtro na GPU: OK.
- H.264 NVENC: OK.
- HEVC/H.265 NVENC: OK.
- AV1 NVENC: OK.
- Render real com efeito + filtro concluído com sucesso.

## v0.2.0 — Video Mutation Studio

- Preserva todos os efeitos da v0.1.0.
- Implementa VRAM virtual persistente 1024×512×16-bit.
- Adiciona 14 efeitos autorais.
- Adiciona 19 filtros/gradações.
- Separa Efeitos e Filtros em toggles independentes.
- Adiciona reatividade a optical flow e FFT de áudio.
- Adiciona áudio original, mute, replace e mix.
- Adiciona backend ModernGL/OpenGL com fallback CPU.
- Adiciona H.264/HEVC/AV1 NVENC.
- Interface redimensionável, fria/minimalista e com scroll vertical/mouse wheel.
- Adiciona diagnóstico de GPU/encoder.
- Adiciona documentação da pesquisa e dos anexos.

## v0.1.0

- Primeira versão do motor VRAM-inspired.
- Corrupted Memory, Tile Storm, Palette Collapse, Address Shift, Controlled Glitch e Full Corruption.
- Resoluções para redes sociais.
- NVENC H.264 + fallback libx264.

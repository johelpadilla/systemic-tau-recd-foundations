# Roadmap teórico Systemic Tau / RECD

**Orden de ataque:** 1 → 2 → 3 → 4 (5 y 6 en paralelo)  
**Estado global (2026-08-01):** **Arco 1–6 cerrado en v0.1**

## Estado

| Punto | Contenido | Estado | Artefacto |
|-------|-----------|--------|-----------|
| **1a–1c** | Formalización de conjunciones, anidamiento, Res | **Hecho v0.1** | `Nota_Formal_Conjunciones_Ordinales.*` |
| **2** | Sinergia irreducible, PID, puente Res–excess3 | **Hecho v0.1** | `Nota_Formal_Sinergia_Irreducible.*` |
| **3** | Estatus de α(λ) / ponderación ontológica | **Hecho v0.2** (+ Gibbs Via B) | `Nota_Formal_Ponderacion_Ontologica.*` + `scripts/gibbs_alpha_compare.py` |
| **4** | Conjunciones en la ruta de Feigenbaum | **Hecho v0.3** (+ barrido \(r\) + diag Res_pair) | `Nota_Formal_Feigenbaum_Conjunciones.*` + `scripts/cascade_r_sweep.py` + `scripts/res_pair_diagnostics.py` |
| **5** | Invariantes y robustez de τₛ / M_ℓ | **Hecho v0.1** | `Nota_Formal_Invariantes_Robustez.*` |
| **6** | Esbozo categórico / algebraico | **Hecho v0.1** | `Nota_Formal_Categorias_Conjunciones.*` |

Índice y respuestas al criterio de éxito: **`INDICE_NOTAS_FORMALES.md`**

## Criterio de éxito — cerrado a nivel de definiciones

| Pregunta | Respuesta |
|----------|-----------|
| ¿Qué es sinergia irreducible ordinal? | \(\mathrm{Res}_{\mathrm{pair}}=\mathrm{KL}(P\|P^{(2)})>\theta_3\) |
| ¿Por qué L3 ≠ “más correlación”? | L3 = residuo fuera de \(\mathcal{R}_{\mathrm{pair}}\); correlación es orden ≤2 |
| ¿Qué cambia en transiciones (Feigenbaum)? | Dual τₛ + profundidad. Emp: excess3 pico cerca \(r_\infty\); Res_pair con \(w\) adecuado mono pre→caos (colapso en caos era sesgo \(w{=}13\)); residual bajo en \(r_\infty\); var ≠ A3 |
| ¿Estatus de α(λ)? | Princip de diseño axiomatizado + template preespecificado; no observable del joint |

## Canon C1–C38 (no reabrir sin scholium)

### Nota 1
1. Conjunción = claim + medida sobre \(S\), A1–A3  
2. Tres planos: claim / estimador / reloj  
3. Nivel 3 := residuo, no := excess³  
4. Anidamiento canónico := Tipo II (claims)  
5. ΔRECD := suma ponderada de evidencias  
6. M-I-1  

### Nota 2
7. Res_ind = TC = KL(P‖P_ind)  
8. TC = Res_pair + TC(P⁽²⁾)  
9. L3 fuerte / débil  
10. Syn heurística ≠ I-proyección  
11. Surp ≥ TC  
12. excess³>0 ⇒ débil, ⇏ fuerte  
13. Reportar (Syn, Surp, excess3)  

### Nota 3
14–21. Separar λ, α, f; modulación operativa; motor admisible; abundancia ≠ share; fallback λ; polaridad s; norma de reporte  

### Nota 4
22–28. Estaciones de cascada; predicción A3; no-trivialidad; separación EWS/τₛ/profundidad; dos usos de δ  

### Nota 5
29–34. Invariancia monótona y permutaciones; no invariancia m/reflexiones mixtas; canónicos; d≥3; T_RECD depende del motor  

### Nota 6
35–38. Π₂ olvido; L3 = obstrucción; claims como funtores; poset de profundidad; categórico subordinado a 1–2  

## Abierto (investigación, no bloqueo de definiciones)

- Conjeturas cuantitativas Syn–Res; teoremas A3(r)  
- ~~Diagnóstico Res_pair vs excess3 en cascada~~ **Hecho**  
- ~~Gibbs-α en software~~ **Hecho** (0.2.2; bridge L∞≈0.16; abundancia≠share)  
- ~~Barrido empírico denso en r~~ **Hecho**  
- ~~Integración paper + cover letter~~ **Hecho**

## Compilar

```bash
cd ~/grok-safe/Fundacion_RECD
for f in Nota_Formal_Conjunciones_Ordinales Nota_Formal_Sinergia_Irreducible \
  Nota_Formal_Ponderacion_Ontologica Nota_Formal_Feigenbaum_Conjunciones \
  Nota_Formal_Invariantes_Robustez Nota_Formal_Categorias_Conjunciones; do
  pdflatex $f.tex && pdflatex $f.tex
done
```

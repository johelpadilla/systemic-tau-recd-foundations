# Índice — Notas formales del roadmap teórico (v0.1 + emp cascade + Res diag)

**Fecha:** 2026-08-01  
**Estado:** Arco 1→6 cerrado en v0.1; **Nota 4 v0.3** (barrido denso + diagnóstico Res_pair); paper fundamentos actualizado.

## Serie

| # | Archivo | Págs. | Cierra |
|---|---------|-------|--------|
| 1 | `Nota_Formal_Conjunciones_Ordinales.pdf` | ~10 | Objeto: claims, axiomas, Res, anidamiento |
| 2 | `Nota_Formal_Sinergia_Irreducible.pdf` | ~9 | L3 fuerte = Res_pair; excess3 delimitado; PID |
| 3 | `Nota_Formal_Ponderacion_Ontologica.pdf` | ~9 | α(λ) + **Gibbs Via B emp.** (v0.2) |
| 4 | `Nota_Formal_Feigenbaum_Conjunciones.pdf` | ~9 | Cascada + barrido \(r\) + **Res_pair diag** (v0.3) |
| 5 | `Nota_Formal_Invariantes_Robustez.pdf` | ~4 | Invariancias, canónicos, asintótica |
| 6 | `Nota_Formal_Categorias_Conjunciones.pdf` | ~4 | Esbozo: Π₂, obstrucción, poset de profundidad |

Compilar todas:

```bash
cd ~/grok-safe/Fundacion_RECD
for f in \
  Nota_Formal_Conjunciones_Ordinales \
  Nota_Formal_Sinergia_Irreducible \
  Nota_Formal_Ponderacion_Ontologica \
  Nota_Formal_Feigenbaum_Conjunciones \
  Nota_Formal_Invariantes_Robustez \
  Nota_Formal_Categorias_Conjunciones
do
  pdflatex "$f.tex" && pdflatex "$f.tex"
done
```

## Criterio de éxito del roadmap — respuestas nítidas

| Pregunta | Respuesta v0.1 |
|----------|----------------|
| ¿Qué es una sinergia irreducible en términos ordinales? | \(\mathrm{Res}_{\mathrm{pair}}(\mathcal{J})=\mathrm{KL}(\mathcal{J}\|P^{(2)})>\theta_3\): el joint de símbolos no es modelo de pares. Categóricamente: obstrucción al funtor de olvido \(\Pi_2\). |
| ¿Por qué el Nivel 3 no es “más correlación”? | Correlación / τₛ / Φ₁ / Φ₂ / TC\((P^{(2)})\) viven en orden ≤2. L3 es el sumando \(\mathrm{KL}(P\|P^{(2)})\) de \(\mathrm{TC}=\mathrm{Res}_{\mathrm{pair}}+\mathrm{TC}(P^{(2)})\). |
| ¿Qué cambia estructuralmente cerca de una transición crítica (ruta Feigenbaum)? | Dual τₛ + profundidad. Emp: excess3 pico cerca \(r_\infty\); Res_pair con \(w\) corto colapsa en caos (sesgo); con \(w\) largo mono pre→caos se restaura; en \(r_\infty\) residual estructuralmente bajo; var ≠ A3. |
| ¿Qué estatus tiene la ponderación ontológica? | Princip admisible axiomatizado + familia preespecificada. No es observable del joint ni ley natural única. Abundancia L3 ≠ share \(f_3\). |

## Canon compacto (C1–C38)

Ver `ROADMAP_TEORICO.md` para la lista numerada completa.

**Núcleo irrenunciable:**
1. Tres planos: claim / estimador / reloj  
2. L3 fuerte := Res_pair; excess3 := proxy  
3. α := diseño admisible; reportar \((M̂,λ,α,f)\)  
4. EWS clásicos ≠ τₛ ≠ profundidad RECD  
5. M-I-1: nada de esto demuestra el acto de ser  

## Qué queda abierto (no es fallo del v0.1)

- Cotas Syn ↔ Res_pair (Conj. Nota 2)  
- Teoremas A_3(r) en clase Feigenbaum acoplada (T4.*)  
- ~~Diagnóstico del colapso de Res_pair~~ **Hecho** (v0.3)  
- ~~Gibbs α en software~~ **Hecho** (`nested-recd` 0.2.2; Nota 3 v0.2; corr(f3,excess3)≈0.08)  
- Validación empírica más allá del ensamble sintético  

## Siguiente trabajo de producto (no roadmap abstracto)

1. ~~Integrar definiciones en paper~~ **Hecho**  
2. ~~Res_pair en `nested-recd`~~ **Hecho** (0.2.1→0.2.2 + Gibbs)  
3. ~~Barrido fino en r~~ **Hecho**  
4. ~~Cover letter Chaos/PRE~~ **Hecho**  
5. ~~Diagnóstico Res_pair~~ **Hecho**  
6. ~~Gibbs-α Via B~~ **Hecho**  
7. Envío journal (siguiente producto humano)  


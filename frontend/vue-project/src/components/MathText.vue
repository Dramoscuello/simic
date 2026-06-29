<template>
  <span v-html="renderedContent" class="math-content"></span>
</template>

<script setup>
/**
 * MathText - Componente para renderizar texto con fórmulas matemáticas LaTeX
 * 
 * Uso:
 *   <MathText :text="contexto" />
 * 
 * Detecta automáticamente LaTeX en el texto y lo renderiza:
 * - Inline: $...$ o \(...\)
 * - Block: $$...$$ o \[...\]
 * - También detecta LaTeX sin delimitadores (\frac, \dfrac, etc.)
 */
import { computed } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  text: {
    type: String,
    default: ''
  },
  displayMode: {
    type: Boolean,
    default: false
  }
})

// Patrones LaTeX comunes que indican que hay matemáticas
const LATEX_PATTERNS = [
  /\\frac/,
  /\\dfrac/,
  /\\sqrt/,
  /\\sum/,
  /\\int/,
  /\\lim/,
  /\\infty/,
  /\\alpha|\\beta|\\gamma|\\delta|\\pi/,
  /\\times|\\div|\\pm|\\cdot/,
  /\\geq|\\leq|\\neq/,
  /\^{[^}]+}/,  // superíndices como x^{2}
  /_{[^}]+}/,   // subíndices como x_{1}
]

/**
 * Detecta si un texto contiene LaTeX sin delimitadores
 */
function containsLatex(text) {
  return LATEX_PATTERNS.some(pattern => pattern.test(text))
}

/**
 * Renderiza una expresión LaTeX con KaTeX
 */
function renderLatex(latex, displayMode = false) {
  try {
    return katex.renderToString(latex, {
      throwOnError: false,
      displayMode: displayMode,
      trust: true,
      strict: false,
      macros: {
        "\\,": "\\thinspace"  // Soporte para espacios finos
      }
    })
  } catch (e) {
    console.warn('KaTeX render error:', e)
    return latex // Devuelve el texto original si falla
  }
}

/**
 * Procesa el texto, detecta LaTeX y lo renderiza
 */
const renderedContent = computed(() => {
  if (!props.text) return ''
  
  let text = props.text
  
  // 1. Procesar bloques $$...$$
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, (match, latex) => {
    return renderLatex(latex.trim(), true)
  })
  
  // 2. Procesar inline $...$
  text = text.replace(/\$([^$]+?)\$/g, (match, latex) => {
    return renderLatex(latex.trim(), false)
  })
  
  // 3. Procesar \[...\] (display mode)
  text = text.replace(/\\\[([\s\S]+?)\\\]/g, (match, latex) => {
    return renderLatex(latex.trim(), true)
  })
  
  // 4. Procesar \(...\) (inline mode)
  text = text.replace(/\\\(([\s\S]+?)\\\)/g, (match, latex) => {
    return renderLatex(latex.trim(), false)
  })
  
  // 5. Detectar LaTeX sin delimitadores (ej: C(x)=\dfrac{...})
  // Buscar patrones como "algo = \comando{...}" 
  text = text.replace(/([A-Za-z]\([^)]+\)\s*=\s*)(\\[a-z]+\{[^}]+\}(?:\{[^}]+\})?(?:[^,\.\s]*)?)/gi, 
    (match, prefix, latex) => {
      if (containsLatex(latex)) {
        return prefix + renderLatex(latex, false)
      }
      return match
    }
  )
  
  // 6. Buscar expresiones matemáticas sueltas con comandos LaTeX
  // Ejemplo: \dfrac{a}{b}, \sqrt{x}, etc.
  text = text.replace(/(\\(?:d?frac|sqrt|sum|int)\{[^}]+\}(?:\{[^}]+\})?)/g, (match) => {
    return renderLatex(match, false)
  })
  
  return text
})
</script>

<style>
.math-content {
  /* Asegurar que el contenido matemático se vea bien */
}

.math-content .katex {
  font-size: 1.1em;
}

.math-content .katex-display {
  margin: 0.5em 0;
}
</style>

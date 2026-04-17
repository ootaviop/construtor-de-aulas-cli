# Exemplo de Aula — Referência de Tags

Este arquivo mostra todas as tags disponíveis para usar no `.docx`.
As tags são escritas como parágrafos no Word, no formato `<tag>` e `</tag>`.

---

## Estrutura geral do documento

```
<topico>
  ...conteúdo do tópico...
</topico>

<topico>
  ...outro tópico...
</topico>
```

Cada `<topico>` vira uma aba/página separada no resultado final.
Se não houver `<topico>`, o documento inteiro é tratado como um único tópico.

---

## `<topo>` — Cabeçalho da aula

Deve ser o primeiro componente dentro de um `<topico>`.
As sub-tags são opcionais.

```
<topo>
<titulotopico>Módulo 1 — Introdução</titulotopico>
<tituloaula>O que é Educação a Distância?</tituloaula>
</topo>
```

> O texto de `<titulotopico>` aparece como etiqueta colorida acima do título.
> O texto de `<tituloaula>` aparece como `<h1>` da aula.

---

## `<secao>` — Agrupador de espaçamento

Envolve componentes para aplicar espaçamento padrão entre eles.
`<topo>` e `<spanmodal>` nunca ficam dentro de `<secao>`.

```
<secao>
  <citacao>
  "Uma citação importante aqui."
  </citacao>

  <atencao>
  Lembre-se de revisar o material complementar.
  </atencao>
</secao>
```

---

## `<citacao>` — Bloco de citação

```
<citacao>
"O conhecimento é a única riqueza que não pode ser roubada."
— Autor Desconhecido
</citacao>
```

---

## `<atencao>` — Caixa de destaque "Atenção"

```
<atencao>
Este conteúdo será cobrado na avaliação final. Preste bastante atenção!
</atencao>
```

---

## `<carrossel>` — Slides navegáveis

Cada slide é delimitado por `<carrosselslide>`.

```
<carrossel>
  <carrosselslide>
  <h3>Slide 1 — Introdução</h3>
  <p>Conteúdo do primeiro slide.</p>
  </carrosselslide>

  <carrosselslide>
  <h3>Slide 2 — Desenvolvimento</h3>
  <p>Conteúdo do segundo slide.</p>
  </carrosselslide>

  <carrosselslide>
  <h3>Slide 3 — Conclusão</h3>
  <p>Conteúdo do terceiro slide.</p>
  </carrosselslide>
</carrossel>
```

---

## `<sanfona>` — Accordion expansível

Cada seção tem `<sanfonasecaocabecalho>` (título clicável) e `<sanfonasecaocorpo>` (conteúdo).

```
<sanfona>
  <sanfonasecao>
    <sanfonasecaocabecalho>O que é aprendizagem ativa?</sanfonasecaocabecalho>
    <sanfonasecaocorpo>
    <p>Aprendizagem ativa é uma abordagem pedagógica em que o estudante...</p>
    </sanfonasecaocorpo>
  </sanfonasecao>

  <sanfonasecao>
    <sanfonasecaocabecalho>Quais são os benefícios?</sanfonasecaocabecalho>
    <sanfonasecaocorpo>
    <p>Os principais benefícios incluem maior engajamento e retenção...</p>
    </sanfonasecaocorpo>
  </sanfonasecao>
</sanfona>
```

---

## `<flipcards>` — Cards que viram

Cada card tem `<flipcardfront>` (frente) e `<flipcardback>` (verso).

```
<flipcards>
  <flipcard>
    <flipcardfront>
    <p>Competência Socioemocional</p>
    </flipcardfront>
    <flipcardback>
    <p>Capacidade de reconhecer e gerenciar as próprias emoções.</p>
    </flipcardback>
  </flipcard>

  <flipcard>
    <flipcardfront>
    <p>Avaliação Formativa</p>
    </flipcardfront>
    <flipcardback>
    <p>Processo contínuo de acompanhamento da aprendizagem do aluno.</p>
    </flipcardback>
  </flipcard>
</flipcards>
```

---

## `<modalcard>` — Cards que abrem modais

Cada card tem título, descrição curta e conteúdo completo no modal.

```
<modalcard>
  <modalcarditem>
    <modalcardtitulo>Planejamento</modalcardtitulo>
    <modalcarddescricao>Clique para saber mais sobre planejamento pedagógico.</modalcarddescricao>
    <modalcardconteudo>
    <p>O planejamento pedagógico é o processo pelo qual o professor organiza...</p>
    <p>Ele deve levar em conta os objetivos de aprendizagem, os recursos disponíveis...</p>
    </modalcardconteudo>
  </modalcarditem>

  <modalcarditem>
    <modalcardtitulo>Avaliação</modalcardtitulo>
    <modalcarddescricao>Conheça os tipos de avaliação.</modalcarddescricao>
    <modalcardconteudo>
    <p>A avaliação pode ser diagnóstica, formativa ou somativa...</p>
    </modalcardconteudo>
  </modalcarditem>
</modalcard>
```

---

## `<listacheck>` — Lista com ícone de check

```
<listacheck>
- Revisar o plano de aula
- Preparar os materiais didáticos
- Verificar os recursos tecnológicos disponíveis
- Realizar a chamada dos alunos
</listacheck>
```

---

## `<listanumero>` — Lista numerada

```
<listanumero>
- Primeiro, identifique os objetivos de aprendizagem.
- Em seguida, selecione as estratégias pedagógicas adequadas.
- Depois, defina os instrumentos de avaliação.
- Por fim, planeje as atividades em sequência lógica.
</listanumero>
```

---

## `<listaletra>` — Lista com letras (a, b, c…)

```
<listaletra>
- Aprendizagem colaborativa
- Metodologias ativas
- Avaliação por competências
- Feedback contínuo
</listaletra>
```

---

## `<videoplayer>` — Player de vídeo (Vimeo)

O conteúdo da tag é a URL de embed do Vimeo.

```
<videoplayer>
https://player.vimeo.com/video/123456789
</videoplayer>
```

---

## `<podcast>` — Player de áudio com modal do especialista

```
<podcast>
<podcasturl>https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/000000000</podcasturl>
<podcastnome>Prof. Maria Silva</podcastnome>
<podcasttema>A importância da escuta ativa na sala de aula</podcasttema>
<podcastsobre>
<p>Maria Silva é doutora em Educação pela USP e atua há 20 anos na formação de professores...</p>
</podcastsobre>
<podcastpdf>https://link-para-o-material.pdf</podcastpdf>
</podcast>
```

> `<podcastpdf>` é opcional. Se omitido, o botão de download não aparece.

---

## `<imagem>` — Imagem centralizada

O conteúdo da tag é o texto alternativo (alt). A URL da imagem é inserida na pós-produção.

```
<imagem>
Diagrama mostrando as etapas do ciclo de aprendizagem
</imagem>
```

---

## `<spanmodal>` — Palavra/trecho clicável que abre modal

É um componente **inline** — fica dentro de um parágrafo de texto normal.

```
<p>
O conceito de
<spanmodal>
<spanmodaltrigger>zona de desenvolvimento proximal</spanmodaltrigger>
<spanmodalcorpo>
<p>A zona de desenvolvimento proximal (ZDP), conceito criado por Vygotsky, refere-se à distância entre o que o aprendiz consegue fazer sozinho e o que consegue fazer com auxílio...</p>
</spanmodalcorpo>
</spanmodal>
é central para entender como o professor pode atuar como mediador.
</p>
```

---

## `<referencias>` — Botão que abre modal de referências bibliográficas

```
<referencias>
<p>FREIRE, Paulo. <strong>Pedagogia do Oprimido</strong>. 17. ed. Rio de Janeiro: Paz e Terra, 1987.</p>
<p>VYGOTSKY, Lev S. <strong>A Formação Social da Mente</strong>. São Paulo: Martins Fontes, 1991.</p>
<p>BRASIL. <strong>Base Nacional Comum Curricular</strong>. Brasília: MEC, 2018. Disponível em: http://basenacionalcomum.mec.gov.br.</p>
</referencias>
```

---

## Exemplo completo de um tópico

```
<topico>

<topo>
<titulotopico>Unidade 2</titulotopico>
<tituloaula>Metodologias Ativas de Ensino</tituloaula>
</topo>

<p>As metodologias ativas colocam o estudante no centro do processo de aprendizagem. Ao longo desta unidade, você vai conhecer as principais abordagens e como aplicá-las na sua prática docente.</p>

<secao>
<atencao>
As atividades desta unidade são obrigatórias para a conclusão do módulo.
</atencao>
</secao>

<secao>
<sanfona>
  <sanfonasecao>
    <sanfonasecaocabecalho>Aprendizagem Baseada em Problemas (ABP)</sanfonasecaocabecalho>
    <sanfonasecaocorpo>
    <p>Na ABP, os alunos partem de um problema real para construir o conhecimento...</p>
    </sanfonasecaocorpo>
  </sanfonasecao>
  <sanfonasecao>
    <sanfonasecaocabecalho>Sala de Aula Invertida</sanfonasecaocabecalho>
    <sanfonasecaocorpo>
    <p>O estudante acessa o conteúdo antes da aula e o tempo em sala é dedicado à prática...</p>
    </sanfonasecaocorpo>
  </sanfonasecao>
</sanfona>
</secao>

<referencias>
<p>BERBEL, Neusi Aparecida Navas. <strong>As metodologias ativas e a promoção da autonomia de estudantes</strong>. Semina: Ciências Sociais e Humanas, Londrina, v. 32, n. 1, p. 25-40, 2011.</p>
</referencias>

</topico>
```

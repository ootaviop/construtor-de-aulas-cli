# Notas de Arquitetura

## Bundles CSS/JS por Profile

Cada profile (curso/projeto) tem seus próprios bundles CSS/JS centralizados, em vez de cada componente carregar assets independentes:

- **Benefício:** Reduz HTTP requests, melhor performance, reutilização de código entre componentes
- **Implementação:** O profile JSON aponta para URLs dos bundles; o pipeline injeta essas URLs na tag `<head>` e antes de `</body>`
- **Futuro (MyBuilder):** Backend compilará bundles customizados baseado na paleta e versão de componentes do projeto

## Isolamento de Componentes em Iframes

A Galeria de Componentes (`/api/gallery/{profile}`) usa `srcdoc` para injetar componentes em iframes isolados:

- Cada iframe recebe: Bootstrap CSS → CSS do profile → HTML do componente → jQuery → Bootstrap JS → JS do profile
- Isola completamente CSS/JS e garante renderização idêntica à de uma aula real
- Permite preview ao vivo sem contaminar o DOM da página principal

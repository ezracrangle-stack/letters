# Cómo editar el sitio (sin programar)

Todo lo que cambias está en un solo archivo: **managers.yaml**.
Cuando guardas un cambio, el sitio se actualiza solo en 3 o 4 minutos.

## Abrir y guardar el archivo

1. Entra a tu repositorio en github.com → clic en **managers.yaml**.
2. Clic en el **lápiz** (Edit this file), arriba a la derecha.
3. Haz tu cambio.
4. Botón verde **Commit changes** → **Commit changes**.

Reglas de oro:
- Respeta los espacios del principio de cada línea. Usa la barra espaciadora, nunca Tab.
- Pon los textos entre comillas `"..."`. Si el texto lleva comillas por dentro, escríbelas así: `\"`.

## Editar tu comentario

Busca al gestor (Ctrl + F con su nombre) y cambia el texto entre comillas de:
- `why:` → por qué leerlo
- `best_for:` → para qué tipo de inversor son sus cartas
- `style:` → estilo de inversión en una línea

## Agregar un gestor que publica cartas en su sitio

Copia este bloque al final de la lista de gestores (antes de la línea `# ─── MANUAL LETTERS`) y cambia los datos:

```yaml
  - id: nombre-corto
    name: Nombre Apellido
    firm: Nombre de la Firma
    style: "Estilo en una línea."
    why: "Por qué vale la pena leerlo."
    best_for: "Para qué inversor."
    letters_page: https://www.firma.com/letters
    access: open
    scrape:
      select: 'a[href$=".pdf"]'
      url_attr: href
      period_from: text
```

- `id`: minúsculas y guiones, sin espacios ni acentos. Es la dirección de su página (`/m/nombre-corto.html`).
- El bloque `scrape` funciona para la mayoría de sitios que listan PDFs con textos como "Q3 2026". Si el sitio es distinto, la primera revisión te avisará con un issue y lo ajustamos juntos.

## Agregar un gestor sin página de cartas (o cartas sueltas)

Igual que arriba, pero sin el bloque `scrape`, y con las cartas a mano:

```yaml
    letters:
      - {period: Q3 2026, url: "https://..."}
      - {period: Q4 2025, title: Annual letter, url: "https://..."}
```

`period` acepta `Q1 2026`, `H1 2026` o solo el año `2025`.

## Gestor que solo comparte cartas a usuarios registrados

En vez de `scrape` o `letters`, pon:

```yaml
    access: registration
```

El sitio muestra su ficha, tu comentario y un enlace a su página, sin enlazar cartas.

## Corregir una carta con fecha o título equivocado

Bajo el gestor, agrega (o amplía) `overrides`. `match` es un pedazo de la dirección de la carta:

```yaml
    overrides:
      - match: "pedazo-del-enlace"
        period: Q1 2025
        title: "Special letter, March 2025"
```

## Quitar un gestor

Borra su bloque completo (desde `- id:` hasta antes del siguiente `- id:`). Sus cartas dejan de mostrarse; el historial queda guardado por si lo vuelves a agregar.

## Revisar que todo salió bien

Pestaña **Actions**: palomita verde = publicado. Cruz roja = abre la ejecución, copia el mensaje y mándamelo.

# Guía para publicar letters.ezrasnotes.com

Tiempo estimado: 30 a 45 minutos, más la espera del DNS (de minutos a unas horas).
No necesitas instalar nada. Todo se hace en el navegador.

Los archivos que vas a subir están en tu carpeta:
`OUTPUTS/letters-site/repo/`

---

## 1. Crea tu cuenta de GitHub

1. Entra a **github.com/signup**.
2. Usa tu correo, una contraseña y un nombre de usuario. El usuario aparece en la dirección técnica del sitio (por ejemplo `ezrasnotes.github.io`), así que elige uno que te guste.
3. Elige el plan **Free**. Es suficiente para todo este proyecto.
4. Te recomiendo activar la verificación en dos pasos (Settings → Password and authentication).

## 2. Crea el repositorio

Un repositorio es la carpeta en línea donde viven los archivos del sitio.

1. Arriba a la derecha, botón **+** → **New repository**.
2. **Repository name:** `letters`
3. Marca **Public**. Tiene que ser público para que GitHub Pages sea gratis.
4. No marques ninguna casilla de "Add a README", ".gitignore" ni "license".
5. Clic en **Create repository**.

## 3. Sube los archivos

1. En la página del repositorio vacío, clic en el enlace **uploading an existing file**.
2. Abre en tu computadora la carpeta `OUTPUTS/letters-site/repo/`.
3. Selecciona **todo lo que hay dentro** (Ctrl + A) y arrástralo a la ventana de GitHub. Las carpetas `docs`, `scripts`, `templates`, `static`, `data` y `tests` se suben con su contenido.
4. Espera a que termine la barra de carga.
5. Abajo, en "Commit changes", escribe `Primera versión` y clic en **Commit changes**.

> Si Windows no muestra el archivo `.gitignore`, no pasa nada: no es indispensable.

## 4. Crea la tarea semanal

Tu computadora no deja escribir en la carpeta `.github`, por eso la tarea viene en el archivo `WORKFLOW_update.yml`. Hay que crearla a mano en GitHub:

1. En el repositorio: **Add file** → **Create new file**.
2. En el nombre escribe exactamente: `.github/workflows/update.yml`
   (al escribir cada `/` GitHub crea la carpeta).
3. Abre `WORKFLOW_update.yml` en tu computadora con el Bloc de notas, copia todo y pégalo en GitHub.
4. Clic en **Commit changes** → **Commit changes**.
5. Opcional: borra `WORKFLOW_update.yml` del repositorio (abre el archivo → menú **⋯** → **Delete file**). Ya no se usa.

## 5. Da permisos a la tarea

1. En el repositorio: **Settings** → **Actions** → **General**.
2. En "Actions permissions" deja marcado **Allow all actions and reusable workflows**.
3. Baja a "Workflow permissions" y marca **Read and write permissions**.
4. Clic en **Save**.

Esto permite que la tarea guarde las cartas nuevas y te abra un aviso (issue) si algo falla.

## 6. Activa GitHub Pages

1. **Settings** → **Pages**.
2. En "Build and deployment" → **Source**: `Deploy from a branch`.
3. **Branch**: `main` y carpeta `/docs`. Clic en **Save**.
4. En uno o dos minutos aparece arriba: "Your site is live at https://TU-USUARIO.github.io/letters/". Ábrelo para comprobar que carga. Los estilos pueden verse raros en esa dirección; se arreglan cuando conectemos el subdominio.

## 7. Conecta letters.ezrasnotes.com

Esto se hace en dos lugares: en GitHub y en el proveedor donde administras el DNS de ezrasnotes.com (donde compraste el dominio: GoDaddy, Namecheap, Cloudflare, Google Domains/Squarespace, etc.). Tu newsletter de Substack no se toca.

**En tu proveedor de dominio**

1. Entra al panel del dominio `ezrasnotes.com` → sección **DNS** (a veces se llama "Manage DNS" o "DNS records").
2. Agrega un registro nuevo:
   - **Tipo:** `CNAME`
   - **Nombre / Host:** `letters`
   - **Valor / Apunta a:** `TU-USUARIO.github.io` (con tu usuario real, sin `/letters`)
   - **TTL:** el que venga por defecto
3. Guarda. Si usas Cloudflare, deja la nube en **gris (DNS only)**, no naranja.

**En GitHub**

1. **Settings** → **Pages** → **Custom domain**: escribe `letters.ezrasnotes.com` → **Save**.
2. GitHub revisa el DNS. Puede tardar desde unos minutos hasta unas horas. Cuando salga la palomita verde, marca **Enforce HTTPS** (puede aparecer hasta una hora después).

**Recomendado (evita que alguien más use tu subdominio):** en tu perfil de GitHub → **Settings** → **Pages** → **Add a domain** → `ezrasnotes.com`. GitHub te da un registro TXT; agrégalo en tu proveedor de DNS igual que el CNAME y vuelve a dar **Verify**.

## 8. Primera revisión de cartas

1. En el repositorio, pestaña **Actions**. Si pide confirmación para activar los workflows, acepta.
2. A la izquierda, **Weekly letters check** → botón **Run workflow** → **Run workflow**.
3. Tarda 3 o 4 minutos (espera 8 segundos entre cada sitio para no molestar).
4. **Palomita verde:** todo bien. El sitio se actualiza solo.
5. **Si algún gestor falla:** la tarea igual termina, no borra nada y te abre un aviso en la pestaña **Issues** con el nombre del gestor. GitHub te manda un correo. Mándame el texto del aviso y lo arreglamos.

Desde aquí, cada lunes la tarea corre sola.

## Si algo no sale

- **"404" en letters.ezrasnotes.com:** revisa que en Pages la carpeta sea `/docs` y que el registro CNAME apunte a `TU-USUARIO.github.io`.
- **El certificado HTTPS no aparece:** espera una hora y vuelve a entrar a Settings → Pages.
- **La tarea falla en "Save changes":** falta el paso 5 (Read and write permissions).

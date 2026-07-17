# 🚀 Guía de Publicación (Deploy 100% Gratis)

Para que el conversor funcione online para todo el mundo gratis, necesitamos subirlo a **Vercel** (Frontend) y **Render** (Backend).

El proceso es muy simple usando GitHub.

---

## 1. Subir el código a GitHub (Gratis)
Si ya tenés cuenta en GitHub, podés usar [GitHub Desktop](https://desktop.github.com/) o la terminal:

```bash
git init
git add .
git commit -m "Versión inicial"
# Creá un repositorio vacío en github.com y luego:
git remote add origin https://github.com/tu-usuario/nef2jpg.git
git push -u origin main
```

---

## 2. Publicar el Backend en Render (Gratis)
El backend procesa las imágenes.

1. Entrá a [Render.com](https://render.com) y creá una cuenta con tu GitHub.
2. Hacé click en **"New +"** y elegí **"Web Service"**.
3. Conectá el repositorio de GitHub que creaste.
4. Render detectará automáticamente el archivo `render.yaml` y configurará todo.
5. Hacé click en **"Create Web Service"**.
6. Esperá a que termine el deploy. Vas a ver una URL parecida a `https://nef2jpg-api.onrender.com`. ¡Copiá esa URL!

---

## 3. Publicar el Frontend en Vercel (Gratis)
El frontend es la página web que ven los usuarios.

1. Primero, abrí el archivo `web/frontend/config.js` en tu PC.
2. Reemplazá `http://localhost:10000` por la URL que copiaste de Render (ej: `https://nef2jpg-api.onrender.com`). Guardá el archivo y hacé `git push` a GitHub para actualizarlo.
3. Entrá a [Vercel.com](https://vercel.com) y creá una cuenta con tu GitHub.
4. Hacé click en **"Add New"** -> **"Project"**.
5. Importá tu repositorio de GitHub.
6. En la configuración de Vercel:
   - **Framework Preset**: Dejalo en *Other*.
   - **Root Directory**: Hacé click en Edit y elegí la carpeta `web/frontend`.
7. Hacé click en **Deploy**.

¡Listo! Vercel te dará una URL (ej: `nef2jpg.vercel.app`) que ya podés compartir con cualquier persona en el mundo.

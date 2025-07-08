# RAG Chatbot - Sistema de Pensiones Dominicano

## 📋 Descripción del Proyecto

Este es un chatbot inteligente basado en **RAG (Retrieval-Augmented Generation)** especializado en el sistema de pensiones dominicano. El sistema utiliza tecnologías modernas para proporcionar respuestas precisas y contextualizadas sobre pensiones, beneficios, requisitos y procedimientos del sistema de pensiones de República Dominicana.

## 🏗️ Arquitectura del Sistema

### Frontend
- **React 18** con **Vite** para el desarrollo
- **Tailwind CSS** para el diseño responsivo
- **shadcn/ui** para componentes de interfaz
- **React Markdown** para renderizado de contenido
- **Syntax Highlighter** para código
- **GitHub Flavored Markdown** para tablas y elementos avanzados

### Backend
- **Flask** (Python) para la API REST
- **Supabase** como base de datos vectorial
- **OpenAI** para embeddings y generación de respuestas
- **LangChain** para el procesamiento de RAG

## 🚀 Tecnologías Utilizadas

### Frontend
```
React 18.2.0
Vite 5.0.8
Tailwind CSS 3.3.5
shadcn/ui components
react-markdown
react-syntax-highlighter
remark-gfm
lucide-react (iconos)
```

### Backend
```
Flask
OpenAI API
Supabase Vector Database
LangChain
Python-dotenv
```

## ⚙️ Configuración del Proyecto

### Prerrequisitos
- Node.js 18+ 
- Python 3.8+
- Cuenta de OpenAI con API key
- Proyecto Supabase configurado

### Variables de Entorno
Crear archivo `.env` en la raíz del proyecto:

```env
# OpenAI
OPENAI_API_KEY=tu_openai_api_key

# Supabase
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=tu_supabase_service_role_key
```

## 🛠️ Instalación y Ejecución

### 1. Instalar Dependencias Frontend
```bash
npm install
```

### 2. Instalar Dependencias Backend
```bash
pip install -r requirements.txt
```

### 3. Ejecutar Backend
```bash
flask --app main.py run --port=5001
```

### 4. Ejecutar Frontend
```bash
npm run dev
```

El frontend estará disponible en: `http://localhost:3001`
El backend estará disponible en: `http://localhost:5001`

## 📊 Características del Chatbot

### Funcionalidades Principales
- ✅ **Chat interactivo** con interfaz moderna
- ✅ **Renderizado Markdown** completo (headers, listas, tablas, código)
- ✅ **Sintaxis highlighting** para bloques de código
- ✅ **Alineación de texto** (izquierda para respuestas, derecha para preguntas)
- ✅ **Tema claro/oscuro** con toggle
- ✅ **Panel de configuración** para parámetros RAG
- ✅ **Fuentes consultadas** con enlaces a documentos
- ✅ **Estado de conexión** en tiempo real

### Parámetros Configurables
- **Modelo de Embedding**: BAAI/bge-m3, OpenAI Small/Large
- **Modelo de Chat**: GPT-4o, GPT-4o Mini, GPT-4, GPT-3.5 Turbo
- **Top K**: Número de documentos a recuperar (default: 10)
- **Temperatura**: Control de creatividad en respuestas (default: 0.1)

### Modelos por Defecto
- **Chat Model**: `gpt-4o`
- **Embedding Model**: `BAAI/bge-m3`
- **Top K**: `10`
- **Temperature**: `0.1`

## 🎨 Interfaz de Usuario

### Características de la UI
- **Diseño responsivo** que funciona en móvil y desktop
- **Tema adaptativo** (claro/oscuro)
- **Animaciones suaves** y transiciones
- **Iconografía moderna** con Lucide React
- **Tipografía optimizada** para legibilidad

### Componentes Principales
- Panel de chat con scroll automático
- Panel de configuración colapsable
- Indicadores de estado de conexión
- Indicador de carga durante respuestas
- Enlaces a fuentes consultadas

## 🔧 Comandos Útiles

### Git
```bash
git init
git add .
git commit -m "Descripción del commit"
git push -u origin main
git reset HEAD~1  # Revertir último commit
```

### Desarrollo
```bash
npm run dev          # Iniciar frontend
npm run build        # Construir para producción
npm run preview      # Vista previa de producción
npm run lint         # Linting del código
```

### Backend
```bash
flask --app main.py run --port=5001  # Ejecutar servidor
pip freeze > requirements.txt        # Actualizar dependencias
```

## 📁 Estructura del Proyecto

```
chatbotTFM/
├── src/
│   ├── components/ui/          # Componentes shadcn/ui
│   ├── App.jsx                 # Componente principal
│   ├── App.css                 # Estilos CSS
│   └── main.jsx                # Punto de entrada
├── main.py                     # Servidor Flask
├── rag_service.py              # Servicio RAG
├── requirements.txt            # Dependencias Python
├── package.json                # Dependencias Node.js
├── tailwind.config.js          # Configuración Tailwind
├── vite.config.js              # Configuración Vite
└── .env                        # Variables de entorno
```

## 🌐 Despliegue

### Vercel (Frontend)
- Conectado automáticamente con GitHub
- Despliegue automático en push a main

### Backend
- Configurado para ejecutarse en servidor con Flask
- Requiere 12GB RAM y 2 CPU mínimo

## 🔒 Seguridad

- Variables de entorno para API keys
- Validación de entrada en backend
- CORS configurado para frontend
- Sanitización de contenido markdown

## 📝 Notas de Desarrollo

- **Versión actual**: Beta funcional
- **Última actualización**: Diciembre 2024
- **Estado**: En desarrollo activo
- **Compatibilidad**: Chrome, Safari, Firefox, Edge


## 📄 Licencia

Este proyecto es parte del Trabajo de Fin de Máster (TFM) en Inteligencia Artificial - EAE Business School.

---

**Institución**: EAE Business School  
**Fecha**: Junio 2025

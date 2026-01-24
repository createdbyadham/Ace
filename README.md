# ACE - Automated Cognitive Education Platform

![ACE](./ACE.png)

## 🚀 Overview

**ACE** (Automated Cognitive Education) is an advanced AI-powered learning platform designed to revolutionize how students and professionals study. By combining **Retrieval-Augmented Generation (RAG)** for intelligent tutoring with **fine-tuned Large Language Models (LLMs)** for personalized content generation, ACE creates a comprehensive study ecosystem.

The platform automatically generates high-quality **Flashcards** and **Multiple Choice Questions (MCQs)** from your study materials (PDFs, Notes) and schedules reviews using a scientifically-backed **Spaced Repetition System (SRS)** based on the SM-2 algorithm.

## ✨ Key Features

### AI-Powered Content Generation
- **Fine-Tuned Llama 3 Integration**: Utilizes a custom fine-tuned model specifically optimized for educational content generation using Unsloth.
- **Smart Flashcards**: Automatically extracts key concepts and definitions from uploaded documents to create flashcards.
- **Dynamic MCQs**: Generates challenging multiple-choice questions with explanations to test deep understanding.

### Intelligent Tutor (RAG Chatbot)
- **Context-Aware Answers**: Chat with your PDF documents. The system retrieves relevant sections to answer questions accurately.
- **Vector Search**: Powered by **ChromaDB** and **Sentence Transformers** (`all-MiniLM-L6-v2`) for semantic understanding of your content.
- **Conversation Memory**: Maintains context across the chat session for a natural dialogue flow.

### Spaced Repetition System (SRS)
- **Optimized Learning**: Implements the **SM-2 Algorithm** to schedule reviews at the optimal time for memory retention.
- **Efficiency**: Minimizes study time while maximizing long-term recall.
- **Daily Dashboard**: Visualizes upcoming reviews and study progress.

### Modern Full-Stack Architecture
- **Responsive UI**: Built with **React**, **Vite**, and **Tailwind CSS**.
- **Component Library**: Features a polished UI using **shadcn/ui** and **Radix UI**.
- **State Management**: Robust data handling with **TanStack Query**.
- **Backend**: High-performance **FastAPI** server with asynchronous processing.
- **Database**: **PostgreSQL** (Supabase) for structured data and **ChromaDB** for vector embeddings.

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18, Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS, Framer Motion
- **Components**: shadcn/ui, Radix UI, Lucide React
- **State/Routing**: TanStack Query, TanStack Router, React Hook Form, Zod

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (via Supabase), SQLAlchemy (ORM), Alembic (Migrations)
- **Vector Store**: ChromaDB
- **ML/AI**: 
  - **PyTorch** & **Unsloth** (for local model inference)
  - **Sentence Transformers** (Embeddings)
  - **OpenAI/GitHub Models API** (Chatbot)
  - **LangChain** (Document processing)

## 🏗️ Architecture

1.  **Ingestion Pipeline**:
    -   User uploads PDF -> Text Extraction -> Chunking -> Embedding Generation -> ChromaDB Storage.
2.  **Generation Pipeline**:
    -   User requests Flashcards/MCQs -> Retrieval of relevant context -> Prompt Engineering -> Fine-tuned Ace Model Inference -> JSON Parsing -> Database Storage.
3.  **Review Pipeline**:
    -   Frontend requests due cards -> Backend queries SRS logic (SM-2) -> User reviews -> Feedback Loop updates card intervals.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL Database (or Supabase credentials)
- NVIDIA GPU (Optional, for local fine-tuned model inference)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/ace-platform.git
    cd ace-platform
    ```

2.  **Backend Setup**
    ```bash
    cd Backend
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r req.txt
    ```

3.  **Environment Variables**
    Create a `.env` file in `Backend/` with:
    ```env
    user=your_db_user
    password=your_db_password
    host=your_db_host
    port=5432
    dbname=your_db_name
    GITHUB_TOKEN=your_github_token
    LLM_ENDPOINT=https://models.inference.ai.azure.com
    LLM_MODEL=gpt-4o
    ```

4.  **Frontend Setup**
    ```bash
    cd Frontend
    npm install
    ```

### Running the Application

1.  **Start the Backend**
    ```bash
    # In Backend directory
    uvicorn main:app --reload
    ```

2.  **Start the Frontend**
    ```bash
    # In Frontend directory
    npm run dev
    ```

## 🔮 Future Improvements

- [ ] Mobile App (React Native)
- [ ] Collaborative Study Groups
- [ ] Voice Mode for Flashcards
- [ ] Integration with Notion/Obsidian

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

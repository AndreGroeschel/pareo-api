# Pareo API

Pareo API is a FastAPI-based backend service for matching startups with investors, leveraging Supabase for data storage and similarity search capabilities.

## 🚀 Features

- FastAPI-powered REST API
- Supabase integration for investor data management
- Similarity search for investor matching
- Built with modern Python tools (UV, Ruff, pre-commit)
- OpenAI integration for advanced matching capabilities

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **Python Version:** >=3.13
- **Package Management:** UV
- **Code Quality:** Ruff, pre-commit
- **Database:** Supabase
- **AI Integration:** OpenAI

## 📋 Prerequisites

- Python 3.13 or higher
- UV package manager
- Supabase account and project
- OpenAI API access

## 🔧 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AndreGroeschel/pareo-api.git
   cd pareo-api
   ```

2. Install dependencies using UV:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

4. Create a `.env` file in the project root:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   OPENAI_API_KEY=your_openai_api_key
   ```

## 🏃‍♂️ Running the API

1. Start the FastAPI server:
   ```bash
   uvicorn pareo_api.main:app --reload
   ```

2. Access the API documentation at:
   ```
   http://localhost:8000/docs
   ```

## 🧪 Testing

```bash
pytest
```

## 📦 Project Structure

```
pareo-api/
├── pareo_api/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   └── services/
├── tests/
├── .env
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
└── pyproject.toml
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 👥 Authors

- André Gröschel ([@AndreGroeschel](https://github.com/AndreGroeschel)) - andre@pareo.app

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- Supabase for the backend infrastructure
- OpenAI for AI capabilities

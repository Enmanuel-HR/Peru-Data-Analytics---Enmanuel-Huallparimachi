# 🇵🇪 GitHub Peru Data Analytics

A comprehensive end-to-end data analytics platform for the Peruvian developer ecosystem on GitHub. This project extracts, classifies, and visualizes data from top developers and repositories in Peru.

## 🚀 Overview

This platform uses a multi-stage ETL process to:
1. **Extract**: Search and retrieve data for hundreds of top developers located in Peru.
2. **Classify**: Use AI-driven categorization to assign repositories to specific industries (ISIC standards).
3. **Analyze**: Calculate impact scores, language diversity, and activity metrics.
4. **Visualize**: Present insights through a modern, multi-page Streamlit dashboard.

## ✨ Features

- **Developer Explorer**: Detailed metrics on developers (followers, total stars, impact score, primary languages).
- **Repository Browser**: Searchable view of the most impactful Peruvian repositories.
- **Industry Insights**: Distribution of tech projects across sectors like Finance, Education, Public Sector, and more.
- **Language Analytics**: Trends in programming language adoption and impact.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Enmanuel-HR/Peru-Data-Analytics---Enmanuel-Huallparimachi.git
   cd Peru-Data-Analytics---Enmanuel-Huallparimachi
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file based on `.env.example`:
   ```env
   GITHUB_TOKEN=your_github_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 📊 Usage

### Running the Dashboard
To view the analytics locally:
```bash
streamlit run app/main.py
```

### Running the ETL Process
To refresh the data from GitHub:
```bash
python src/full_etl.py
python src/export_data.py
```

## 📂 Project Structure

- `app/`: Multi-page Streamlit dashboard code.
- `src/`: Core ETL logic, database configuration, and metric calculators.
- `data/`: Processed data ready for visualization.
- `scripts/`: Utility scripts for data maintenance.

## 👨‍💻 Author

**Enmanuel Huallparimachi**
[GitHub Profile](https://github.com/Enmanuel-HR)

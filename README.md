## Brand Reputation Dashboard

Monitor a brand’s online reputation using news articles and Reddit posts.
Analyze sentiment, view trends, get AI-generated insights, and download reports.

---

### Features

* Get latest news and Reddit posts
* Sentiment analysis (positive, negative, neutral)
* Charts and word cloud
* AI summary with recommendations


---

### Requirements

* Python 3.8+
* API keys:

  * [NewsAPI](https://newsapi.org/)
  * [Groq AI](https://groq.com/)
  * [Reddit API (PRAW)](https://praw.readthedocs.io/)

---

### Setup

```bash
# Clone the project
git clone https://github.com/yourusername/brand-reputation-dashboard.git
cd brand-reputation-dashboard

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Add a `.env` file with your keys:

```
NEWS_API_KEY=your_news_api_key
GROQ_API_KEY=your_groq_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

---

### Run

```bash
streamlit run app.py
```

---

### Output

* Key metrics
* Sentiment charts
* Word cloud
* Top 5 news & Reddit posts
* AI-generated insight



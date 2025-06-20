import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import praw

# Loading keys
load_dotenv()
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')

groq_client = Groq(api_key=GROQ_API_KEY)
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent="BrandReputationDashboard"
)

# fetching news
def get_brand_news(brand, start_date, end_date, max_articles=50):
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': brand,
        'from': start_date.strftime('%Y-%m-%d'),
        'to': end_date.strftime('%Y-%m-%d'),
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': max_articles,
        'apiKey': NEWS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    articles = []
    if 'articles' in data:
        for a in data['articles']:
            articles.append({
                'title': a.get('title', ''),
                'description': a.get('description', ''),
                'publishedAt': a.get('publishedAt', ''),
                'url': a.get('url', ''),
                'source': a.get('source', {}).get('name', '')
            })
    return articles

# fetching reddit
def get_reddit_posts(brand, limit=20):
    posts = []
    try:
        for submission in reddit.subreddit("all").search(brand, limit=limit, sort='new'):
            posts.append({
                'title': submission.title or '',
                'description': submission.selftext or '',
                'publishedAt': datetime.fromtimestamp(submission.created_utc).isoformat(),
                'url': submission.url,
                'source': submission.subreddit.display_name
            })
    except Exception as e:
        st.warning(f"Reddit API error: {e}")
    return posts

# sentiment
def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return 'Positive', polarity
    elif polarity < -0.1:
        return 'Negative', polarity
    else:
        return 'Neutral', polarity

# groq insight
def get_groq_summary(brand, avg_news, avg_reddit, pos_news, neg_news, pos_reddit, neg_reddit):
    prompt = f"""
    Brand: {brand}

    NEWS:
    Avg Sentiment: {avg_news:.2f}
    Positive: {pos_news}, Negative: {neg_news}

    REDDIT:
    Avg Sentiment: {avg_reddit:.2f}
    Positive: {pos_reddit}, Negative: {neg_reddit}

    Provide a clear, concise insight & recommendations.
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq error: {e}"


# main app
def main():
    st.set_page_config("Brand Reputation Dashboard", "📊", layout="wide")
    st.title("📊 Brand Reputation Dashboard")
    st.caption("Powered by NewsAPI, Reddit & Groq AI")

    with st.sidebar:
        st.header("🔍 Brand Settings")
        brand = st.text_input("Brand", "Nike")
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        end_date = st.date_input("End Date", datetime.now())
        max_articles = st.slider("Max News Articles", 10, 100, 50)
        max_reddit = st.slider("Max Reddit Posts", 10, 50, 20)
        go = st.button("🔎 Analyze")

    if not (NEWS_API_KEY and GROQ_API_KEY and REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET):
        st.error("Missing keys in .env file.")
        return

    if go:
        with st.spinner(f"Fetching data for '{brand}'..."):
            news = get_brand_news(brand, start_date, end_date, max_articles)
            reddit_posts = get_reddit_posts(brand, max_reddit)

        if not news and not reddit_posts:
            st.warning("No results found.")
            return

        for a in news:
            sentiment, score = analyze_sentiment(f"{a['title']} {a['description']}")
            a['sentiment'] = sentiment
            a['score'] = score
            a['date'] = pd.to_datetime(a['publishedAt'], errors='coerce').date()

        for p in reddit_posts:
            sentiment, score = analyze_sentiment(f"{p['title']} {p['description']}")
            p['sentiment'] = sentiment
            p['score'] = score
            p['date'] = pd.to_datetime(p['publishedAt'], errors='coerce').date()

        df_news = pd.DataFrame(news)
        df_reddit = pd.DataFrame(reddit_posts)

        # metrics
        pos_news, neg_news, avg_news = 0, 0, 0
        pos_reddit, neg_reddit, avg_reddit = 0, 0, 0

        if not df_news.empty:
            pos_news = (df_news['sentiment'] == 'Positive').sum()
            neg_news = (df_news['sentiment'] == 'Negative').sum()
            avg_news = df_news['score'].mean()

        if not df_reddit.empty:
            pos_reddit = (df_reddit['sentiment'] == 'Positive').sum()
            neg_reddit = (df_reddit['sentiment'] == 'Negative').sum()
            avg_reddit = df_reddit['score'].mean()

        st.markdown("## 📈 Metrics")
        cols = st.columns(6)
        cols[0].metric("Avg News", f"{avg_news:.2f}")
        cols[1].metric("Pos News", pos_news)
        cols[2].metric("Neg News", neg_news)
        cols[3].metric("Avg Reddit", f"{avg_reddit:.2f}")
        cols[4].metric("Pos Reddit", pos_reddit)
        cols[5].metric("Neg Reddit", neg_reddit)

        st.markdown("---")
        st.markdown("## 📊 Visuals")

        if not df_news.empty:
            news_counts = df_news['sentiment'].value_counts().rename_axis('sentiment').reset_index(name='count')
            pie_news = px.pie(news_counts, names='sentiment', values='count', title="News Sentiment")
            st.plotly_chart(pie_news, use_container_width=True)

        if not df_reddit.empty:
            reddit_counts = df_reddit['sentiment'].value_counts().rename_axis('sentiment').reset_index(name='count')
            pie_reddit = px.pie(reddit_counts, names='sentiment', values='count', title="Reddit Sentiment")
            st.plotly_chart(pie_reddit, use_container_width=True)

        trend_news = df_news.groupby('date')['score'].mean().reset_index()
        if not trend_news.empty:
            st.plotly_chart(px.line(trend_news, x='date', y='score', markers=True, title="News Sentiment Over Time"),
                            use_container_width=True)

        all_text = " ".join(
            (df_news['title'].fillna('') + " " + df_news['description'].fillna('')).tolist() +
            (df_reddit['title'].fillna('') + " " + df_reddit['description'].fillna('')).tolist()
        )
        try:
            wc = WordCloud(width=800, height=400, background_color='white').generate(all_text)
            st.markdown("## 🗂️ Word Cloud")
            fig_wc, ax_wc = plt.subplots()
            ax_wc.imshow(wc, interpolation='bilinear')
            ax_wc.axis('off')
            st.pyplot(fig_wc)
        except:
            st.warning("Could not create word cloud.")

        st.markdown("## 📰 Top 5 Posts")
        df_news['platform'] = 'News'
        df_reddit['platform'] = 'Reddit'
        df_combined = pd.concat([df_news, df_reddit]).sort_values(by='score', ascending=False)

        for _, row in df_combined.head(5).iterrows():
            icon = {"Positive": "✅", "Negative": "⚠️", "Neutral": "➖"}
            short_title = row['title'][:100] + "..." if len(row['title']) > 100 else row['title']
            st.write(f"### {icon[row['sentiment']]} [{row['platform']}] [{short_title}]({row['url']})")
            with st.expander("Show details"):
                st.write(f"**Full Title:** {row['title']}")
                st.write(f"**Full Description:** {row['description']}")
                st.write(f"Sentiment: `{row['sentiment']} ({row['score']:.2f})`")
            st.caption(f"Published: {row['date']} | Source: {row['source']}")
            st.markdown("---")

        st.markdown("## 🤖 AI Insight")
        with st.spinner("Analyzing..."):
            ai = get_groq_summary(brand, avg_news, avg_reddit, pos_news, neg_news, pos_reddit, neg_reddit)
            st.success(ai)


if __name__ == "__main__":
    main()

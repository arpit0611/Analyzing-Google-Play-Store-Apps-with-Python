"""Clean the historical Google Play Store dataset and produce visualizations."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px

ROOT = Path(__file__).resolve().parent
from src.cleaning import clean_google_play


def main():
    source = ROOT / 'data/raw/googleplaystore.csv'
    if not source.exists():
        raise SystemExit('Source dataset not found. Run: python download_data.py')
    charts = ROOT / 'charts'
    charts.mkdir(exist_ok=True)
    processed = ROOT / 'data/processed'
    processed.mkdir(exist_ok=True)
    raw = pd.read_csv(source)
    df, audit = clean_google_play(raw)
    if df.empty:
        raise SystemExit('No usable app records after cleaning')
    df.to_csv(processed/'googleplaystore_cleaned.csv',index=False)

    # Chart 1: categories with the most apps
    count=df['Category'].value_counts().head(12).sort_values()
    fig,ax=plt.subplots(figsize=(10,6))
    count.plot(kind='barh',ax=ax,color='#0f766e')
    ax.set(title='Top 12 App Categories by Listing Count',xlabel='Number of apps',ylabel='')
    ax.grid(axis='x',alpha=.15)
    fig.tight_layout(); fig.savefig(charts/'01_top_categories.png',dpi=160);plt.close(fig)

    # Chart 2: free versus paid
    types=df['Type'].value_counts().reindex(['Free','Paid'],fill_value=0)
    fig,ax=plt.subplots(figsize=(6.2,5.2))
    ax.pie(types,labels=types.index,autopct='%1.1f%%',startangle=90,
           colors=['#0f766e','#e09f3e'],wedgeprops={'width':0.46})
    ax.set_title('Free vs Paid App Listings')
    fig.tight_layout();fig.savefig(charts/'02_free_vs_paid.png',dpi=160);plt.close(fig)

    # Chart 3: content ratings
    counts=df['Content Rating'].fillna('Unknown').value_counts().head(8).sort_values()
    fig,ax=plt.subplots(figsize=(9,5.2))
    counts.plot(kind='barh',ax=ax,color='#2563eb')
    ax.set(title='App Listings by Content Rating',xlabel='App count',ylabel='')
    ax.grid(axis='x',alpha=.15)
    fig.tight_layout();fig.savefig(charts/'03_content_ratings.png',dpi=160);plt.close(fig)

    # Chart 4: user rating distribution (only non-missing ratings)
    fig,ax=plt.subplots(figsize=(9,5.2))
    ax.hist(df['Rating'].dropna(),bins=np.arange(1,5.2,.2),color='#7c3aed',edgecolor='white')
    ax.set(title='Distribution of App Ratings',xlabel='Google Play star rating',ylabel='App count',xlim=(1,5))
    ax.grid(axis='y',alpha=.15)
    fig.tight_layout();fig.savefig(charts/'04_rating_distribution.png',dpi=160);plt.close(fig)

    # Chart 5: median install threshold by category, sorted after groups >= 30 apps
    category_stats=df.groupby('Category').agg(apps=('App','count'),median_install_floor=('Installs_lower_bound','median'))
    med=category_stats.query('apps >= 30')['median_install_floor'].dropna().nlargest(10).sort_values()
    fig,ax=plt.subplots(figsize=(10,5.7))
    med.plot(kind='barh',ax=ax,color='#e09f3e')
    ax.set(title='Median Reported Install Threshold, by Category',xlabel='Reported install lower bound (not exact downloads)',ylabel='')
    ax.grid(axis='x',alpha=.15)
    fig.tight_layout();fig.savefig(charts/'05_median_install_threshold.png',dpi=160);plt.close(fig)

    # Interactive relationships
    tmp=df.dropna(subset=['Size_MB','Rating','Reviews_num']).copy()
    tmp=tmp.loc[tmp['Reviews_num']>0]
    fig=px.scatter(tmp, x='Size_MB', y='Rating', color='Type',hover_name='App',
            hover_data=['Category','Reviews_num'],opacity=0.5,
            title='App Size vs Rating (hover for app details)',labels={'Size_MB':'App Size (MB)','Rating':'Star rating'})
    fig.write_html(charts/'06_size_vs_rating_interactive.html',include_plotlyjs="cdn")

    price_df=df[(df['Type']=='Paid') & df['Price_usd'].gt(0) & df['Rating'].notna()].copy()
    if len(price_df):
        fig=px.scatter(price_df,x='Price_usd',y='Rating',hover_name='App',color='Category',
            opacity=.65,log_x=True,title='Paid App Price vs Rating (log price axis)',
            labels={'Price_usd':'Listed price (USD)','Rating':'Star rating'})
        fig.write_html(charts/'07_paid_price_vs_rating_interactive.html',include_plotlyjs="cdn")
    rated=df.dropna(subset=['Rating']).copy()
    fig=px.box(rated,x='Type',y='Rating',color='Type',points='outliers',
           title='App Rating Distribution: Free vs Paid',labels={'Rating':'Star rating','Type':'App type'})
    fig.write_html(charts/'08_free_vs_paid_ratings_boxplot.html',include_plotlyjs="cdn")

    rated = df.dropna(subset=['Rating'])
    top_category = df['Category'].value_counts().idxmax()
    print('Historical Google Play Store sample (~2018)')
    print('Cleaning summary:', audit)
    print('Apps analyzed:',len(df))
    print('Most represented category:',top_category)
    print('Share of free listings: {:.1f}%'.format(100*types['Free']/len(df)))
    print('Average recorded star rating: {:.2f}'.format(rated['Rating'].mean()))
    print('Visualizations saved to:',charts)


if __name__ == '__main__':
    main()

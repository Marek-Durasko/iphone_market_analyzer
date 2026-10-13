import csv
import logging
import argparse
from pathlib import Path
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt

from analysis_utils import extract_model_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_data(csv_file):
    """Analyze the scraped data and generate insights."""
    logger.info(f"Loading data from {csv_file}")

    try:
        df = pd.read_csv(csv_file, delimiter=';', encoding='utf-8-sig')
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return None

    logger.info(f"Loaded {len(df)} listings")

    # Convert numeric price to proper type
    df['Čisté číslo'] = pd.to_numeric(df['Čisté číslo'], errors='coerce')
    df = df.dropna(subset=['Čisté číslo'])

    # Extract model names
    df['Model'] = df['Produkt'].apply(extract_model_name)

    # Basic statistics
    logger.info("\n=== DATA ANALYSIS ===")
    logger.info(f"Total listings: {len(df)}")
    logger.info(f"Average price: €{df['Čisté číslo'].mean():.2f}")
    logger.info(f"Median price: €{df['Čisté číslo'].median():.2f}")
    logger.info(f"Min price: €{df['Čisté číslo'].min():.2f}")
    logger.info(f"Max price: €{df['Čisté číslo'].max():.2f}")
    logger.info(f"Price std: €{df['Čisté číslo'].std():.2f}")

    # Model distribution
    model_counts = df['Model'].value_counts()
    logger.info(f"\nTop 5 most common models:")
    for model, count in model_counts.head(5).items():
        logger.info(f"  {model}: {count} listings")

    # Price by model
    logger.info(f"\nAverage price by model:")
    model_prices = df.groupby('Model')['Čisté číslo'].agg(['mean', 'count'])
    model_prices = model_prices[model_prices['count'] >= 3]  # Only models with 3+ listings
    model_prices = model_prices.sort_values('mean', ascending=False)
    for model, row in model_prices.head(5).iterrows():
        logger.info(f"  {model}: €{row['mean']:.2f} ({int(row['count'])} listings)")

    return df


def create_visualizations(df, output_dir='charts'):
    """Create and save visualization charts."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    logger.info(f"\n=== CREATING VISUALIZATIONS ===")

    # 1. Price distribution histogram
    plt.figure(figsize=(10, 6))
    plt.hist(df['Čisté číslo'], bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel('Price (€)')
    plt.ylabel('Frequency')
    plt.title('Price Distribution of iPhone Listings')
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path / 'price_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {output_path / 'price_distribution.png'}")

    # 2. Average price by model (bar chart)
    model_prices = df.groupby('Model')['Čisté číslo'].agg(['mean', 'count'])
    model_prices = model_prices[model_prices['count'] >= 3]  # Only models with 3+ listings
    model_prices = model_prices.sort_values('mean', ascending=True).tail(10)

    plt.figure(figsize=(12, 6))
    model_prices['mean'].plot(kind='barh', color='steelblue', edgecolor='black')
    plt.xlabel('Average Price (€)')
    plt.ylabel('Model')
    plt.title('Average Price by iPhone Model (3+ listings)')
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(output_path / 'price_by_model.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {output_path / 'price_by_model.png'}")

    # 3. Number of listings by model
    model_counts = df['Model'].value_counts().head(10)

    plt.figure(figsize=(12, 6))
    model_counts.plot(kind='bar', color='coral', edgecolor='black')
    plt.xlabel('Model')
    plt.ylabel('Number of Listings')
    plt.title('Number of Listings by iPhone Model (Top 10)')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path / 'listings_by_model.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {output_path / 'listings_by_model.png'}")

    logger.info(f"\nAll charts saved to {output_path}/")


def main():
    parser = argparse.ArgumentParser(description='Analyze iPhone price data')
    parser.add_argument('--input', default='bazos_produkty.csv', help='Input CSV file')
    parser.add_argument('--output-dir', default='charts', help='Output directory for charts')
    args = parser.parse_args()

    if not Path(args.input).exists():
        logger.error(f"Input file {args.input} not found. Run the scraper first.")
        return

    df = analyze_data(args.input)
    if df is not None:
        create_visualizations(df, args.output_dir)
        logger.info("\nAnalysis complete!")


if __name__ == "__main__":
    main()

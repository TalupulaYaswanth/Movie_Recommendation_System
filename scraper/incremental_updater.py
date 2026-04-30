from .vortex_scraper import scrape_pages
import pandas as pd
import os

def run_incremental_update(max_pages=1):
    """
    Runs the scraper for a limited number of pages and then 
    deduplicates the resulting CSV to ensure no redundant entries.
    """
    print(f"Starting incremental update for {max_pages} pages...")
    scrape_pages(max_pages=max_pages)
    
    # Post-process: Deduplicate the CSV
    csv_path = os.path.join(os.path.dirname(__file__), "vortex_data.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            initial_len = len(df)
            # Deduplicate based on Movie Link or Title
            df = df.drop_duplicates(subset=['Movie Link'], keep='first')
            df = df.drop_duplicates(subset=['Title'], keep='first')
            df.to_csv(csv_path, index=False)
            print(f"Incremental Update Complete. Deduplicated: {initial_len} -> {len(df)} movies.")
        except Exception as e:
            print(f"Error during deduplication: {e}")
    else:
        print("Scraper finished but CSV not found for deduplication.")

if __name__ == "__main__":
    run_incremental_update(1)

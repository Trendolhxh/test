#!/usr/bin/env python3
"""Parse Trustpilot reviews from raw text files and output CSV."""
import csv
import re
import os
import glob

def parse_reviews(text):
    """Parse REVIEW_START/REVIEW_END blocks from text."""
    reviews = []
    blocks = re.split(r'REVIEW_START\s*\n', text)
    for block in blocks[1:]:  # skip first empty split
        end_idx = block.find('REVIEW_END')
        if end_idx == -1:
            continue
        block = block[:end_idx].strip()

        name = rating = title = review_text = date = ''

        # Parse fields
        name_m = re.search(r'^Name:\s*(.+)', block, re.MULTILINE)
        rating_m = re.search(r'^Rating:\s*(\d)', block, re.MULTILINE)
        title_m = re.search(r'^Title:\s*(.+)', block, re.MULTILINE)
        date_m = re.search(r'^Date:\s*(.+)', block, re.MULTILINE)

        if name_m:
            name = name_m.group(1).strip()
        if rating_m:
            rating = rating_m.group(1).strip()
        if title_m:
            title = title_m.group(1).strip()
        if date_m:
            date = date_m.group(1).strip()
            # Normalize date format
            date = re.sub(r'T[\d:.]+Z?$', '', date)  # Remove time portion
            # Convert "Mar 11, 2026" format to "2026-03-11"
            months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',
                      'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
            m = re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d+),?\s+(\d{4})', date)
            if m:
                date = f"{m.group(3)}-{months[m.group(1)]}-{int(m.group(2)):02d}"

        # Extract text - everything between Title line and Date line
        text_m = re.search(r'^Text:\s*(.*?)(?=\n(?:Date:|REVIEW_END)|\Z)', block, re.MULTILINE | re.DOTALL)
        if text_m:
            review_text = text_m.group(1).strip()

        if name or title:  # Must have at least name or title
            reviews.append({
                'name': name,
                'rating': rating,
                'title': title,
                'text': review_text,
                'date': date
            })

    return reviews

def deduplicate(reviews):
    """Remove duplicate reviews based on name+title combination."""
    seen = set()
    unique = []
    for r in reviews:
        key = (r['name'].lower().strip(), r['title'].lower().strip()[:50])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

def main():
    all_reviews = []

    # Read all raw data files
    data_dir = '/home/user/test/raw_reviews'
    if os.path.isdir(data_dir):
        for filepath in sorted(glob.glob(os.path.join(data_dir, '*.txt'))):
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            reviews = parse_reviews(text)
            all_reviews.extend(reviews)
            print(f"  {os.path.basename(filepath)}: {len(reviews)} reviews")

    print(f"\nTotal raw reviews parsed: {len(all_reviews)}")

    # Deduplicate
    unique_reviews = deduplicate(all_reviews)
    print(f"Unique reviews after dedup: {len(unique_reviews)}")

    # Sort by date descending
    unique_reviews.sort(key=lambda r: r['date'], reverse=True)

    # Write CSV
    output_path = '/home/user/test/eightsleep_trustpilot_reviews.csv'
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'rating', 'title', 'text', 'date'])
        writer.writeheader()
        writer.writerows(unique_reviews)

    print(f"\nCSV written to: {output_path}")
    print(f"Total reviews in CSV: {len(unique_reviews)}")

if __name__ == '__main__':
    main()

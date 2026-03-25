#!/usr/bin/env python3
"""Generate index.html showcase page for OfekTech Cycle B accepted candidates."""

import csv
import html
import re

# ---- Configuration ----

ACCEPTED_CSV = '/tmp/masa-accepted.csv'
SOURCE_CSV = '/tmp/masa-source.csv'
FORM_CSV = '/tmp/masa-form-responses.csv'

# The 18 accepted candidates with display names and matching hints
ACCEPTED_NAMES = [
    "עדן בועז מימון",
    "יצחק ליאור",
    "דניאל בן צור",
    "מולוגטה דוד טגניה",
    "עידו חן",
    "רן עוקשי",
    "תומר זילברשטיין",
    "ירין חמדאן",
    "עידו אורייה יוסף",
    "ליאל דבח ורועי חלמיש",
    "נתנאל כהן",
    "אמיר גבאי-טוטחאזן",
    "ידידיה רבינוביץ",
    "יואב פרידמן",
    "עמית בן שטרית",
    "אורי גרשוני",
    "מתן לביא",
    "גיא סוקולצקי",
]

DISPLAY_NAMES = {
    "מולוגטה דוד טגניה": "דוד טגניה",
}

# For candidates with multiple submissions, specify which one to use
# by matching a keyword in the problem field
SUBMISSION_SELECTOR = {
    "מתן לביא": "תרגול מתמטי",       # first submission about adaptive math
    "ירין חמדאן": "נפילות",             # smart walking stick submission
    "רן עוקשי": "כלכלי",               # financial AI app
    "ידידיה רבינוביץ": "מיון עובדים",   # job platform for youth (second submission)
}


def esc(s):
    """HTML-escape a string."""
    if not s:
        return ""
    return html.escape(s.strip())


def nl2br(s):
    """Convert newlines to <br> for HTML display."""
    if not s:
        return ""
    return html.escape(s.strip()).replace('\n', '<br>')


def normalize_name(name):
    """Strip whitespace and normalize for matching."""
    return name.strip()


def name_matches(csv_name, accepted_name):
    """Check if a CSV name matches an accepted candidate name."""
    csv_n = normalize_name(csv_name)
    acc_n = normalize_name(accepted_name)
    # Direct match
    if csv_n == acc_n:
        return True
    # Partial match (e.g. "ליאל דבח" in "ליאל דבח ורועי חלמיש")
    if csv_n in acc_n or acc_n in csv_n:
        return True
    # Strip trailing/leading spaces and try again
    csv_clean = csv_n.replace('\u200f', '').replace('\u200e', '').strip()
    acc_clean = acc_n.replace('\u200f', '').replace('\u200e', '').strip()
    if csv_clean in acc_clean or acc_clean in csv_clean:
        return True
    return False


def read_accepted():
    """Read accepted candidates CSV."""
    candidates = {}
    with open(ACCEPTED_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip title row
        header = next(reader)  # number, name, phone, email, venture, mentor, mentor2, city, presentation_link
        for row in reader:
            if len(row) < 2 or not row[1].strip():
                continue
            # Stop at mentors section
            if 'מנטורים' in row[0]:
                break
            name = row[1].strip()
            if name not in ACCEPTED_NAMES:
                continue
            candidates[name] = {
                'number': row[0].strip() if row[0].strip() else '',
                'name': name,
                'display_name': DISPLAY_NAMES.get(name, name),
                'phone': row[2].strip() if len(row) > 2 else '',
                'email': row[3].strip() if len(row) > 3 else '',
                'venture': row[4].strip() if len(row) > 4 else '',
                'mentor': row[5].strip() if len(row) > 5 else '',
                'mentor2': row[6].strip() if len(row) > 6 else '',
                'city': row[7].strip() if len(row) > 7 else '',
                'presentation_link': row[8].strip() if len(row) > 8 else '',
                'background': '',
                'problem': '',
                'solution': '',
                'tech': '',
                'cohort': '',
            }
    return candidates


def read_source(candidates):
    """Read source CSV and match form data to candidates."""
    with open(SOURCE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        # Columns: date, time, name, phone, email, city, background, problem, solution, tech, mentor
        for row in reader:
            if len(row) < 10:
                continue
            csv_name = row[2].strip()
            for acc_name, cand in candidates.items():
                if not name_matches(csv_name, acc_name):
                    continue
                # Check if this candidate has a submission selector
                selector = SUBMISSION_SELECTOR.get(acc_name)
                if selector:
                    # Only use this row if it matches the selector keyword
                    if selector not in row[7] and selector not in row[8]:
                        continue
                # If already filled and no selector, use first match (with time = scheduled slot)
                if cand['background'] and not selector:
                    continue
                cand['background'] = row[6].strip()
                cand['problem'] = row[7].strip()
                cand['solution'] = row[8].strip()
                cand['tech'] = row[9].strip()
                break


def read_cohort(candidates):
    """Read form responses CSV for cohort data."""
    with open(FORM_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        # Column 5 (index 5) has cohort info
        for row in reader:
            if len(row) < 6:
                continue
            csv_name = row[1].strip()
            for acc_name, cand in candidates.items():
                if not name_matches(csv_name, acc_name):
                    continue
                cohort = row[5].strip() if row[5].strip() and row[5].strip() != '.' else ''
                if cohort and not cand['cohort']:
                    cand['cohort'] = cohort
                    break


def generate_summary(cand):
    """Generate a short summary for the card view from the problem field."""
    problem = cand.get('problem', '')
    if not problem:
        return cand.get('venture', '')
    # Take first sentence or first 120 chars
    sentences = re.split(r'[.!?।,]', problem)
    summary = sentences[0].strip() if sentences else problem[:120]
    if len(summary) > 150:
        summary = summary[:147] + '...'
    return summary


def generate_html(candidates):
    """Generate the full HTML page."""
    # Order candidates by the ACCEPTED_NAMES list
    ordered = []
    for name in ACCEPTED_NAMES:
        if name in candidates:
            ordered.append(candidates[name])

    cards_html = ""
    details_html = ""

    for i, cand in enumerate(ordered):
        cid = f"candidate-{i}"
        display_name = esc(cand['display_name'])
        venture = esc(cand['venture'])
        city = esc(cand['city'])
        cohort = esc(cand['cohort'])
        summary = esc(generate_summary(cand))
        background = nl2br(cand['background'])
        problem = nl2br(cand['problem'])
        solution = nl2br(cand['solution'])
        tech = nl2br(cand['tech'])
        pres_link = cand['presentation_link']

        # Card
        cards_html += f'''
        <div class="card" onclick="showDetail('{cid}')">
            <div class="card-header">
                <h3>{display_name}</h3>
            </div>
            <div class="card-body">
                <div class="venture-title">{venture if venture else '—'}</div>
                <div class="card-city">{city}</div>
                <p class="card-summary">{summary}</p>
            </div>
            <div class="card-footer">
                <span class="view-more">לפרטים נוספים &larr;</span>
            </div>
        </div>
'''

        # Presentation button
        pres_btn = ""
        if pres_link:
            pres_btn = f'<a href="{esc(pres_link)}" target="_blank" rel="noopener" class="pres-btn">צפה במצגת</a>'

        # Detail view
        details_html += f'''
        <div id="{cid}" class="detail-view" style="display:none;">
            <button class="back-btn" onclick="hideDetail('{cid}')">&rarr; חזרה לרשימה</button>
            <div class="detail-card">
                <h2>{display_name}</h2>
                <div class="detail-meta">
                    <span class="meta-item"><strong>עיר:</strong> {city}</span>
                    {f'<span class="meta-item"><strong>מחזור מסע:</strong> {cohort}</span>' if cohort else ''}
                </div>
                <div class="detail-venture">
                    <h3>{venture if venture else '—'}</h3>
                </div>
                {f"""
                <div class="detail-section">
                    <h4>רקע</h4>
                    <p>{background}</p>
                </div>
                """ if background else ""}
                {f"""
                <div class="detail-section">
                    <h4>הבעיה</h4>
                    <p>{problem}</p>
                </div>
                """ if problem else ""}
                {f"""
                <div class="detail-section">
                    <h4>הפתרון</h4>
                    <p>{solution}</p>
                </div>
                """ if solution else ""}
                {f"""
                <div class="detail-section">
                    <h4>היבט טכנולוגי</h4>
                    <p>{tech}</p>
                </div>
                """ if tech else ""}
                {pres_btn}
            </div>
        </div>
'''

    page = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>אופק טק — יזמי מחזור ב׳</title>
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Heebo', sans-serif;
            background: #f0f4f8;
            color: #1e293b;
            line-height: 1.7;
        }}
        header {{
            background: linear-gradient(135deg, #1a4a5e 0%, #0f2d3a 100%);
            color: white;
            padding: 2.5rem 1rem;
            text-align: center;
        }}
        header h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }}
        header h1 span {{
            color: #22c55e;
        }}
        header p {{
            font-size: 1.1rem;
            opacity: 0.85;
            font-weight: 300;
        }}
        .count-badge {{
            display: inline-block;
            background: #22c55e;
            color: #0f2d3a;
            font-weight: 600;
            padding: 0.25rem 1rem;
            border-radius: 20px;
            margin-top: 0.8rem;
            font-size: 0.95rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            flex-direction: column;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }}
        .card-header {{
            background: #1a4a5e;
            color: white;
            padding: 1rem 1.2rem;
        }}
        .card-header h3 {{
            font-size: 1.2rem;
            font-weight: 600;
        }}
        .card-body {{
            padding: 1rem 1.2rem;
            flex: 1;
        }}
        .venture-title {{
            color: #1a4a5e;
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
            line-height: 1.5;
        }}
        .card-city {{
            color: #64748b;
            font-size: 0.85rem;
            margin-bottom: 0.6rem;
        }}
        .card-summary {{
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.6;
        }}
        .card-footer {{
            padding: 0.8rem 1.2rem;
            border-top: 1px solid #e2e8f0;
            text-align: left;
        }}
        .view-more {{
            color: #22c55e;
            font-weight: 500;
            font-size: 0.9rem;
        }}
        /* Detail view */
        .detail-view {{
            padding-bottom: 2rem;
        }}
        .back-btn {{
            background: none;
            border: 2px solid #1a4a5e;
            color: #1a4a5e;
            padding: 0.5rem 1.2rem;
            border-radius: 8px;
            font-family: 'Heebo', sans-serif;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            margin-bottom: 1.5rem;
            transition: background 0.2s, color 0.2s;
        }}
        .back-btn:hover {{
            background: #1a4a5e;
            color: white;
        }}
        .detail-card {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}
        .detail-card h2 {{
            font-size: 1.8rem;
            color: #1a4a5e;
            margin-bottom: 0.8rem;
        }}
        .detail-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
            margin-bottom: 1.2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #e2e8f0;
        }}
        .meta-item {{
            font-size: 0.95rem;
            color: #475569;
        }}
        .meta-item strong {{
            color: #1a4a5e;
        }}
        .detail-venture {{
            margin-bottom: 1.5rem;
        }}
        .detail-venture h3 {{
            font-size: 1.2rem;
            color: #1a4a5e;
            background: #f0fdf4;
            border-right: 4px solid #22c55e;
            padding: 0.8rem 1rem;
            border-radius: 0 8px 8px 0;
        }}
        .detail-section {{
            margin-bottom: 1.5rem;
        }}
        .detail-section h4 {{
            font-size: 1.05rem;
            color: #1a4a5e;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}
        .detail-section p {{
            color: #475569;
            font-size: 0.95rem;
            line-height: 1.8;
        }}
        .pres-btn {{
            display: inline-block;
            background: #22c55e;
            color: white;
            text-decoration: none;
            padding: 0.7rem 1.8rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            margin-top: 1rem;
            transition: background 0.2s;
        }}
        .pres-btn:hover {{
            background: #16a34a;
        }}
        @media (max-width: 640px) {{
            header h1 {{
                font-size: 1.6rem;
            }}
            header p {{
                font-size: 0.95rem;
            }}
            .grid {{
                grid-template-columns: 1fr;
            }}
            .detail-card {{
                padding: 1.2rem;
            }}
            .detail-card h2 {{
                font-size: 1.4rem;
            }}
            .detail-meta {{
                flex-direction: column;
                gap: 0.5rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1><span>אופק טק</span> — יזמי מחזור ב׳</h1>
        <p>תוכנית האקסלרציה של מסע אל האופק</p>
        <div class="count-badge">{len(ordered)} יזמים ויזמות</div>
    </header>
    <div class="container">
        <div id="grid-view" class="grid">
            {cards_html}
        </div>
        {details_html}
    </div>
    <script>
        function showDetail(id) {{
            document.getElementById('grid-view').style.display = 'none';
            document.getElementById(id).style.display = 'block';
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        function hideDetail(id) {{
            document.getElementById(id).style.display = 'none';
            document.getElementById('grid-view').style.display = 'grid';
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
    </script>
</body>
</html>
'''
    return page


def main():
    candidates = read_accepted()
    print(f"Loaded {len(candidates)} accepted candidates")

    read_source(candidates)
    read_cohort(candidates)

    # Check data quality
    for name, cand in candidates.items():
        missing = []
        if not cand['background']:
            missing.append('background')
        if not cand['problem']:
            missing.append('problem')
        if not cand['cohort']:
            missing.append('cohort')
        if missing:
            print(f"  Warning: {name} missing: {', '.join(missing)}")

    html_content = generate_html(candidates)
    output_path = '/tmp/masa-candidates/index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\nGenerated {output_path}")
    print(f"Total candidates: {len(candidates)}")


if __name__ == '__main__':
    main()

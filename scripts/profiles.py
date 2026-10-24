"""Generate the university research profiles served by PrepSavvy."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPARTMENTS = [
 ('oxford', 'Oxford', 'https://www.philosophy.ox.ac.uk/'),
 ('uc-irvine', 'UC Irvine', 'https://www.humanities.uci.edu/philosophy'),
 ('cambridge', 'Cambridge', 'https://www.phil.cam.ac.uk/'),
 ('nyu', 'NYU', 'https://as.nyu.edu/departments/philosophy.html'),
 ('edinburgh', 'Edinburgh', 'https://philosophy.ed.ac.uk/'),
 ('glasgow', 'Glasgow', 'https://www.gla.ac.uk/schools/humanities/subjects/philosophy/'),
 ('rutgers', 'Rutgers', 'https://philosophy.rutgers.edu/'),
 ('princeton', 'Princeton', 'https://philosophy.princeton.edu/'),
 ('geneva', 'Geneva', 'https://www.unige.ch/lettres/philo/'),
 ('macquarie', 'Macquarie', 'https://www.mq.edu.au/faculty-of-arts/schools/school-of-humanities'),
 ('groningen', 'Groningen', 'https://www.rug.nl/filosofie/?lang=en'),
 ('australian-national-university', 'Australian National University', 'https://philosophy.cass.anu.edu.au/'),
 ('ruhr-bochum', 'Ruhr University Bochum', 'https://www.philosophie.ruhr-uni-bochum.de/'),
 ('kings-college-london', 'King’s College London', 'https://www.kcl.ac.uk/philosophy'),
 ('southampton', 'Southampton', 'https://www.southampton.ac.uk/about/faculties-schools-departments/philosophy'),
 ('mit', 'MIT', 'https://philosophy.mit.edu/'),
 ('amsterdam', 'Amsterdam', 'https://www.uva.nl/en/discipline/philosophy/philosophy.html'),
 ('helsinki', 'Helsinki', 'https://www.helsinki.fi/en/faculty-humanities/research/disciplines/philosophy-history-and-art/philosophy'),
 ('st-andrews', 'St Andrews', 'https://www.st-andrews.ac.uk/philosophy/'),
 ('usc', 'USC', 'https://dornsife.usc.edu/phil/'),
]
CONTEXT = {
 'oxford': ('Oxford connects philosophy with technology through its Institute for Ethics in AI. The institute appointed an inaugural academic team of seven philosophers in 2020, with work spanning privacy, democracy and responsibility. Students interested in this intersection can investigate both the Philosophy Faculty and the institute’s current projects.', 'https://www.ox.ac.uk/news/2020-09-11-inaugural-academic-team-appointed-oxford-university-s-institute-ethics-ai'),
 'uc-irvine': ('Philosophy at Irvine spans the Department of Philosophy and the Department of Logic and Philosophy of Science. James Owen Weatherall’s research includes the foundations of physics and models of how false beliefs spread. His work with Cailin O’Connor connects philosophy of science with social learning and misinformation.', 'https://www.faculty.uci.edu/profile/?facultyId=5909'),
 'nyu': ('NYU ranks first among U.S. departments in the 2024 Philosophical Gourmet Report’s faculty reputation survey. In our journal corpus, its decline from 104 to 86 articles is concentrated in Philosophical Studies, which fell from 26 to nine. Analysis increased from three to twelve. The venue comparison gives a more specific picture than the aggregate growth rate.', 'https://philosophicalgourmet.com/overall-rankings-2024/'),
 'macquarie': ('Macquarie’s School of Humanities describes research on agency, mind and the self, including moral cognition, bioethics, neuroethics and the philosophy and ethics of artificial intelligence. Its Ethics and Agency Research Centre provides an institutional focus for this work.', 'https://www.mq.edu.au/faculty-of-arts/schools/school-of-humanities/our-research'),
 'amsterdam': ('Amsterdam organizes philosophy research into four programs: Philosophy and Public Affairs; Logic and Language, Mind and Body; the Philosophical Tradition in Context; and Critical Cultural Theory. Students can use those research groups to identify the faculty and methods most relevant to their interests.', 'https://www.uva.nl/en/discipline/philosophy/research/article.html'),
 'helsinki': ('Helsinki’s theoretical philosophy research includes logic, epistemology, metaphysics, philosophy of language, mind and science, and the history of philosophy. Applicants can investigate these areas through the university’s philosophy discipline and its current research groups.', 'https://www.helsinki.fi/en/faculty-humanities/research/disciplines/philosophy-history-and-art/philosophy'),
}

def profiles():
    rows = list(csv.DictReader((ROOT/'data/2026-10-23/schools.csv').open(encoding='utf-8')))
    result = []
    for row, (slug, short, url) in zip(rows[:20], DEPARTMENTS):
        profile = {'slug': slug, 'name': row['institution'], 'shortName': short,
            'country': row['country'], 'departmentUrl': url,
            'rank': int(row['rank']), 'articles': int(row['articles']),
            'influence': float(row['top_decile_equivalent']),
            'citations': float(row['fractional_citations']),
            'highlyCitedShare': float(row['top_decile_share_pct']),
            'earlierArticles': int(row['articles_2015_2019']),
            'laterArticles': int(row['articles_2020_2024']),
            'growth': float(row['output_change_pct']),
            'updatedAt': '2026-10-24'}
        if slug in CONTEXT:
            profile['researchContext'], profile['researchSource'] = CONTEXT[slug]
        result.append(profile)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'profiles/philosophy-universities.json')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profiles(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Generated {len(DEPARTMENTS)} university research profiles')

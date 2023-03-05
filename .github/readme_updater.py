import os
from datetime import datetime
from typing import List

import pandas as pd
from github import Github, Repository
from regex import match


def process_group(group: str, repo: Repository) -> pd.DataFrame:
    group_table = pd.DataFrame(columns=['student'] + [str(x) for x in range(1, 13)])
    api_result = [(c.name, c.html_url, c.decoded_content.decode('utf-8')) for c in repo.get_contents(group)]
    for (student, url, log) in api_result:
        df = process_log(log)
        student_row = {'student': f'<a href="{url}">{student[:-3].replace("_", " ")}</a>'}
        for _, r in df.iterrows():
            student_row[str(r['lab'])] = r['score']
        group_table = pd.concat([group_table, pd.DataFrame([student_row])])
    group_table = group_table.set_index('student', drop=True)
    group_table = group_table.applymap(lambda x: '' if pd.isna(x) else str(x))
    return group_table


def process_log(log: str) -> pd.DataFrame:
    pattern = '[0-9]+\s:\s.+\s:\s[0-9]+\.[0-9]+\.[0-9]+\s:\s([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[Ee]([+-]?\d+))?\s:\s.*'
    actions = list(filter(lambda x: match(pattern, x), map(str.strip, log.split('\n'))))
    rows = []
    for action in actions:
        lab, teacher, date, score, note = action.split(' : ')
        rows.append({
            'lab': int(lab),
            'teacher': teacher,
            'date': datetime.strptime(date, '%d.%m.%y'),
            'score': float(score),
            'note': note
        })
    df = pd.DataFrame(rows)
    if len(df) != 0:
        df = df.iloc[df.groupby('lab')['score'].idxmax()]
    return df


def main():
    g = Github(os.environ['GITHUB_TOKEN'])
    repo = g.get_repo('xopclabs/ahpkis2023')
    groups = [c.path for c in repo.get_contents('') if not c.path.startswith('.') and c.path != 'README.md']
    readme = '# АХП КИС 2023\n\n'
    for group in groups:
        group_table = process_group(group, repo)
        readme += f'## {group}\n\n' + group_table.to_html(index_names=False, escape=False) + '\n\n'
    repo.update_file('README.md', 'Update README.md', readme, repo.get_contents('README.md').sha)


if __name__ == '__main__':
    main()
from bs4 import BeautifulSoup
import pandas as pd
import re
import requests

import ipywidgets as widgets
from IPython.display import display_html


def get_df(url, criteria=None):
    fname = "jobs.pkl"

    try:
        df = pd.read_pickle(fname)
    except FileNotFoundError:
        raw = pd.read_json(url)
        jobs = raw.data.jobs["nodes"]
        df = pd.DataFrame(jobs)
        jobinfo_keys = list(df["jobInfo"][0].keys())
        df[jobinfo_keys] = df["jobInfo"].apply(
            lambda x: pd.Series([x[k] for k in jobinfo_keys])
        )
        df.drop("jobInfo", axis=1)
        print("writing to pkl")
        df.to_pickle(fname)
    else:
        print("retrieving from pkl")
    finally:
        c1 = df["available"] == True
        c2 = df["studentOpportunities"].apply(len) == 0
        return df[c1 & c2]


def filter_by_list(df, undesired, col):
    pattern = "|".join(map(re.escape, undesired))
    regex = re.compile(pattern, re.IGNORECASE)
    mask = df[col].apply(lambda x: any(regex.search(item) for item in x))
    return df[~mask]


def view_entries(df, col):
    for w in df.explode(col)[col].unique():
        print(w)


def view_jobs(target_df):
    for _, row in target_df.iterrows():
        print(f"-> {row['title']} <-")
        print(row["summary"])
        for q in row["qualifications"]:
            print(f" - {q}")
        print()
        print(f"https://www.cia.gov/careers{row['uri']}")
        print(100 * "-")


def see_page(longlist, df):
    for note in longlist:
        row = df.loc[df["title"] == note["title"]]
        print(f"-> {row['title'].item()} <-")
        job_desc_url = f"https://www.cia.gov/careers{row['uri'].item()}"
        print(job_desc_url)
        page = requests.get(job_desc_url)
        soup = BeautifulSoup(page.text, "html.parser")
        about = _get_sect(soup, "about")
        display_html(" ".join(str(a) for a in about), raw=True)
        quals = _get_sect(soup, "qualifications")
        display(
            widgets.Accordion(
                children=[
                    widgets.HTML(
                        value=" ".join(str(q) for q in quals),
                    )
                ],
                titles=("Qualifications",),
            )
        )


def _get_sect(soup, text):
    match_el = soup.find_all(lambda tag: _match_tag(tag, "h2", text))
    if match_el:
        siblings = []
        for el in match_el:
            next_sibling = el.find_next_sibling()
            while next_sibling and not next_sibling.name.startswith("h"):
                siblings.append(next_sibling)
                next_sibling = next_sibling.find_next_sibling()
        return siblings


def _match_tag(tag, tag_type, text):
    return tag.name == tag_type and text.lower() in tag.text.lower()


if __name__ == "__main__":
    print(
        "This script should not be run directly! Import these functions for use in another file."
    )

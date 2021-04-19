from selenium import webdriver
from lxml import html
import pandas as pd
import numpy as np
from tqdm import tqdm
import sys

def get_scores_for_version(link, driver):
    driver.get("https://www.kaggle.com" + link)
    tree = html.fromstring(driver.page_source)
    public_els = tree.xpath("//div[@class='kernel-code-pane__submission-score-public']/div[2]/text()")
    private_els = tree.xpath("//div[@class='kernel-code-pane__submission-score-private']/div[2]/text()")

    public_score, private_score = np.nan, np.nan
    if len(public_els) > 0:
        public_score = float(public_els[0])
    if len(private_els) > 0:
        private_score = float(private_els[0])    

    return public_score, private_score

def main(kernel_url, fname):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome('./chromedriver', chrome_options=chrome_options,
      service_args=['--verbose'])

    driver.get(kernel_url)
    driver.find_element_by_xpath("//span[contains(@class, 'fa fa-ellipsis-h')]").click()
    driver.find_element_by_xpath("//span[@name='history']").click()
    tree = html.fromstring(driver.page_source)

    rows = tree.xpath("//div[contains(@class, 'sc-kIzrRt eFtbII')]")
    statuses = []
    links = []
    names = []
    run_dates = []
    run_durations = []
    for row in rows:
        status = row.xpath('./a[1]/i/text()')
        if len(status) > 0:
            statuses.append('OK' if status[0] == 'check_circle' else 'Failed')
        else:
            continue

        links.append(row.xpath('./a[1]/@href')[0])
        names.append(row.xpath('./a[2]/text()')[0])
        run_dates.append(row.xpath('./span[1]/a[1]/span/@title')[0][:24])
        run_durations.append(float(row.xpath('./a[4]/text()')[0][:-1]))

    df = pd.DataFrame({
        'Status': statuses,
        'Link': links,
        'Name': names,
        'RunDate': run_dates,
        'Duration': run_durations
    })

    scores = []
    for link in tqdm(df['Link'].values, desc = 'Receiving scores for versions:'):
        scores.append(get_scores_for_version(link, driver))

    driver.close()
    
    df['PublicScore'] = [x[0] for x in scores]
    df['PrivateScore'] = [x[1] for x in scores]
    if fname is not None:
        df.to_csv(fname, index = False)
    else:
        print(df)
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Example usage 1 (save results to file): python main.py <kernel_url> <fname>')
        print('Example usage 2 (print to stdout): python main.py <kernel_url>')
    else:
        kernel_url = sys.argv[1]
        fname = None
        if len(sys.argv) > 2:
            fname = sys.argv[2]
        main(kernel_url, fname)
    

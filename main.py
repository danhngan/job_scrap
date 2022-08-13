
from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import time


###################################
# Params


search_url = 'https://ms.vietnamworks.com/job-search/v1.0/search'
base_job_url = 'https://www.vietnamworks.com/'
# keyword = "phân tích dữ liệu"

query_params = {
    "query": '',
    "filter":[],"ranges":[],
    "order":[],
    "hitsPerPage":50,
    "page":0,
    "retrieveFields":
    [
        "benefits",
        "jobTitle",
        "salaryMax",
        "isSalaryVisible",
        "jobLevelVI",
        "isShowLogo",
        "salaryMin",
        "companyLogo",
        "userId",
        "jobLevel",
        "jobId",
        "companyId",
        "approvedOn",
        "isAnonymous",
        "alias",
        "expiredOn",
        "industries",
        "workingLocations",
        "services",
        "companyName",
        "salary",
        "onlineOn",
        "simpleServices",
        "visibilityDisplay",
        "isShowLogoInSearch",
        "priorityOrder"]}

columns = {
    "Keyword": "Keyword",
    "jobTitle": "Job Title",
    "companyName": "Company Name",
    "salary": "Salary",
    "salaryMax": "Max Salary",
    "salaryMin": "Min Salary",
    "expiredOn": "Job Deadline",
    "jobLevelVI": "Level",
    "jobId": "Job ID",
    "benefits": "Benefits",
    "Skills": 'Skills',
    "Language": "Language",
    "City Address": "City Address",
    "workingLocations": "Address Work",
    "jobUrl": 'URL'
}

###################################
# Get data

def get_data(url, query_params):
    # DataFrame for storing data
    df = pd.DataFrame()
    n_page = 1
    c_page = 0
    while c_page < n_page:
        print(f'Getting page {c_page+1}')
        # Update page number and get page data
        query_params['page'] = c_page
        response = json.loads(requests.post(url=url,
                                            json=query_params).text)
        
        # Check response
        meta_data = response['meta']
        if meta_data['code'] == 200:
            job_data = response['data']
        else:
            print(f'Error: {meta_data["code"]} at page {c_page}')
            break

        # Store data to DataFrame
        for job in job_data:
            job['jobUrl'] = base_job_url + str(job['jobId']) + '-jv'

            # Job page data (contain skills and language)
            job_page = requests.get(job['jobUrl'])
            soup = BeautifulSoup(job_page.text, 'html.parser')
            requirements = soup.find_all('span' , attrs={'class':"content-label"})
            skills = requirements[3]
            language = requirements[4]
            skills = skills.find_next_sibling('span').text.strip('\n ')
            language = language.find_next_sibling('span').text.strip('\n ')
            job['Skills'] = skills
            job['Language'] = language

            df = df.append(job, ignore_index=True)
            time.sleep(0.1)
        # Update number of pages and current page number
        n_page = meta_data['nbPages']
        c_page += 1
        time.sleep(0.5)

    return df


###################################
# Data processing functions


def process_work_location(work_locations):
    """
    return two lists, city addresses and long addresses
    """
    long_address = []
    city_address = []
    for location_list in work_locations:
        temp_long = []
        temp_city = []
        for city in location_list:
            temp_long.append(city['address'])
            temp_city.append(city['cityNameVI'])
        long_address.append(';'.join(temp_long))
        city_address.append(';'.join(temp_city))
    return city_address, long_address


def process_benefits(benefits):
    """
    return a string of benefits seperated by ;
    """
    if benefits is None:
        return ' '
    string_benefits = []
    for benefit in benefits:
        string_benefits.append(benefit['benefitName'] + ': ' + str(benefit['benefitValue']))
    return ';'.join(string_benefits)

def process_salaries(row):
    """
    return a string representing salary
    """
    if row["salaryMin"] == 0 and row["salaryMax"] == 0:
        return 'Thương lượng'
    elif row["salaryMin"] == 0:
        return f'Lên tới {row["salaryMax"]}$'
    elif row["salaryMax"] == 0:
        return f'Từ {row["salaryMin"]}$'
    else:
        return f'Từ {row["salaryMin"]}$ đến {row["salaryMax"]}$'

def process_data(df: pd.DataFrame):
    df['expiredOn'] = pd.to_datetime(df['expiredOn'])
    df['expiredOn'] = df['expiredOn'].dt.strftime('%d-%m-%Y')
    df['City Address'], df['workingLocations'] = process_work_location(df['workingLocations'])
    df['salary'] = df.apply(process_salaries, axis=1)
    df['benefits'] = df['benefits'].apply(process_benefits)
    return df


###################################
# Main

def main():
    # Get keyword
    keyword = input('Enter keyword: ')
    query_params["query"] = keyword

    # Output file path
    output_path = input('Enter output file path: ')
    if len(output_path) == 0:
        output_path = 'Job_scraping.xlsx'
    if output_path[-5:] != '.xlsx':
        output_path += '.xlsx'

    # Get data
    process_df = get_data(search_url, query_params)
    process_df['Keyword'] = keyword
    

    # Process data
    process_df = process_data(process_df)
    process_df = process_df[list(columns.keys())].copy()
    process_df.rename(columns=columns, inplace=True)
    process_df.drop(['Max Salary', 'Min Salary', 'Job ID'], axis=1, inplace=True)
    
    # Save data
    process_df.to_excel(output_path)

    print('Done!')


if __name__ == '__main__':
    main()

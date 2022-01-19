import requests
import statistics

from itertools import count
from environs import Env
from terminaltables import AsciiTable


def get_hh_vacancies(language:str, search_area=1, search_period=30):
    vacancies = []
    url = 'https://api.hh.ru/vacancies'
    max_per_page_param = 100
    payload = {
        'text': language,
        'search_field': 'name',
        'area': search_area,
        'period': search_period,
        'per_page': max_per_page_param,
    }
    
    for page in count(0, 1):
        payload['page'] = page

        response = requests.get(url, params=payload)
        response.raise_for_status()

        response = response.json()
        vacancies += response['items']
        total_pages = response['pages']
        vacancies_amount = response['found']

        if page == total_pages - 1:
            return vacancies, vacancies_amount


def get_sj_vacancies(language:str, token:str, town_id=4):
    vacancies = []
    url = 'https://api.superjob.ru/2.0/vacancies'
    headers = {
        'X-Api-App-Id': token
    }
    payload = {
        'town': town_id,
        'keywords[1][keys]': language,
        'period': 30,
        'count': 100
    }

    for page in count(0, 1):
        payload['page'] = page

        response = requests.get(url, params=payload, headers=headers)
        response.raise_for_status()

        response = response.json()
        vacancies += response['objects']
        vacancies_amount = response['total']
        more_pages = response['more']

        if not more_pages:
            return vacancies, vacancies_amount


def get_average_salary(salary_from, salary_to):
    if salary_from:
        return salary_from * 1.2
    else:
        return salary_to * 0.8


def get_hh_salaries(vacancies:list):
    salaries = []

    for vacancy in vacancies:
        if not vacancy['salary']:
            continue

        if vacancy['salary']['currency'] != 'RUR':
            continue
        
        if vacancy['salary']['from'] and vacancy['salary']['to']:
            salary = (
                vacancy['salary']['from'] + vacancy['salary']['to']
            ) / 2
            salaries.append(salary)

        elif vacancy['salary']['from'] or vacancy['salary']['to']:
            salaries.append(
                get_average_salary(
                    vacancy['salary']['from'],
                    vacancy['salary']['to']
                )
            )

    return salaries


def get_sj_salaries(vacancies:list):
    salaries = []

    for vacancy in vacancies:
        if vacancy['currency'] != 'rub':
            continue

        if vacancy['payment_from'] and vacancy['payment_to']:
            salary = (vacancy['payment_from'] + vacancy['payment_to']) / 2
            salaries.append(round(salary))

        elif vacancy['payment_from'] or vacancy['payment_to']:
            salaries.append(
                get_average_salary(
                    vacancy['payment_from'],
                    vacancy['payment_to']
                )
            )

    return salaries


def get_statistics(language, salaries, vacancies_amount):
    salary_statistics = {
        'language': language,
        'vacancies_found': vacancies_amount,
        'vacancies_processed': len(salaries),
        'average_salary': round(statistics.mean(salaries))
    }

    return salary_statistics


def create_table(statistics:list, statistics_source:str):
    table_data = [
        [
            'Язык програмирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        ]
    ]

    for language_stat in statistics:
        table_data.append(
            [
                language_stat['language'],
                language_stat['vacancies_found'],
                language_stat['vacancies_processed'],
                language_stat['average_salary']
            ]
        )

    return AsciiTable(table_data, statistics_source)


if __name__ == '__main__':
    env = Env()
    env.read_env()
    sj_token = env('SJ_TOKEN')

    most_popular_languages = [
        'Python',
        # 'Javascript',
        # 'Java',
        # 'Ruby',
        # 'C++'
    ]

    hh_common_statistics = []
    sj_common_statistics = []

    for language in most_popular_languages:
        vacancies_hh, vacancies_amount_hh = get_hh_vacancies(language)
        vacancies_sj, vacancies_amount_sj = get_sj_vacancies(language, sj_token)

        hh_salaries = get_hh_salaries(vacancies_hh)
        sj_salaries = get_sj_salaries(vacancies_sj)

        hh_statistics = get_statistics(language, hh_salaries, vacancies_amount_hh)
        sj_statistics = get_statistics(language, sj_salaries, vacancies_amount_sj)

        hh_common_statistics.append(hh_statistics)
        sj_common_statistics.append(sj_statistics)


    hh_table = create_table(hh_common_statistics, 'HeadHanter Moscow')
    sj_table = create_table(sj_common_statistics, 'SuperJob Moscow')

    print(hh_table.table)
    print(sj_table.table)
    
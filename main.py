import requests
import statistics

from itertools import count
from environs import Env
from terminaltables import AsciiTable


def get_hh_vacancies(language: str, search_area=1, search_period=30):
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

        vacancies_info = response.json()
        vacancies += vacancies_info['items']
        total_pages = vacancies_info['pages']
        vacancies_amount = vacancies_info['found']

        if page == total_pages - 1:
            return vacancies, vacancies_amount


def get_sj_vacancies(language: str, token: str, town_id=4):
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

        vacancies_info = response.json()
        vacancies += vacancies_info['objects']
        vacancies_amount = vacancies_info['total']
        more_pages = vacancies_info['more']

        if not more_pages:
            return vacancies, vacancies_amount


def predict_rub_salary(salary_from, salary_to):
    if salary_from:
        return salary_from * 1.2
    
    return salary_to * 0.8


def get_hh_salaries(vacancies: list):
    salaries = []

    for vacancy in vacancies:
        if not vacancy['salary']:
            continue

        if vacancy['salary']['currency'] != 'RUR':
            continue
        
        payment_from = vacancy['salary']['from']
        payment_to = vacancy['salary']['to']

        if payment_from and payment_to:
            salary = (payment_from + payment_to) / 2
            salaries.append(salary)

        elif payment_from or payment_to:
            salaries.append(
                predict_rub_salary(
                    payment_from,
                    payment_to
                )
            )

    return salaries


def get_sj_salaries(vacancies: list):
    salaries = []

    for vacancy in vacancies:
        if vacancy['currency'] != 'rub':
            continue
        
        payment_from = vacancy['payment_from']
        payment_to = vacancy['payment_to']

        if payment_from and payment_to:
            salary = (payment_from + payment_to) / 2
            salaries.append(round(salary))

        elif payment_from or payment_to:
            salaries.append(
                predict_rub_salary(
                    payment_from,
                    payment_to
                )
            )

    return salaries


def get_statistics(language, salaries, vacancies_amount):
    average_salary = round(statistics.mean(salaries))

    salary_statistics = {
        'language': language,
        'vacancies_found': vacancies_amount,
        'vacancies_processed': len(salaries),
        'average_salary': average_salary
    }

    return salary_statistics


def create_table(statistics: list, statistics_source: str):
    result_table = [
        [
            '???????? ??????????????????????????????',
            '???????????????? ??????????????',
            '???????????????? ????????????????????',
            '?????????????? ????????????????'
        ]
    ]

    for language_stat in statistics:
        result_table.append(
            [
                language_stat['language'],
                language_stat['vacancies_found'],
                language_stat['vacancies_processed'],
                language_stat['average_salary']
            ]
        )

    return AsciiTable(result_table, statistics_source)


if __name__ == '__main__':
    env = Env()
    env.read_env()
    sj_token = env('SJ_TOKEN')

    most_popular_languages = [
        'Python',
        'Javascript',
        'Java',
        'Ruby',
        'C++'
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
    
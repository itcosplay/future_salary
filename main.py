import json
import requests
import statistics

from environs import Env
from terminaltables import AsciiTable


class HeadHanterStatistics:
    def __init__(self, area=1, period=30):
        self.area = area
        self.period = period


    def get_vacancies_by_programming_lan(self, language):
        max_per_page_param = 100
        vacancies = None
        current_page = 0
        total_pages = 0

        while current_page <= total_pages:
            payload = {
                'text': f'{language}',
                'search_field': 'name',
                'area': self.area,
                'period': self.period,
                'per_page': max_per_page_param,
                'page': current_page
            }
        
            response = requests.get('https://api.hh.ru/vacancies', params=payload)
            response.raise_for_status()

            if vacancies is None:
                vacancies = response.json()
                total_pages = vacancies['pages']
                current_page += 1
            else:
                vacancies['items'] = vacancies['items'] + response.json()['items']
                current_page += 1
        
        return vacancies
        

    def get_salaries_from_vacancies(self, vacancies):
        salaries = []

        for vacancy in vacancies:
            if vacancy['salary']:
                salary = {
                    'from': vacancy['salary']['from'],
                    'to': vacancy['salary']['to'],
                    'currency': vacancy['salary']['currency'],
                    'gross': vacancy['salary']['gross']
                }

                salaries.append(salary)

        return salaries


    def predict_salary(self, salaries):
        predicted_salaries = []

        for salary in salaries:
            if salary['currency'] != 'RUR':
                pass
            elif salary['from'] and salary['to']:
                salary = (salary['from'] + salary['to']) / 2
                predicted_salaries.append(salary)
                
            elif not salary['from']:
                salary = salary['to'] * 0.8
                predicted_salaries.append(salary)
                
            elif not salary['to']:
                salary = salary['from'] * 1.2
                predicted_salaries.append(salary)

        return predicted_salaries


    def get_statistics_by_program_lan(self, language):
        vacancies = self.get_vacancies_by_programming_lan(language)
        salaries = self.get_salaries_from_vacancies(vacancies['items'])
        predicted_salaries = self.predict_salary(salaries)

        salary_statistics = {
            'vacancies_found': vacancies['found'],
            'vacancies_processed': len(salaries),
            'average_salary': round(statistics.mean(predicted_salaries))
        }

        return salary_statistics
    

    def show_statistics_by_languages(self, *args):
        languages_statistics = {}
        for language in args:
            languages_statistics[language] = self.get_statistics_by_program_lan(language)
        
        table_data = create_table_data(languages_statistics)
        table = AsciiTable(table_data, 'HeadHanter')
        print(table.table)
    

    def create_table_data(self, statistics:dict):
        table_data = [
            [
                'Язык програмирования',
                'Вакансий найдено',
                'Вакансий обработано',
                'Средняя зарплата'
            ]
        ]

        for program_language in statistics.keys():
            language_data = [
                f'{program_language}',
                statistics[f'{program_language}']['vacancies_found'],
                statistics[f'{program_language}']['vacancies_processed'],
                statistics[f'{program_language}']['average_salary']
            ]
            table_data.append(language_data)

        return table_data


class SuperJobStatistics:
    def __init__(self, token, town_id=4):
        self.token = token
        self.town_id = town_id


    def get_vacancies_by_programming_lan(self, language):
        current_page = 0
        total_pages = 0
        vacancies = None
        url = 'https://api.superjob.ru/2.0/vacancies'
        headers = {
            'X-Api-App-Id': self.token
        }
        while total_pages <= current_page:
            
            payload = {
                'town': self.town_id,
                'keywords[1][keys]': language,
                'period': 30,
                'page': current_page,
                'count': 100
            }
            print('current_page: ', current_page)

            response = requests.get(url, params=payload, headers=headers)
            response.raise_for_status()

            if vacancies is None:
                vacancies = response.json()
                more_results = vacancies['more']
                
                current_page += 1
            else:
                vacancies['objects'] = vacancies['objects'] + response.json()['objects']
                more_results = vacancies['more']
                print('more_results: ', more_results)
                current_page += 1

        with open('sj_data.json', 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=4)

        return response.json()

    
    def get_salaries_from_vacancies(self, vacancies):
        salaries = []

        for vacancy in vacancies:
            if vacancy['currency'] == 'rub':
                salary = {
                    'from': vacancy['payment_from'],
                    'to': vacancy['payment_to']
                }

                salaries.append(salary)

        return salaries

    
    def predict_salary(self, salaries):
        predicted_salaries = []

        for salary in salaries:
            if salary['from'] and salary['to']:
                salary = (salary['from'] + salary['to']) / 2
                predicted_salaries.append(salary)
                
            elif not salary['from']:
                salary = salary['to'] * 0.8
                predicted_salaries.append(salary)
                
            elif not salary['to']:
                salary = salary['from'] * 1.2
                predicted_salaries.append(salary)
            else:
                continue

        return predicted_salaries

    
    def get_statistics_by_program_lan(self, language):
        vacancies = self.get_vacancies_by_programming_lan(language)
        salaries = self.get_salaries_from_vacancies(vacancies['objects'])
        predicted_salaries = self.predict_salary(salaries)

        salary_statistics = {
            'vacancies_found': vacancies['total'],
            'vacancies_processed': len(salaries),
            'average_salary': round(statistics.mean(predicted_salaries))
        }

        return salary_statistics


    def show_statistics_by_languages(self, *args):
        languages_statistics = {}
        for language in args:
            languages_statistics[language] = self.get_statistics_by_program_lan(language)
        
        table_data = create_table_data(languages_statistics)
        table = AsciiTable(table_data, 'SuperJob')
        print(table.table)


    def create_table_data(self, statistics:dict):
            table_data = [
                [
                    'Язык програмирования',
                    'Вакансий найдено',
                    'Вакансий обработано',
                    'Средняя зарплата'
                ]
            ]

            for program_language in statistics.keys():
                language_data = [
                    f'{program_language}',
                    statistics[f'{program_language}']['vacancies_found'],
                    statistics[f'{program_language}']['vacancies_processed'],
                    statistics[f'{program_language}']['average_salary']
                ]
                table_data.append(language_data)

            return table_data
    




def get_vacancies_by_programming_lan(language):
    moscow_area = 1
    month_period = 30
    max_per_page_param = 100

    payload = {
        'text': f'{language}',
        'search_field': 'name',
        'area': moscow_area,
        'period': month_period,
        'per_page': max_per_page_param
    }

    response = requests.get('https://api.hh.ru/vacancies', params=payload)
    response.raise_for_status()
    
    vacancies_data = response.json()
    total_pages = vacancies_data['pages']
    current_page = vacancies_data['page']

    while current_page <= total_pages:
        current_page += 1
        payload = {
            'text': f'програмист {language}',
            'search_field': 'name',
            'area': moscow_area,
            'period': month_period,
            'per_page': max_per_page_param,
            'page': current_page
        }

        response = requests.get('https://api.hh.ru/vacancies', params=payload)
        response.raise_for_status()

        vacancies_data['items'] = vacancies_data['items'] + response.json()['items']

    return vacancies_data


def get_salaries_from_vacancies(vacancies):
    salaries = []

    for vacancy in vacancies:
        if vacancy['salary']:
            salary = {
                'from': vacancy['salary']['from'],
                'to': vacancy['salary']['to'],
                'currency': vacancy['salary']['currency'],
                'gross': vacancy['salary']['gross']
            }

            salaries.append(salary)

    return salaries


def predict_rub_salary(salaries):
    predicted_salaries = []

    for salary in salaries:
        if salary['currency'] != 'RUR':
            pass
        elif salary['from'] and salary['to']:
            salary = (salary['from'] + salary['to']) / 2
            predicted_salaries.append(salary)
            
        elif not salary['from']:
            salary = salary['to'] * 0.8
            predicted_salaries.append(salary)
            
        elif not salary['to']:
            salary = salary['from'] * 1.2
            predicted_salaries.append(salary)

    return predicted_salaries


def get_statistics_by_program_lan(language):
    vacancies_data = get_vacancies_by_programming_lan(language)
    salaries = get_salaries_from_vacancies(vacancies_data['items'])
    predicted_salaries = predict_rub_salary(salaries)

    salary_statistics = {
        'vacancies_found': vacancies_data['found'],
        'vacancies_processed': len(salaries),
        'average_salary': round(statistics.mean(predicted_salaries))
    }

    return salary_statistics


def get_vacancies_from_sj(token, language):
    url = 'https://api.superjob.ru/2.0/vacancies'
    headers = {
        'X-Api-App-Id': token
    }

    payload = {
        'town': 4,
        'keywords[1][keys]': language
    }

    response = requests.get(url, params=payload, headers=headers)
    response.raise_for_status()

    with open('sj_data.json', 'w', encoding='utf-8') as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=4)

    return response.json()


def get_salaries_from_sj_vacancies(vacancies):
    salaries = []

    for vacancy in vacancies:
        if vacancy['currency'] == 'rub':
            salary = {
                'from': vacancy['payment_from'],
                'to': vacancy['payment_to']
            }

            salaries.append(salary)

    return salaries


def predict_salary_from_sj(salaries):
    predicted_salaries = []

    for salary in salaries:
        if salary['from'] and salary['to']:
            salary = (salary['from'] + salary['to']) / 2
            predicted_salaries.append(salary)
            
        elif not salary['from']:
            salary = salary['to'] * 0.8
            predicted_salaries.append(salary)
            
        elif not salary['to']:
            salary = salary['from'] * 1.2
            predicted_salaries.append(salary)
        else:
            continue

    return predicted_salaries


def get_statistics_by_program_lan_from_sj(token, language):
    vacancies_data = get_vacancies_from_sj(token, language)
    salaries = get_salaries_from_sj_vacancies(vacancies_data['objects'])
    predicted_salaries = predict_salary_from_sj(salaries)

    salary_statistics = {
        'vacancies_found': vacancies_data['total'],
        'vacancies_processed': len(salaries),
        'average_salary': round(statistics.mean(predicted_salaries))
    }

    return salary_statistics


def create_table_data(statistics:dict):
    table_data = [
        [
            'Язык програмирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        ]
    ]

    for program_language in statistics.keys():
        language_data = [
            f'{program_language}',
            statistics[f'{program_language}']['vacancies_found'],
            statistics[f'{program_language}']['vacancies_processed'],
            statistics[f'{program_language}']['average_salary']
        ]
        table_data.append(language_data)

    return table_data


if __name__ == '__main__':
    env = Env()
    env.read_env()
    sj_token = env('SJ_TOKEN')

    # head_hunter_stat = HeadHanterStatistics()
    # head_hunter_stat.show_statistics_by_languages(
    #     'python',
    #     'javascript',
    #     'java'
    # )

    super_job_stat = SuperJobStatistics(sj_token)
    # super_job_stat.show_statistics_by_languages(
    #     'python',
    #     'javascript',
    #     'java'
    # )

    super_job_stat.get_vacancies_by_programming_lan('c#')
    # super_job_stat.get_vacancies_by_programming_lan('python')


    # popular_languages = ['python', 'javascript', 'java']
    # popular_languages = ['python']

    # languages_statistics = {}
    # for language in popular_languages:
    #     languages_statistics[language] = get_statistics_by_program_lan(language)
    
    # print(languages_statistics)


    # languages_statistics = {}
    # for language in popular_languages:
    #     languages_statistics[language] = get_statistics_by_program_lan_from_sj(sj_token, language)

    # print(languages_statistics)

    # table_data_hh = create_table_data(languages_statistics)

    # table = AsciiTable(table_data, 'HeadHanter')
    # print(table.table)

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
        
        table_data = self.create_table_data(languages_statistics)
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
        while current_page <= total_pages:
            payload = {
                'town': self.town_id,
                'keywords[1][keys]': language,
                'period': 30,
                'page': current_page,
                'count': 100
            }

            response = requests.get(url, params=payload, headers=headers)
            response.raise_for_status()

            if vacancies is None:
                vacancies = response.json()
                total_pages = vacancies['total'] // payload['count']
                current_page += 1
            else:
                vacancies['objects'] = vacancies['objects'] + response.json()['objects']
                current_page += 1
        
        # if you want to save vacancies in sj_data.json, uncoment code below
        # with open('sj_data.json', 'w', encoding='utf-8') as f:
        #     json.dump(vacancies, f, ensure_ascii=False, indent=4)

        return vacancies

    
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
        
        table_data = self.create_table_data(languages_statistics)
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

    head_hunter_stat = HeadHanterStatistics()
    head_hunter_stat.show_statistics_by_languages(*most_popular_languages)

    super_job_stat = SuperJobStatistics(sj_token)
    super_job_stat.show_statistics_by_languages(*most_popular_languages)

    
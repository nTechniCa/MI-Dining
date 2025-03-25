import json
from bs4 import BeautifulSoup
import os
import requests
from datetime import datetime
import pytz
import time
import random
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger.setLevel(logging.DEBUG)

# import google.generativeai as genai

# GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# if not GEMINI_API_KEY:
#     raise ValueError("Please set the GEMINI_API_KEY environment variable")

def fetch_dining_hall_info(preferences={}) -> dict: #TODO: Add preferences parameter
    def get_current_time_est():
        # Create a timezone object for Eastern Standard Time
        est = pytz.timezone('America/New_York')

        # Get the current time in UTC
        utc_now = datetime.utcnow()

        # Make the UTC time aware by adding timezone information
        aware_utc_now = pytz.utc.localize(utc_now)

        # Convert from UTC to EST
        est_now = aware_utc_now.astimezone(est)

        return est_now

    current_day = get_current_time_est().strftime('%Y-%m-%d')
    current_time = get_current_time_est().strftime('%H:%M')

    this_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(this_dir, 'output')
    data_dir = os.path.join(this_dir, 'data')
    menu_htmls_dir = os.path.join(data_dir, 'menu_htmls')

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(menu_htmls_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    dining_halls = [
        'Bursley',
        'East Quad',
        'Markley',
        'Mosher-Jordan',
        'North Quad',
        'South Quad'
    ]

    base_url = 'https://dining.umich.edu/menus-locations/dining-halls/'

    def save_webpage(url, file_path):
        try:
            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Open a file and write the content
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(response.text)
                print(f"Page saved successfully to {file_path}")
            else:
                print(f"Failed to retrieve the page. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"An error occurred: {e}")

    def webscraping_needed():
        if os.path.exists(output_dir + '/dining_hall_info.json'):
            data = json.load(open(output_dir + '/dining_hall_info.json'))
            if data[-1]['last_updated'] == current_day:
                logger.info("Data is up to date, no need to scrape.")
                return False
        logger.info("Data is not up to date, scraping is needed.")
        return True

    if webscraping_needed():
        # Save the HTML of the webpages
        for hall in dining_halls:
            url = base_url + hall.lower().replace(' ', '-') + '/'
            file_name = url.split('/')[-2] + '.html'
            file_path = os.path.join(menu_htmls_dir, file_name)
            save_webpage(url, file_path)

        all_info = []

        # Load the HTML from a file
        file_list = os.listdir(f'{data_dir}/menu_htmls')
        dining_halls = {}


        for file_path in file_list:
            if not file_path.endswith('.html'):
                print(f"Skipping {file_path} because it is not an HTML file")
                continue

            with open(menu_htmls_dir + '/' + file_path, 'r') as file:
                html_content = file.read()

            dining_hall_info = {}

            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            dining_hall_name = soup.find('title').get_text(strip=True)
            dining_hall_info['dining_hall'] = dining_hall_name.split(' | ')[0].strip()
            dining_hall_info['last_updated'] = current_day

            # Initialize a dictionary to store the menu data
            menus = {'Breakfast': [], 'Lunch': [], 'Dinner': []}

            menu_items = soup.find('div', id="mdining-items") 
            sections = list(menu_items.find_all('ul', class_="items")) 
            for section in sections:
                meal_time = section.find_previous('h3').get_text(strip=True)

                section_object = {}
                section_object['station_name'] = section.find_previous('h4').get_text(strip=True)
                section_object['items'] = []
                items = list(section.find_all('div', class_="nutrition-wrapper"))
                for item in items:
                    item_object = {}
                    item_name = item.find_previous('div', class_="item-name").get_text(strip=True)
                    item_object['item_name'] = item_name
                    traits = item.find_previous('ul', class_="traits")
                    item_object['traits'] = [trait.get_text(strip=True) for trait in traits.find_all('li')]
                    if item_name == "No Service":
                        continue
                    item_object['nutrition'] = {}

                    nutrition_info = list(item.find_all('td'))
                    for attribute in nutrition_info:
                        if "Serving Size" in attribute.get_text():
                            item_object['nutrition']['serving_size'] = attribute.get_text().split('(')[-1][:-2]
                        if "Calories" in attribute.get_text():
                            item_object['nutrition']['calories'] = attribute.get_text().split(' ')[-1]
                        if "Total Fat" in attribute.get_text():
                            item_object['nutrition']['total_fat'] = attribute.get_text().split(' ')[-1]
                        if "Saturated Fat" in attribute.get_text():
                            item_object['nutrition']['saturated_fat'] = attribute.get_text().split(' ')[-1]
                        if "Trans Fat" in attribute.get_text():
                            item_object['nutrition']['trans_fat'] = attribute.get_text().split(' ')[-1]
                        if "Cholesterol" in attribute.get_text():
                            item_object['nutrition']['cholesterol'] = attribute.get_text().split(' ')[-1]
                        if "Sodium" in attribute.get_text():
                            item_object['nutrition']['sodium'] = attribute.get_text().split(' ')[-1]
                        if "Total Carbohydrate" in attribute.get_text():
                            item_object['nutrition']['total_carbohydrate'] = attribute.get_text().split(' ')[-1]
                        if "Dietary Fiber" in attribute.get_text():
                            item_object['nutrition']['dietary_fiber'] = attribute.get_text().split(' ')[-1]
                        if "Sugars" in attribute.get_text():
                            item_object['nutrition']['sugars'] = attribute.get_text().split(' ')[-1]
                        if "Protein" in attribute.get_text():
                            item_object['nutrition']['protein'] = attribute.get_text().split(' ')[-1]
                        if "Vitamin A" in attribute.get_text():
                            next_attribute = nutrition_info[nutrition_info.index(attribute) + 1].get_text()
                            item_object['nutrition']['vitamin_a'] = next_attribute.split(' ')[-1]
                        if "Vitamin C" in attribute.get_text():
                            next_attribute = nutrition_info[nutrition_info.index(attribute) + 1].get_text()
                            item_object['nutrition']['vitamin_c'] = next_attribute.split(' ')[-1]
                        if "Calcium" in attribute.get_text():
                            next_attribute = nutrition_info[nutrition_info.index(attribute) + 1].get_text()
                            item_object['nutrition']['calcium'] = next_attribute.split(' ')[-1]
                        if "Iron" in attribute.get_text():
                            next_attribute = nutrition_info[nutrition_info.index(attribute) + 1].get_text()
                            item_object['nutrition']['iron'] = next_attribute.split(' ')[-1]
                    section_object['items'].append(item_object)

                menus[meal_time].append(section_object)
            
            dining_hall_info['menus'] = menus
            all_info.append(dining_hall_info)


        file_path = os.path.join(output_dir, "dining_hall_info.json")
        with open(file_path, 'w') as file:
            json.dump(all_info, file, indent=4)
            logger.info(f"Data saved successfully to {file_path}")

    dining_hall_info = json.load(open(output_dir + '/dining_hall_info.json'))

    #TODO: Add a filtering mechanism to only show the information depending on users preferences (traits, dining halls, etc.)

    context = f'Here is all of the dining hall information for todays menus that you can refernce to answer the students questions: {dining_hall_info}\n\n' 
    context += f'Current day and time: {get_current_time_est()}\n\n'

    dining_hall_hours = json.load(open(data_dir + '/static_info/dining_hall_hours.json'))

    days_translation = {
        'Sunday': 0,
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6
    }

    def currently_serving(dining_halls, dining_hall_hours, time):
        hours = int(time.split(':')[0])
        minutes = int(time.split(':')[1]) / 60

        current_day = days_translation[get_current_time_est().strftime('%A')]

        current_time = hours + minutes

        current_serving = "Dining hall serving statuses: \n\n"

        for hall in dining_halls:
            hours_each_day = list(dining_hall_hours[hall].keys())
            current_hours = None
            for day in hours_each_day:
                day_interval = None
                if '-' in day:
                    beginning = days_translation[day.split('-')[0].strip()]
                    end = days_translation[day.split('-')[1].strip()]
                    day_interval = (beginning, end)
                else:
                    beginning = days_translation[day]
                    end = days_translation[day]
                    day_interval = (beginning, end)

                if current_day >= day_interval[0] and current_day <= day_interval[1]:
                    current_hours = dining_hall_hours[hall][day]
                    break

            if current_hours:
                if current_time >= current_hours['Breakfast'][0] and current_time <= current_hours['Breakfast'][1]:
                    current_serving += f"{hall} is currently serving breakfast: {current_hours['Breakfast']}\n"
                elif current_time >= current_hours['Lunch'][0] and current_time <= current_hours['Lunch'][1]:
                    current_serving += f"{hall} is currently serving lunch: {current_hours['Lunch']}\n"
                elif current_time >= current_hours['Dinner'][0] and current_time <= current_hours['Dinner'][1]:
                    current_serving += f"{hall} is currently serving dinner: {current_hours['Dinner']}\n"
                else:
                    current_serving += f"{hall} is currently closed.\n"
            else:
                current_serving += f"{hall} is currently closed.\n"

        return current_serving


    context += currently_serving(dining_halls, dining_hall_hours, current_time)
    return {"context": context}


# context = fetch_dining_hall_info()

# genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# model = genai.GenerativeModel(
#     model_name="gemini-1.5-flash",
#     system_instruction="Using information about University of Michigan dining halls, answer the student's prompts.",
# )

# print("Model loaded successfully, ready to generate content. Type exit to quit.")

# prompt = input("Student > ")
# prompt += context + "Student prompt: " + prompt

# chat = model.start_chat(
#     history =[]
# )

# while prompt != "exit":
#     response = chat.send_message(prompt, stream=True)
#     print("Model > ", flush=True)
#     for chunk in response:
#         words = chunk.text.split()
#         # for word in words:
#         #     delay = random.uniform(0.01, 0.02)
#         #     print(word, end=' ', flush=True)
#         #     time.sleep(delay)
#         print(chunk.text, flush=True)
#     print()
#     prompt = input("Student > ")

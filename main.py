import os
import requests
from bs4 import BeautifulSoup
import urllib


'''
SAMPLE 1 Download Class; function search_data | Sample Output | Variable: get_example_sentence

<div class="exampleSentence">
<span class="recordingsAndTranscriptions"><span class="en-GB hasRecording" title="British English">
<span class="audioIcon icon-sound dontprint soundOnClick" 
data-audio-url="/images-common/en/mp3/the_dumpster_was_empty_except_for_a_single_bag_of_garbage.mp3" tabindex="-1">
</span></span></span>The dumpster was empty except for a single bag of garbage.    <span class="exampleSentenceTranslation">
(Kontener był pusty oprócz jednej torby ze śmieciami.)
</span>'''


'''
SAMPLE 2 Download Class; function search_data | Sample Output | Variable: data_map

{'en_sentence': 'The dumpster was empty except for a single bag of garbage.', 
'pl_sentence': 'Kontener był pusty oprócz jednej torby ze śmieciami.', 
'get_mp3': '/images-common/en/mp3/the_dumpster_was_empty_except_for_a_single_bag_of_garbage.mp3'}
'''


class Settings:
    def __init__(self) -> None:
        self.url = "https://www.diki.pl"
        self.url_query = "/slownik-angielskiego?q="
        self.words_list = 'words.txt'
        self.ankideck_path = 'words_to_anki.txt'
        self.anki_media_path = "/home/kamil/.local/share/Anki2/kamil/collection.media/" # https://docs.ankiweb.net/importing/text-files.html


class AnkiFiles:
    def __init__(self, path_to_words_file: str, path_to_deck_file: str) -> None:
        self.path_to_words_file = path_to_words_file
        self.path_to_deck_file = path_to_deck_file
        self.words = []
        self.words_number = 0


    def clear_anki_deck_file(self):
        # Clear ankideck_path = 'words_to_anki.txt' to avoid importing old data once again
        try:
            with open(self.path_to_deck_file, 'w') as words_file:
                pass
        except Exception as error:
            print(f'Cannot clear file. Error: {error}')


    def read_words_file(self):
        # Read the file with english words - one per line - and return it as a list
        try:
            with open(self.path_to_words_file) as words_file:
                self.words = words_file.readlines()
                return self.words
        except Exception as error:
            print(f'Cannot read from file. Error: {error}')


    def get_words_number(self):
        # Count how many words are in the file
        self.words_number = len(self.words)
        print(f'There are {self.words_number} words in file')


class Download:
    def __init__(self, user_settings: object, user_words_list: list) -> None:
        self.user_settings = user_settings
        self.words_list = user_words_list
        self.removed_words = []
        self.data_map = {}
        self.mp3_filename = ''
        self.mp3_website_path = ''
        self.download_flag = False
    
    
    def return_data_map(self):
        # Return data_map from SAMPLE 2, function useful only for test purposes
        if self.download_flag:
            return self.data_map
        

    def extract_mp3_filename(self):
        # Extract filename from web path, to see sample path check SAMPLE 2
        mp3_path = self.data_map['get_mp3']
        mp3_filename_startpoint = mp3_path.find("mp3")
        mp3_filename = mp3_path[mp3_filename_startpoint + 4:]
        self.mp3_filename = mp3_filename
    

    def print_removed_words(self):
        # Print words that were not found on webpage because http response code was different than 200
        if len(self.removed_words) > 0:
            print('A list of words that were not found: ')
            for word in self.removed_words:
                print(word, end=' ')
                

    def search_data(self, content):
        # Search for polish and english sentences and mp3, check SAMPLE 1 to see correct output from get_example_sentence
        soup = BeautifulSoup(content, 'html.parser')
        get_example_sentence = soup.find('div', {'class': 'exampleSentence'})
        if get_example_sentence != None:
            en_pl_sentence = get_example_sentence.get_text(strip=True)
            en_pl_sentence_split = en_pl_sentence.split("(")
            mp3 = get_example_sentence.find('span', {'class' : 'audioIcon'}).get('data-audio-url')
            self.data_map = {'en_sentence' : en_pl_sentence_split[0],
                        'pl_sentence' : en_pl_sentence_split[1].replace(")", ""),
                        'get_mp3'     : mp3}
            
            self.download_flag = True
        else: 
            self.download_flag = False

    
    def download_data(self):
        # Download mp3 file and save it in anki_media_path from Settings class
        url = self.user_settings.url + self.data_map['get_mp3']
        try:
            response = requests.get(url)
            if response.status_code == 200:
                file_to_save = os.path.join(self.user_settings.anki_media_path + self.mp3_filename)
                print(file_to_save)
                with open(file_to_save, 'wb') as file:
                    file.write(response.content)
            else:
                print(f'Wrong status code for file {self.mp3_filename}')
        except Exception as e:
            print(f'An error occured: {e}')


    def append_anki_deck(self):
        # Concatinate polish, english and mp3 file name into one strign and save it to the file
        try:
            with open(self.user_settings.ankideck_path, 'a') as flashcards:
                    flashcards.write(self.data_map['pl_sentence'] + ';' + self.data_map['en_sentence'] + '[sound:' + self.mp3_filename + ']\n')
        except Exception as write_error:
            print(f'Cannot write to file. Error: {write_error}')


    def main(self):
        for word in self.words_list:
            req = self.user_settings.url + self.user_settings.url_query + urllib.parse.quote(word.lower().strip())
            response = requests.get(req)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                self.search_data(response.text)
                if self.download_flag:
                    self.extract_mp3_filename()
                    self.download_data()  
                    self.append_anki_deck()
            else:
                self.removed_words.append(word)


    def run(self):
        if len(self.words_list) > 0:
            self.main()
        else:
            print('Words list is empty')



def main():
    diki_settings = Settings()
    user_anki_files = AnkiFiles(diki_settings.words_list, diki_settings.ankideck_path) # Provide words file & anki_deck file paths
    user_anki_files.clear_anki_deck_file()
   
    # Test without file
    #dupa = ['work']
    #download_word = Download(diki_settings, dupa)


    # Test with file
    download_word = Download(diki_settings, user_anki_files.read_words_file()) # Second argument has to be a list
    
    
    download_word.run()

    # Print information about download status
    user_anki_files.get_words_number()
    download_word.print_removed_words()
    print('Before you import deck, please check if it has correct format "PL sentence;ENG sentece;[sound:/file_name.mp3]"\nExecute: cat words_to_anki.txt')
    print('''To import deck:\n1. Go to File > Import\n
          2. Choose words_to_anki.txt\n
          3. You need to turn on the "allow HTML in fields" checkbox in the import dialog for HTML newlines to work.\n
          4. Click Import''')



main()





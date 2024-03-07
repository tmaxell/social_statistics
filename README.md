This program allows you to analyze and gather insights from the content of Telegram channels and VK groups. It retrieves messages from specified channels/groups, processes the data, and provides analysis on common topics, keywords, and hashtags.

#  Installation

Install the required dependencies using pip:</br>
`pip install pyqt5 pyrogram nltk requests` </br>
Create install.py file with this code: </br>
`import nltk 
nltk.download('stopwords') 
nltk.download('punkt')` </br>
Launch this code. </br>

Configure API tokens:

Create a configuration.py file in the project directory. </br>
Define your Telegram API ID, API hash, VK access token, and any other required credentials in this file. </br>

Run the program: </br>

`python3 main.py`

# Usage:

Launch the program. </br>
Enter the names of Telegram channels and VK group IDs you want to analyze. </br>
Click the "Start" button to initiate the analysis. </br>
View the analysis results displayed in the user interface. </br>

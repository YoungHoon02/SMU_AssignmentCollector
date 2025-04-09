# Configuration settings for the e-campus crawler

ECAMPUS_URL = "https://ecampus.smu.ac.kr"
LOGIN_URL = f"{ECAMPUS_URL}/login.php"
COURSES_URL = f"{ECAMPUS_URL}/courses"
ASSIGNMENT_URL_PATTERN = f"{ECAMPUS_URL}/mod/assign/~"

# WebDriver settings
WEBDRIVER_PATH = "/path/to/chromedriver"  # Update this path to your WebDriver executable
HEADLESS = True  # Set to True to run in headless mode, False to see the browser window

# Timeout settings
TIMEOUT = 10  # seconds for waiting for elements to load
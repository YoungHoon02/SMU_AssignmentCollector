class Login:
    def __init__(self, driver, username, password):
        self.driver = driver
        self.username = username
        self.password = password

    def perform_login(self):
        self.driver.get("https://ecampus.smu.ac.kr/login.php")
        username_field = self.driver.find_element("name", "username")
        password_field = self.driver.find_element("name", "password")
        login_button = self.driver.find_element("name", "login")

        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        login_button.click()